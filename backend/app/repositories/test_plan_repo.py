# 测试计划的数据访问层
#
# 这里只拼接 SQLAlchemy 查询和分页，不做项目是否存在等业务校验；
# 校验逻辑在 TestPlanService。查询都带 project_id，防止通过其他项目的
# 计划 id 读到不属于当前项目的数据。
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.test_plan import TestPlan
from app.repositories.base import BaseRepository


class TestPlanRepository(BaseRepository[TestPlan]):
    """测试计划的 CRUD；通用增删改查和分页由 BaseRepository 提供。"""

    def __init__(self, db: Session):
        # 把模型类型固定下来，基类的 get/create 等方法就不用每次传 TestPlan
        super().__init__(TestPlan, db)

    def list_by_project(
        self, project_id: int, offset: int = 0, limit: int = 20
    ) -> tuple[int, list[TestPlan]]:
        """分页查询某个项目的计划，新建的排在前面。

        返回 (total, items)：total 用于前端分页器，items 是当前页数据。
        offset/limit 由 service 根据 page/size 换算，仓储层只负责查询。
        """
        return self.paginate(
            offset,
            limit,
            condition=TestPlan.project_id == project_id,
            order_by=TestPlan.id.desc(),  # 新建的计划排前面
        )

    def get_by_project(self, project_id: int, plan_id: int) -> TestPlan | None:
        """按「项目 + 计划 id」查单条。

        同时匹配 project_id 和 id，避免拿其他项目的计划 id 越权读取；
        查不到返回 None，由 service 决定是否抛 404。
        """
        return self.db.scalar(
            select(TestPlan).where(
                TestPlan.id == plan_id,
                TestPlan.project_id == project_id,
            )
        )
