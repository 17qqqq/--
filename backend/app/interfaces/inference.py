# 推理后端接口（留给"模型功能"负责人实现）
#
# ── 边界 ────────────────────────────────────────────────────────────────
# 后端只负责：登记模型（MLModel 表，已有）、保存模型文件路径、选择启用模型。
# 真正"加载 .pt/.onnx 并输出血管掩码"由模型模块实现，实现后注册即可。
#
# ── 约定 ────────────────────────────────────────────────────────────────
# 1. 输入图像统一是 numpy.ndarray，形状 HxWx3，dtype uint8，RGB 顺序。
#    这里不 import numpy，避免未安装 numpy 时整个后端起不来。
# 2. 输出统一是二值掩码 numpy.ndarray，形状 HxW，取值 0/1 或 0/255。
# 3. 一个实现类对应一种框架（pytorch / onnx / …），名字与 MLModel.framework 一致。
# 4. 同一实例可能被多次 load()，实现里要自行处理旧模型释放（close）。
#
# ── 实现示例（模型模块的同学）──────────────────────────────────────────
#     @inference_backends.register("pytorch")
#     class PyTorchBackend(BaseInferenceBackend):
#         def load(self, model_path, options=None):
#             self.model = torch.load(model_path, map_location="cpu")
#             self.model.eval()
#         def predict(self, image):
#             ...  # 返回 HxW 的 0/1 掩码
#         def close(self):
#             self.model = None
#
# 注册后，执行引擎用 inference_backends.require("pytorch") 取实现即可。
from abc import ABC, abstractmethod
from typing import Any

from app.interfaces.registry import InterfaceRegistry


class BaseInferenceBackend(ABC):
    """分割模型推理后端。"""

    # 对应 MLModel.framework，例如 "pytorch" / "onnx"
    framework: str = ""

    @abstractmethod
    def load(self, model_path: str, options: dict[str, Any] | None = None) -> None:
        """加载模型。model_path 是 MLModel.file_path 存的路径。

        options 预留给设备选择（cpu/cuda）、输入尺寸等实现相关参数。
        """

    @abstractmethod
    def predict(self, image: Any) -> Any:
        """对单张 RGB 图像推理，返回 HxW 的二值掩码。

        image: numpy.ndarray, shape=(H, W, 3), dtype=uint8
        return: numpy.ndarray, shape=(H, W), 0/1 或 0/255
        """

    def close(self) -> None:
        """释放模型资源；默认什么都不做，按需覆盖。"""


# 全局注册表：执行引擎 / 报告生成通过它取实现
inference_backends: InterfaceRegistry[BaseInferenceBackend] = InterfaceRegistry(
    "推理后端"
)
