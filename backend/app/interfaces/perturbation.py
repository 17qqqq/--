# 扰动算子接口（留给"扰动参数配置"负责人实现算法）
#
# ── 边界 ────────────────────────────────────────────────────────────────
# 后端已经完成：扰动开关的存储（perturbation_configs 表）、GET/PUT 接口、
# 前端页面与工作台的联动。这里只留"把扰动作用到图像上"的算法接口。
#
# ── 命名约定 ────────────────────────────────────────────────────────────
# 注册名必须与数据库字段对应，执行引擎据此决定对每张图施加哪些扰动：
#     enable_brightness  -> 亮度扰动
#     enable_contrast    -> 对比度扰动
#     enable_noise       -> 高斯噪声
# 新增扰动类型时：模型加列 + 前端 PERTURBATION_OPTIONS 加项 + 这里注册同名实现。
#
# ── 实现示例 ───────────────────────────────────────────────────────────
#     @perturbations.register("enable_brightness")
#     class BrightnessPerturbation(BasePerturbation):
#         key = "enable_brightness"
#         label = "亮度扰动"
#         def apply(self, image, *, strength=100, params=None):
#             factor = 1 + (strength / 100) * 0.5
#             return np.clip(image * factor, 0, 255).astype(np.uint8)
from abc import ABC, abstractmethod
from typing import Any

from app.interfaces.registry import InterfaceRegistry


class BasePerturbation(ABC):
    """一种图像扰动。实现应保持无状态（不要在图与图之间累积数据）。"""

    # 与 PerturbationConfig 的开关字段名一致，如 "enable_noise"
    key: str = ""
    # 页面展示名，如 "高斯噪声"
    label: str = ""

    @abstractmethod
    def apply(
        self,
        image: Any,
        *,
        strength: int = 100,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """对图像施加扰动。

        image:    numpy.ndarray, shape=(H, W, 3), dtype=uint8, RGB
        strength: 0-100，来自 PerturbationConfig.strength
        params:   来自 PerturbationConfig.params（可能为 None）
        return:   新图像，形状和 dtype 与输入一致；不要原地修改输入
        """

    def describe(self) -> dict[str, str]:
        """给 /capabilities 之类的接口展示用。"""
        return {"key": self.key, "label": self.label}


perturbations: InterfaceRegistry[BasePerturbation] = InterfaceRegistry("扰动算子")
