# 扩展接口层（Ports）
#
# 这个包是"本后端"与"其他成员负责的算法模块"之间的唯一契约层。
#
# 四个扩展点：
#   inference.py     推理后端       BaseInferenceBackend / inference_backends
#   perturbation.py  扰动算子       BasePerturbation     / perturbations
#   metrics.py       指标计算       BaseMetric           / metrics
#   defect.py        缺陷检测       BaseDefectDetector   / defect_detectors
#
# 团队约定：
# 1. 算法实现放在各自模块里，import 这里的基类，再用注册表装饰器登记；
# 2. 本后端不 import 任何具体算法类，只通过注册表按名字取实现；
# 3. 未注册时调用方会抛 KeyError，接口层统一转成 501，提示"实现尚未接入"。
#
# 查看当前已接入哪些实现：GET /api/v1/capabilities
from app.interfaces.defect import BaseDefectDetector, defect_detectors
from app.interfaces.inference import BaseInferenceBackend, inference_backends
from app.interfaces.metrics import BaseMetric, metrics
from app.interfaces.perturbation import BasePerturbation, perturbations

__all__ = [
    "BaseInferenceBackend",
    "inference_backends",
    "BasePerturbation",
    "perturbations",
    "BaseMetric",
    "metrics",
    "BaseDefectDetector",
    "defect_detectors",
]
