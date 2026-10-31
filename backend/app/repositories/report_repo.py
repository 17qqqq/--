# 测试报告的数据访问层
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.report import Report
from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    def __init__(self, db: Session):
        super().__init__(Report, db)

    def list_by_project(
        self, project_id: int, offset: int = 0, limit: int = 20
    ) -> tuple[int, list[Report]]:
        return self.paginate(
            offset,
            limit,
            condition=Report.project_id == project_id,
            order_by=Report.id.desc(),
        )

    def get_by_project(self, project_id: int, report_id: int) -> Report | None:
        return self.db.scalar(
            select(Report).where(
                Report.id == report_id,
                Report.project_id == project_id,
            )
        )
