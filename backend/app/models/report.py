# Report（测试报告）与 ReportSnapshot（指标快照）
#
# 报告 = 一次评估的汇总结论 + 一组指标数值。
# 指标怎么算由"鲁棒性指标统计"模块实现（见 app/interfaces/metrics.py），
# 本模块只负责把结果存下来、查出来。
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import REPORT_STATUS_PENDING
from app.db.base import Base
from app.models.mixins import PKMixin, TimestampMixin


class Report(PKMixin, TimestampMixin, Base):
    __tablename__ = "reports"

    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)

    # 关联的计划；手动建的报告可以为空
    test_plan_id: Mapped[int | None] = mapped_column(
        ForeignKey("test_plans.id"), nullable=True, index=True
    )

    # 关联的执行记录 id。
    # 执行模块目前还没有建 test_runs 表，所以这里先存普通整数、不加外键；
    # 等执行模块建表后再改成 ForeignKey("test_runs.id") 即可（SQLite 需要重建表）。
    test_run_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(String(1000), default="")

    # 状态：pending / finished / failed，见 core/constants.py
    status: Mapped[str] = mapped_column(
        String(20), default=REPORT_STATUS_PENDING, index=True
    )

    # 报告的汇总指标，结构由指标模块决定，例如：
    # {"dice": {"baseline": 0.93, "noise": 0.81, "drop": 0.12}}
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=None)

    # 生成时间（与 created_at 分开：报告可能先建记录、后异步生成）
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # 指标明细；删除报告时一起删（ORM 层 cascade）
    snapshots: Mapped[list["ReportSnapshot"]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ReportSnapshot.id",
    )


class ReportSnapshot(PKMixin, TimestampMixin, Base):
    """一条指标明细：某张图 / 某种扰动下的某个指标值。"""

    __tablename__ = "report_snapshots"

    report_id: Mapped[int] = mapped_column(
        ForeignKey("reports.id", ondelete="CASCADE"), index=True
    )

    # 扰动类型，例如 "baseline" / "brightness" / "noise"
    perturbation_type: Mapped[str] = mapped_column(String(50), index=True)

    # 指标名，与 metrics 注册表的名字一致（dice / iou / hd95 …）
    metric_name: Mapped[str] = mapped_column(String(50), index=True)

    metric_value: Mapped[float] = mapped_column(Float)

    # 同一指标无扰动时的值，方便直接算下降幅度
    baseline_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    # 对应哪条用例；允许为空（按扰动类型聚合时没有具体用例）
    case_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    report: Mapped[Report] = relationship(back_populates="snapshots")
