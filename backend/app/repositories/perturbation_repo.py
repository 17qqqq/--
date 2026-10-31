# 扰动参数配置的数据访问层（Repository）
#
# 这一层只回答"怎么查、怎么改"，不判断"项目存不存在""该不该给默认值"，
# 那些属于业务规则，放在 services/perturbation_service.py。
#
# 为什么还要包一层：BaseRepository 已经提供了 get / list / create / update /
# delete，本类只需要补"按项目查"这种领域查询。等以后换成 MySQL 或加缓存，
# 改动也只落在这一层。
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.perturbation import PerturbationConfig
from app.repositories.base import BaseRepository


class PerturbationRepository(BaseRepository[PerturbationConfig]):
    """PerturbationConfig 的查询封装。

    self.model 由 BaseRepository.__init__ 赋值，BaseRepository 里的
    create()/update()/get() 都基于它工作，所以这里只写额外查询即可。
    """

    def __init__(self, db: Session):
        super().__init__(PerturbationConfig, db)

    def get_by_project(self, project_id: int) -> PerturbationConfig | None:
        """按项目查询配置；一个项目最多一条（project_id 有唯一约束）。

        返回 None 表示"还没创建过"，由 service 决定是建默认值还是报错。
        用 scalar() 而不是 scalars().first()：唯一约束保证最多一行，
        scalar() 语义更明确，多行时会直接报错而不是静默取第一条。
        """
        return self.db.scalar(
            select(PerturbationConfig).where(
                PerturbationConfig.project_id == project_id
            )
        )

    # ── 可复用要点 ──────────────────────────────────────────────────────
    # 新模块的 repository 基本都是这个结构：
    #   1. 继承 BaseRepository[你的模型]
    #   2. __init__ 里 super().__init__(模型类, db)
    #   3. 只补 BaseRepository 没有的领域查询（按项目、按状态、模糊搜索…）
