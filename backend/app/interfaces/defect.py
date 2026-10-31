# 缺陷检测接口（留给"测试与缺陷检测"负责人实现）
#
# ── 边界 ────────────────────────────────────────────────────────────────
# 这部分没有独立数据表：检测结果由执行模块自己决定怎么落库
# （可以加 defects 表，也可以写进执行结果）。这里只约定"怎么被调用"。
#
# ── 返回结构约定 ────────────────────────────────────────────────────────
# detect() 返回一个列表，每一项是一个缺陷：
#     {
#         "type": "vessel_break",       # 缺陷类型，字符串
#         "bbox": [x1, y1, x2, y2],     # 可选，像素坐标
#         "score": 0.87,                # 可选，置信度 0-1
#         "message": "血管断裂",         # 可选，给报告用的说明
#     }
# 报告模块只依赖这些键，新的缺陷类型不需要改报告代码。
from abc import ABC, abstractmethod
from typing import Any

from app.interfaces.registry import InterfaceRegistry


class BaseDefectDetector(ABC):
    """根据预测掩码/原图判断分割缺陷。"""

    key: str = ""

    @abstractmethod
    def detect(
        self,
        image: Any,
        prediction: Any,
        ground_truth: Any | None = None,
    ) -> list[dict[str, Any]]:
        """返回缺陷列表；没有发现缺陷时返回空列表。

        image:        numpy.ndarray (H, W, 3) uint8
        prediction:   numpy.ndarray (H, W) 二值掩码
        ground_truth: numpy.ndarray (H, W) 或 None（无金标准时只能做无参考检测）
        """


defect_detectors: InterfaceRegistry[BaseDefectDetector] = InterfaceRegistry(
    "缺陷检测器"
)
