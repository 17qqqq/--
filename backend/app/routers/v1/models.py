# 模型选择接口
#
# 路由只做三件事：接收参数 → 调用 service → 包装统一响应。
# 真正的校验和业务规则在 app/services/model_service.py。
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import PageParams, PageResult, ResponseModel
from app.schemas.model import MLModelCreate, MLModelDetail
from app.services.model_service import ModelService

router = APIRouter()


@router.get("", response_model=ResponseModel[PageResult[MLModelDetail]])
def list_models(
    project_id: int,
    params: PageParams = Depends(),
    db: Session = Depends(get_db),
):
    """查询某个项目下的模型列表。"""
    total, items = ModelService(db).list_by_project(project_id, params)
    return ResponseModel(
        data=PageResult[MLModelDetail](
            total=total,
            items=[MLModelDetail.model_validate(item) for item in items],
        )
    )


@router.get("/active", response_model=ResponseModel[MLModelDetail])
def get_active_model(
    project_id: int,
    db: Session = Depends(get_db),
):
    """查询某个项目当前启用的模型。"""
    obj = ModelService(db).get_active(project_id)
    return ResponseModel(data=MLModelDetail.model_validate(obj) if obj else None)


@router.post("", response_model=ResponseModel[MLModelDetail])
def create_model(
    payload: MLModelCreate,
    db: Session = Depends(get_db),
):
    """登记一个待测试的模型。"""
    obj = ModelService(db).create(payload)
    return ResponseModel(data=MLModelDetail.model_validate(obj))


@router.put("/{model_id}/activate", response_model=ResponseModel[MLModelDetail])
def activate_model(
    model_id: int,
    project_id: int,
    db: Session = Depends(get_db),
):
    """把指定模型设为当前项目启用模型。"""
    obj = ModelService(db).activate(project_id, model_id)
    return ResponseModel(data=MLModelDetail.model_validate(obj))
