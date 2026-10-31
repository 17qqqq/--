# 测试计划的数据访问层
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.test_plan import TestPlan
from app.repositories.base import BaseRepository


class TestPlanRepository(BaseRepository[TestPlan]):
    def __init__(self, db: Session):
        super().__init__(TestPlan, db)

    def list_by_project(
        self, project_id: int, offset: int = 0, limit: int = 20
    ) -> tuple[int, list[TestPlan]]:
        return self.paginate(
            offset,
            limit,
            condition=TestPlan.project_id == project_id,
            order_by=TestPlan.id.desc(),  # 新建的计划排前面
        )

    def get_by_project(self, project_id: int, plan_id: int) -> TestPlan | None:
        return self.db.scalar(
            select(TestPlan).where(
                TestPlan.id == plan_id,
                TestPlan.project_id == project_id,
            )
        )
