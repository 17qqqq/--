# 测试报告的业务逻辑
#
# ── 本模块做什么 ────────────────────────────────────────────────────────
# 存储和查询报告（reports / report_snapshots 两张表）。
# 报告数据由指标模块算好后通过 POST /reports 提交，或由执行模块调用
# ReportService.create() 直接写入。
#
# ── 本模块不做什么 ──────────────────────────────────────────────────────
# 不加载模型、不施加扰动、不计算 Dice/IoU——这些都在 app/interfaces 里
# 定义了接口，由其他成员实现并通过注册表接入。
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.constants import REPORT_STATUS_FINISHED
from app.core.exceptions import BadRequestError, NotFoundError, NotImplementedYetError
from app.models.project import Project
from app.models.report import Report, ReportSnapshot
from app.models.test_plan import TestPlan
from app.repositories.report_repo import ReportRepository
from app.schemas.common import PageParams
from app.schemas.report import ReportCreate, ReportGenerateRequest


class ReportService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ReportRepository(db)

    def _ensure_project(self, project_id: int) -> None:
        if not self.db.get(Project, project_id):
            raise NotFoundError("项目不存在")

    def _ensure_plan(self, project_id: int, plan_id: int | None) -> None:
        """计划可以为空；不为空时必须存在且属于当前项目。"""
        if plan_id is None:
            return
        plan = self.db.get(TestPlan, plan_id)
        if not plan or plan.project_id != project_id:
            raise BadRequestError("测试计划不存在或不属于该项目")

    def create(self, payload: ReportCreate):
        """保存一份已计算好的报告。

        调用方（指标/执行模块）负责提供 metrics 汇总和 snapshots 明细；
        这里只做归属校验和落库，并标记为已生成。
        """
        self._ensure_project(payload.project_id)
        self._ensure_plan(payload.project_id, payload.test_plan_id)

        report = self.repo.create(
            project_id=payload.project_id,
            test_plan_id=payload.test_plan_id,
            test_run_id=payload.test_run_id,
            title=payload.title,
            summary=payload.summary,
            status=REPORT_STATUS_FINISHED,
            metrics=payload.metrics,
            generated_at=datetime.now(),
        )
        # 逐条明细一起插入；ORM 会自动处理 report_id
        report.snapshots = [
            ReportSnapshot(**item.model_dump()) for item in payload.snapshots
        ]

        self.db.commit()
        self.db.refresh(report)
        return report

    def list(self, project_id: int, params: PageParams):
        self._ensure_project(project_id)
        offset = (params.page - 1) * params.size
        return self.repo.list_by_project(project_id, offset=offset, limit=params.size)

    def get(self, project_id: int, report_id: int):
        self._ensure_project(project_id)
        obj = self.repo.get_by_project(project_id, report_id)
        if not obj:
            raise NotFoundError("测试报告不存在")
        return obj

    def delete(self, project_id: int, report_id: int) -> None:
        obj = self.get(project_id, report_id)
        self.repo.delete(obj)  # snapshots 由 relationship 的 delete-orphan 级联删除
        self.db.commit()

    def generate(self, payload: ReportGenerateRequest):
        """自动生成报告（接口已定义，执行链路未接入）。

        完整流程需要：
          1. 执行模块按计划读取用例图像
          2. 扰动模块按快照施加扰动（app/interfaces/perturbation.py）
          3. 推理模块输出掩码（app/interfaces/inference.py）
          4. 指标模块计算数值（app/interfaces/metrics.py）
        以上实现注册齐之后，把这里的占位替换成调用执行引擎即可。
        """
        self._ensure_project(payload.project_id)
        self._ensure_plan(payload.project_id, payload.test_plan_id)
        raise NotImplementedYetError(
            "报告自动生成依赖推理、扰动、指标实现，当前尚未接入；"
            "可先用 POST /reports 提交已计算好的指标数据。"
        )
