# 汇总导出所有 model，保证 Base.metadata 完整
#
# 新增模型后必须在这里 import，Base.metadata.create_all 才会建表。
from app.models.ml_model import MLModel
from app.models.perturbation import PerturbationConfig
from app.models.project import Project
from app.models.report import Report, ReportSnapshot
from app.models.test_case import TestCase
from app.models.test_plan import TestPlan, test_plan_cases
from app.models.user import User

__all__ = [
    "User",
    "Project",
    "MLModel",
    "PerturbationConfig",
    "TestCase",
    "TestPlan",
    "test_plan_cases",
    "Report",
    "ReportSnapshot",
]
