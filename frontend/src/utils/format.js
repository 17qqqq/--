// 后端返回 ISO 时间（2026-01-01T12:00:00），页面统一显示到秒
export const formatDate = (value) =>
  value ? value.replace("T", " ").slice(0, 19) : "-";
