# MLModel（待测试的模型）
#
# 这里的“模型”指被测的眼底血管分割模型，不是 SQLAlchemy 的 model 概念。
# 表结构先按“一个项目可以登记多个模型，但同一时间只启用一个”设计；
# “只能有一个启用模型”属于业务规则，放在 services/model_service.py 里校验，
# 不在数据库层用唯一索引硬约束，方便以后支持多模型对比。
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import PKMixin, TimestampMixin


class MLModel(PKMixin, TimestampMixin, Base):
    __tablename__ = "ml_models"

    # 模型归属项目；项目删除时如何处理关联模型，在 service 层决定
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)

    name: Mapped[str] = mapped_column(String(100), index=True)
    version: Mapped[str] = mapped_column(String(50), default="")

    # 预留 pytorch / onnx / tensorflow 等；真正加载模型时再按框架分派
    framework: Mapped[str] = mapped_column(String(20), default="pytorch")

    # 只存模型文件路径，不要把二进制文件塞进 SQLite
    # 建议路径：backend/storage/models/{project_id}/{filename}
    file_path: Mapped[str] = mapped_column(String(500), default="")
    description: Mapped[str] = mapped_column(String(500), default="")

    # 当前项目正在使用的模型；同一项目由 service 保证最多一个为 True
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
