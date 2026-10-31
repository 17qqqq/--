# TestCase（测试用例）—— 一个待测样本
#
# 表结构只保留"编排测试计划"需要的最小字段：
# 用例属于哪个项目、叫什么、原图和金标准掩码放在哪。
# 图像读取/预处理由执行模块负责，这里只存路径，不存二进制。
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import PKMixin, TimestampMixin


class TestCase(PKMixin, TimestampMixin, Base):
    __tablename__ = "test_cases"

    # 用例归属项目；计划只能挑选同项目的用例
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)

    name: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[str] = mapped_column(String(500), default="")

    # 原图（RGB）与金标准血管掩码的路径。
    # 约定用相对 backend/ 的路径，例如 storage/datasets/1/001.png
    image_path: Mapped[str] = mapped_column(String(500), default="")
    mask_path: Mapped[str] = mapped_column(String(500), default="")

    # 停用的用例不参与新计划；已有计划的历史记录不受影响
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
