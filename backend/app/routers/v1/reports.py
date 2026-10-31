# 测试报告接口
#
# 报告数据由指标/执行模块计算后提交；本路由负责存储与查询。
# 自动生成接口 /generate 已定义，但依赖的算法实现尚未接入，当前返回 501。
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import PageParams, PageResult, ResponseModel
from app.schemas.report import ReportCreate, ReportDetail, ReportGenerateRequest
from app.services.report_service import ReportService

router = APIRouter()


@router.get("", response_model=ResponseModel[PageResult[ReportDetail]])
def list_reports(
    project_id: int,
    params: PageParams = Depends(),
    db: Session = Depends(get_db),
):
    """分页查询某个项目下的报告（按创建时间倒序）。"""
    total, items = ReportService(db).list(project_id, params)
    return ResponseModel(
        data=PageResult[ReportDetail](
            total=total,
            items=[ReportDetail.model_validate(item) for item in items],
        )
    )


@router.post("", response_model=ResponseModel[ReportDetail])
def create_report(payload: ReportCreate, db: Session = Depends(get_db)):
    """提交一份已计算好的报告（汇总指标 + 指标明细）。"""
    obj = ReportService(db).create(payload)
    return ResponseModel(data=ReportDetail.model_validate(obj))


@router.post("/generate", response_model=ResponseModel[ReportDetail])
def generate_report(payload: ReportGenerateRequest, db: Session = Depends(get_db)):
    """自动生成报告。

    执行/指标模块接入后，这里会走完整的"读图 → 扰动 → 推理 → 计算"链路。
    当前会返回 501（code 50100），前端可提示"功能尚未接入"。
    """
    obj = ReportService(db).generate(payload)
    return ResponseModel(data=ReportDetail.model_validate(obj))


@router.get("/{report_id}", response_model=ResponseModel[ReportDetail])
def get_report(
    report_id: int,
    project_id: int,
    db: Session = Depends(get_db),
):
    """查询报告详情，包含全部指标明细。"""
    obj = ReportService(db).get(project_id, report_id)
    return ResponseModel(data=ReportDetail.model_validate(obj))


@router.delete("/{report_id}", response_model=ResponseModel[None])
def delete_report(
    report_id: int,
    project_id: int,
    db: Session = Depends(get_db),
):
    """删除报告；指标明细随报告一起删除。"""
    ReportService(db).delete(project_id, report_id)
    return ResponseModel(data=None)
