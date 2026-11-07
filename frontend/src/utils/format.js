// 后端返回 ISO 时间（2026-01-01T12:00:00），页面统一显示到秒
export const formatDate = (value) =>
  value ? value.replace("T", " ").slice(0, 19) : "-";

// 报告状态 → el-tag 的文案和颜色；未知状态原样显示，避免新增状态时页面空白
const REPORT_STATUS = {
  pending: { label: "待生成", type: "info" },
  finished: { label: "已完成", type: "success" },
  failed: { label: "失败", type: "danger" },
};

export const statusMeta = (status) =>
  REPORT_STATUS[status] || { label: status || "-", type: "info" };

export const formatMetricValue = (value) =>
  typeof value === "number" ? Number(value.toFixed(4)) : String(value ?? "-");

// metrics 的结构由指标模块决定，常见形式是一层 key + 数值或一层嵌套对象。
// shortcut: 只展开两层，指标模块使用更深结构时改为递归或直接展示 JSON
export function metricRows(metrics) {
  if (!metrics || typeof metrics !== "object") return [];

  return Object.entries(metrics).map(([key, value]) => ({
    key,
    value:
      value && typeof value === "object"
        ? Object.entries(value)
            .map(([innerKey, innerValue]) => `${innerKey} ${formatMetricValue(innerValue)}`)
            .join(" / ")
        : formatMetricValue(value),
  }));
}

export const formatMetrics = (metrics) => {
  const rows = metricRows(metrics);
  return rows.length
    ? rows.map((row) => `${row.key}: ${row.value}`).join(" · ")
    : "-";
};
