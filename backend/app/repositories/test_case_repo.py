# 测试用例的数据访问层
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.test_case import TestCase
from app.repositories.base import BaseRepository


class TestCaseRepository(BaseRepository[TestCase]):
    def __init__(self, db: Session):
        super().__init__(TestCase, db)

    def list_by_project(
        self,
        project_id: int,
        offset: int = 0,
        limit: int = 20,
        enabled: bool | None = None,
    ) -> tuple[int, list[TestCase]]:
        # enabled 为 None 表示不过滤；True/False 只返回对应状态的用例。
        # 计划页选用例时传 True，避免把已停用的样本带进新计划。
        condition = TestCase.project_id == project_id
        if enabled is not None:
            condition = condition & TestCase.enabled.is_(enabled)
        return self.paginate(offset, limit, condition=condition)

    def get_by_project(self, project_id: int, case_id: int) -> TestCase | None:
        return self.db.scalar(
            select(TestCase).where(
                TestCase.id == case_id,
                TestCase.project_id == project_id,
            )
        )

    def list_by_ids(self, project_id: int, case_ids: list[int]) -> list[TestCase]:
        """按 id 批量取用例；只返回属于该项目的，调用方据此判断有没有非法 id。"""
        if not case_ids:
            return []
        return list(
            self.db.scalars(
                select(TestCase).where(
                    TestCase.project_id == project_id,
                    TestCase.id.in_(case_ids),
                )
            ).all()
        )
