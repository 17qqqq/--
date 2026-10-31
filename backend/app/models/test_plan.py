# TestPlan（测试计划）与计划-用例关联表
#
# 一个计划 = 选一个项目 + 选一个模型 + 勾选若干用例 + 一份扰动配置快照。
# 执行模块拿到计划后按快照执行；本模块只负责"编排"和存储，不跑推理。
from sqlalchemy import (
    JSON,
    Column,
    ForeignKey,
    String,
    Table,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import PLAN_STATUS_DRAFT
from app.db.base import Base
from app.models.mixins import PKMixin, TimestampMixin
from app.models.test_case import TestCase

# 计划与用例的多对多关联表。
# ondelete="CASCADE"：删计划或删用例时，关联行自动清理（SQLite 已开启外键）。
test_plan_cases = Table(
    "test_plan_cases",
    Base.metadata,
    Column(
        "plan_id",
        ForeignKey("test_plans.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "case_id",
        ForeignKey("test_cases.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class TestPlan(PKMixin, TimestampMixin, Base):
    __tablename__ = "test_plans"

    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[str] = mapped_column(String(500), default="")

    # 状态取值见 app/core/constants.py（draft / ready / running / finished）
    status: Mapped[str] = mapped_column(String(20), default=PLAN_STATUS_DRAFT, index=True)

    # 计划指定使用的模型；允许为空（创建时还没选模型）
    model_id: Mapped[int | None] = mapped_column(
        ForeignKey("ml_models.id"), nullable=True, index=True
    )

    # 创建计划时把当前扰动配置整份拷一份存下来：
    # 之后用户改项目的扰动开关，不会影响已经建好的历史计划。
    # 结构：{enable_brightness, enable_contrast, enable_noise, params, strength}
    perturbation_snapshot: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, default=None
    )

    # 计划包含的用例；lazy="selectin" 表示查询计划时顺带用一条 IN 查询取回用例，
    # 避免在序列化时逐个触发查询（N+1）。
    cases: Mapped[list[TestCase]] = relationship(
        secondary=test_plan_cases,
        lazy="selectin",
    )
