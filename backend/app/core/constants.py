# 全局常量
#
# 状态值统一放这里，schema 的 Literal、service 的默认值都引用同一份，
# 避免"一处写 draft、一处写草稿"导致前后端对不上。

# 测试计划状态
PLAN_STATUS_DRAFT = "draft"        # 草稿：还在编辑，不参与执行
PLAN_STATUS_READY = "ready"        # 就绪：可以执行
PLAN_STATUS_RUNNING = "running"    # 执行中
PLAN_STATUS_FINISHED = "finished"  # 已完成
PLAN_STATUSES = (
    PLAN_STATUS_DRAFT,
    PLAN_STATUS_READY,
    PLAN_STATUS_RUNNING,
    PLAN_STATUS_FINISHED,
)

# 报告状态（报告由执行模块触发生成，生成前先建记录）
REPORT_STATUS_PENDING = "pending"    # 待生成/生成中
REPORT_STATUS_FINISHED = "finished"  # 已生成
REPORT_STATUS_FAILED = "failed"      # 生成失败
REPORT_STATUSES = (
    REPORT_STATUS_PENDING,
    REPORT_STATUS_FINISHED,
    REPORT_STATUS_FAILED,
)
