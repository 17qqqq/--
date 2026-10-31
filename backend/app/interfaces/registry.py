# 通用接口注册表
#
# 四个扩展点（推理后端、扰动算子、指标计算、缺陷检测）都用同一套注册机制：
# 团队其他成员在自己的文件里实现接口类，然后用装饰器注册一个名字；
# 业务代码只通过名字取实现，不 import 具体类，避免互相依赖。
#
# 用法：
#     @inference_backends.register("pytorch")
#     class PyTorchBackend(BaseInferenceBackend):
#         ...
#
# 注册表存的是"实例"：注册时自动调用无参构造。实现类如果需要配置，
# 请把配置放在 load() / apply() 的参数里，或提供无参构造 + 属性注入。
from typing import Generic, TypeVar

T = TypeVar("T")


class InterfaceRegistry(Generic[T]):
    """按名字保存接口实现的容器。"""

    def __init__(self, kind: str):
        # kind 只用于错误提示，例如 "推理后端"、"指标"
        self.kind = kind
        self._items: dict[str, T] = {}

    def register(self, name: str, *, replace: bool = False):
        """装饰器：把实现类注册到 name 下。

        重复注册默认报错，避免两个人写了同名实现互相覆盖；
        测试或热替换时可以传 replace=True。
        """

        def decorator(cls: type[T]) -> type[T]:
            if name in self._items and not replace:
                raise ValueError(f"{self.kind} '{name}' 已注册，如需替换请传 replace=True")
            self._items[name] = cls()  # 实例化：注册表里存对象，不存类
            return cls

        return decorator

    def get(self, name: str) -> T | None:
        return self._items.get(name)

    def require(self, name: str) -> T:
        """取实现；不存在时抛出带说明的 KeyError。"""
        item = self.get(name)
        if item is None:
            raise KeyError(
                f"{self.kind} '{name}' 尚未注册，"
                f"可用：{', '.join(self.names()) or '（空）'}"
            )
        return item

    def names(self) -> list[str]:
        return sorted(self._items)

    def __contains__(self, name: str) -> bool:
        return name in self._items

    def __len__(self) -> int:
        return len(self._items)
