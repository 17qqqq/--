# 扰动参数配置接口（路由层）
#
# ── 路由层的三条纪律 ────────────────────────────────────────────────────
# 1. 只做三件事：解析参数 → 调 service → 包统一响应
# 2. 不写 SQL、不写业务判断、不 try/except（异常交给全局处理器）
# 3. 每个函数的 docstring 会出现在 /docs（Swagger）里，所以写清楚用途
#
# ── 路径是怎么拼出来的 ──────────────────────────────────────────────────
# app/routers/v1/__init__.py 里注册时加了前缀：
#     api_router.include_router(perturbations.router, prefix="/perturbations")
# main.py 里又加了 API 前缀 /api/v1
# 所以下面的 "/{project_id}" 最终是：
#     GET /api/v1/perturbations/1
#
# ── 返回值 ──────────────────────────────────────────────────────────────
# 所有接口统一返回 ResponseModel[T]：{"code": 0, "message": "ok", "data": ...}
# 前端 api/request.js 会自动把 data 解包出来，页面拿到的就是配置对象本身。
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import ResponseModel
from app.schemas.perturbation import PerturbationConfigDetail, PerturbationConfigUpdate
from app.services.perturbation_service import PerturbationService

router = APIRouter()


@router.get("/{project_id}", response_model=ResponseModel[PerturbationConfigDetail])
def get_config(project_id: int, db: Session = Depends(get_db)):
    """获取某个项目的扰动配置；没有配置时用默认值自动创建。

    - project_id 是路径参数，不合法（非整数）时 FastAPI 直接返回 422
    - response_model 负责把 ORM 对象转成 dict，并过滤掉 schema 里没定义的字段
    - Depends(get_db)：每个请求一个 Session，请求结束自动关闭
    """
    obj = PerturbationService(db).get_or_create(project_id)
    return ResponseModel(data=PerturbationConfigDetail.model_validate(obj))


@router.put("/{project_id}", response_model=ResponseModel[PerturbationConfigDetail])
def update_config(
    project_id: int,
    payload: PerturbationConfigUpdate,
    db: Session = Depends(get_db),
):
    """保存多选开关；未提交的字段保持原值。

    前端配置页点「保存配置」时调用，请求体形如：
        {"enable_brightness": true, "enable_contrast": false, "enable_noise": true}
    返回保存后的完整配置，前端用它覆盖本地 store，保证两边一致
    （包括 updated_at 这类服务端生成的值）。
    """
    obj = PerturbationService(db).update(project_id, payload)
    return ResponseModel(data=PerturbationConfigDetail.model_validate(obj))
