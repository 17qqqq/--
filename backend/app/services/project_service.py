from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.ml_model import MLModel
from app.models.perturbation import PerturbationConfig
from app.models.report import Report, ReportSnapshot
from app.models.test_case import TestCase
from app.models.test_plan import TestPlan
from app.models.user import User
from app.repositories.project_repo import ProjectRepository
from app.schemas.common import PageParams
from app.schemas.project import ProjectCreate


class ProjectService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ProjectRepository(db)

    def create(self, payload: ProjectCreate):
        if not self.db.get(User, payload.owner_id):
            raise BadRequestError("owner_id 对应的用户不存在")
        obj = self.repo.create(**payload.model_dump())
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def list(self, params: PageParams):
        offset = (params.page - 1) * params.size
        return self.repo.list(offset=offset, limit=params.size)

    def get(self, project_id: int):
        obj = self.repo.get(project_id)
        if not obj:
            raise NotFoundError("项目不存在")
        return obj

    def delete(self, project_id: int) -> None:
        """删除项目及它名下的全部数据。
        数据库里只有 report_snapshots 和 test_plan_cases 声明了级联，
        其余外键都是普通约束，所以这里按依赖顺序显式清理：
        报告明细 → 报告 → 计划 → 用例 → 扰动配置 → 模型 → 项目。。
        """
        project = self.get(project_id)


        report_ids = select(Report.id).where(Report.project_id == project_id)
        self.db.execute(
            delete(ReportSnapshot).where(ReportSnapshot.report_id.in_(report_ids))
        )
        self.db.execute(delete(Report).where(Report.project_id == project_id))


        # 报告引用了 test_plans，必须先删报告再删计划
        self.db.execute(delete(TestPlan).where(TestPlan.project_id == project_id))
        self.db.execute(delete(TestCase).where(TestCase.project_id == project_id))
        self.db.execute(
            delete(PerturbationConfig).where(
                PerturbationConfig.project_id == project_id
            )
        )
        self.db.execute(delete(MLModel).where(MLModel.project_id == project_id))

        self.db.delete(project)
        self.db.commit()