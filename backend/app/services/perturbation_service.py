# 扰动参数配置的业务逻辑层（Service）
#
# ── 这一层负责什么 ──────────────────────────────────────────────────────
# 1. 校验：project_id 对应的项目必须存在（不存在 → 404，而不是数据库外键报 500）
# 2. 默认值：项目第一次访问时自动建一条配置，前端不用先调"创建"接口
# 3. 局部更新：PUT 只覆盖请求体里出现过的字段
# 4. 事务：查询/写入的 commit、refresh 都在这里，路由层不碰 session
#
# ── 事务处理说明 ────────────────────────────────────────────────────────
# BaseRepository.create() 内部只 flush（把 SQL 发给数据库但不提交），
# 这样可以拿到自增 id，同时把"什么时候提交"的决定权留给 service。
# 这里每次操作结束都 commit + refresh：
#   commit  -> 真正落盘
#   refresh -> 重新从库里读回 created_at / updated_at 等服务端生成的字段，
#              否则响应里可能出现 None 或旧值
#
# ── 异常约定 ────────────────────────────────────────────────────────────
# 抛 AppException 的子类（这里用 NotFoundError），由 core/exceptions.py 里的
# 全局处理器统一转成 {"code": 40400, "message": "...", "data": null}，
# 路由和前端都不需要写 try/except。
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.project import Project
from app.repositories.perturbation_repo import PerturbationRepository
from app.schemas.perturbation import PerturbationConfigUpdate


class PerturbationService:
    def __init__(self, db: Session):
        # session 由路由的 Depends(get_db) 注入；请求结束自动 close
        self.db = db
        self.repo = PerturbationRepository(db)

    def _ensure_project(self, project_id: int) -> None:
        """确认项目存在。

        直接查主键是成本最低的方式（SQLite 主键索引）。
        把校验单独抽出来，是因为 get_or_create 和后续可能的 update 都要用。
        """
        if not self.db.get(Project, project_id):
            raise NotFoundError("项目不存在")

    def get_or_create(self, project_id: int):
        """查询项目配置；不存在时按默认值创建一条。

        为什么让 GET 也写库：
        - 前端打开配置页不需要先判断"有没有配置"，少一次请求、少一种分支
        - 默认值（三个开关 False、params NULL、strength 100）只在模型里定义一次，
          前端不需要自己造一份"默认配置"
        注意：这是"读时创建"（read-through）模式，适合配置类数据；
        如果以后要统计"创建时间"，第一次 GET 的时间就是创建时间。
        """
        self._ensure_project(project_id)

        obj = self.repo.get_by_project(project_id)
        if obj is None:
            # 只传 project_id，其余字段走模型层的 default：
            # enable_* = False、params = None、strength = 100
            obj = self.repo.create(project_id=project_id)
            self.db.commit()
            self.db.refresh(obj)
        return obj

    def update(self, project_id: int, payload: PerturbationConfigUpdate):
        """保存配置；只更新请求体里出现过的字段。

        exclude_unset=True 的作用：
        - 前端目前只提交三个 enable_* 字段
        - 这样 params / strength 不会因为"没传"而被重置成 None / 100
        - 以后前端加了强度滑块，只要多传一个字段就能生效，不用改后端
        """
        obj = self.get_or_create(project_id)

        # model_dump(exclude_unset=True) 只保留"客户端显式传了"的键，
        # 与普通 model_dump()（会把默认值也带出来）不同。
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)

        self.db.commit()
        self.db.refresh(obj)
        return obj

    # ── 其他模块可以直接抄的写法 ────────────────────────────────────────
    # 1. 「_ensure_xxx + get_or_create」：适合"每个项目/用户只有一份"的配置类
    #    数据，比如外观设置、通知设置、默认参数。
    # 2. 「exclude_unset 局部更新」：适合前端只改一部分字段的 PUT/PATCH。
    # 3. 「service 里 commit、router 里不 commit」：保证一个业务操作一个事务。
