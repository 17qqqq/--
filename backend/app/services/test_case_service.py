# 测试用例的业务逻辑
#
# 只做增删改查和归属校验；用例里的图像怎么读、怎么预处理由执行模块决定。
#
# 注意：本类里有个方法叫 list，会在类体内遮蔽内置的 list。
# 因此开启延迟注解（PEP 563），让 list[int] 只在运行时求值，避免类定义阶段报错。
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.project import Project
from app.repositories.test_case_repo import TestCaseRepository
from app.schemas.common import PageParams
from app.schemas.test_case import TestCaseCreate, TestCaseUpdate


class TestCaseService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TestCaseRepository(db)

    def _ensure_project(self, project_id: int) -> None:
        if not self.db.get(Project, project_id):
            raise NotFoundError("项目不存在")

    def create(self, payload: TestCaseCreate):
        self._ensure_project(payload.project_id)
        obj = self.repo.create(**payload.model_dump())
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def list(
        self,
        project_id: int,
        params: PageParams,
        enabled: bool | None = None,
    ):
        self._ensure_project(project_id)
        offset = (params.page - 1) * params.size
        return self.repo.list_by_project(
            project_id,
            offset=offset,
            limit=params.size,
            enabled=enabled,
        )

    def get(self, project_id: int, case_id: int):
        self._ensure_project(project_id)
        obj = self.repo.get_by_project(project_id, case_id)
        if not obj:
            raise NotFoundError("测试用例不存在")
        return obj

    def update(self, project_id: int, case_id: int, payload: TestCaseUpdate):
        obj = self.get(project_id, case_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, project_id: int, case_id: int) -> None:
        obj = self.get(project_id, case_id)
        self.repo.delete(obj)
        self.db.commit()

    # ── 给测试计划模块复用 ──────────────────────────────────────────────
    # 计划创建/更新时用它校验"勾选的用例都属于这个项目"
    def list_by_ids(self, project_id: int, case_ids: list[int]):
        return self.repo.list_by_ids(project_id, case_ids)
