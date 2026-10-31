# 测试报告的请求 / 响应结构
#
# 报告数据由"指标/执行"模块计算好后提交；本模块负责校验和存储。
# 计算逻辑的接入点在 app/interfaces/metrics.py。
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReportSnapshotCreate(BaseModel):
    """一条指标明细。"""

    perturbation_type: str = Field(..., min_length=1, max_length=50)
    metric_name: str = Field(..., min_length=1, max_length=50)
    metric_value: float
    # 无扰动时的基准值，可为空
    baseline_value: float | None = None
    case_id: int | None = None


class ReportCreate(BaseModel):
    project_id: int = Field(..., ge=1)
    test_plan_id: int | None = Field(None, ge=1)
    # 执行记录由执行模块维护，这里只存 id
    test_run_id: int | None = Field(None, ge=1)

    title: str = Field(..., min_length=1, max_length=200)
    summary: str = Field("", max_length=1000)
    # 汇总指标，结构由指标模块决定
    metrics: dict | None = None
    snapshots: list[ReportSnapshotCreate] = Field(default_factory=list)


class ReportGenerateRequest(BaseModel):
    """POST /reports/generate 的请求体。

    实现接入后，由指标/执行模块按这个请求生成报告；
    目前接口返回 501，表示"接口已定义，计算实现未接入"。
    """

    project_id: int = Field(..., ge=1)
    test_plan_id: int | None = Field(None, ge=1)
    test_run_id: int | None = Field(None, ge=1)
    title: str = Field("", max_length=200)


class ReportSnapshotDetail(ReportSnapshotCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ReportDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    test_plan_id: int | None
    test_run_id: int | None
    title: str
    summary: str
    status: str
    metrics: dict | None
    generated_at: datetime | None
    snapshots: list[ReportSnapshotDetail] = []
    created_at: datetime
    updated_at: datetime
