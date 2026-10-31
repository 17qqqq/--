# 系统级接口：连通性检测 + 扩展能力清单
from fastapi import APIRouter

from app.interfaces import (
    defect_detectors,
    inference_backends,
    metrics,
    perturbations,
)
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/ping", response_model=ResponseModel[dict])
def ping():
    return ResponseModel(data={"msg": "pong from backend"})


@router.get("/capabilities", response_model=ResponseModel[dict])
def capabilities():
    """列出当前已注册的扩展实现。

    四个列表对应 app/interfaces 下的四个接口；为空表示对应模块
    还没有把实现接进来。前端或联调时可以拿它判断"哪部分还没就绪"。
    """
    return ResponseModel(
        data={
            "inference": inference_backends.names(),
            "perturbations": perturbations.names(),
            "metrics": metrics.names(),
            "defect_detectors": defect_detectors.names(),
        }
    )
