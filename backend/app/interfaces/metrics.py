# 鲁棒性指标接口（留给"鲁棒性指标统计"负责人实现计算）
#
# ── 边界 ────────────────────────────────────────────────────────────────
# 后端已经完成：报告与指标快照的存储表（reports / report_snapshots）、
# 报告 CRUD 接口。这里只留"给一对掩码算出一个数"的计算接口。
#
# ── 命名约定 ────────────────────────────────────────────────────────────
# 注册名就是报告里存的 metric_name，建议用学术常用写法：
#     dice / iou / sensitivity / specificity / accuracy / hd95
#
# ── 实现示例 ───────────────────────────────────────────────────────────
#     @metrics.register("dice")
#     class DiceMetric(BaseMetric):
#         key = "dice"
#         higher_is_better = True
#         def compute(self, prediction, ground_truth):
#             p = prediction.astype(bool).ravel()
#             g = ground_truth.astype(bool).ravel()
#             return 2 * (p & g).sum() / (p.sum() + g.sum() + 1e-8)
from abc import ABC, abstractmethod
from typing import Any

from app.interfaces.registry import InterfaceRegistry


class BaseMetric(ABC):
    """一种分割评价指标。"""

    # 报告快照里的 metric_name，如 "dice"
    key: str = ""
    # True 表示越大越好（Dice/IoU），False 表示越小越好（HD95）
    higher_is_better: bool = True

    @abstractmethod
    def compute(self, prediction: Any, ground_truth: Any) -> float:
        """计算一个样本的指标值。

        prediction / ground_truth: numpy.ndarray, shape=(H, W)，二值掩码
        return: float；无法计算时应返回 0 或抛出异常，由调用方决定怎么处理
        """


metrics: InterfaceRegistry[BaseMetric] = InterfaceRegistry("指标")
