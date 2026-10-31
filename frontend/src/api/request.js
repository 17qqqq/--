// 统一请求封装：所有页面只调用 api 目录下的函数，不直接写 fetch
//
// 地址策略：
// - 开发环境：/api/v1 由 Vite 代理到 http://127.0.0.1:8000
// - 打包后：/api/v1 与前端页面同源，由 FastAPI 同时提供
// 所以这里默认使用相对路径，桌面应用里不需要改任何地址。
const API_BASE = import.meta.env.VITE_API_BASE || "/api/v1";

/**
 * 发送请求并解包统一响应体 { code, message, data }
 *
 * @param {string} path 以 / 开头的接口路径，例如 "/projects"
 * @param {object} options
 * @param {"GET"|"POST"|"PUT"|"PATCH"|"DELETE"} [options.method]
 * @param {object} [options.body] 请求体，自动 JSON 序列化
 * @param {object} [options.query] 查询参数，自动拼接并跳过空值
 * @returns {Promise<any>} 响应体中的 data 字段
 */
export async function request(path, { method = "GET", body, query } = {}) {
  const url = new URL(`${API_BASE}${path}`, window.location.origin);

  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, value);
      }
    });
  }

  let response;
  try {
    response = await fetch(url, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    // fetch 抛错通常代表后端没启动或端口不对
    throw new Error("无法连接后端服务，请确认 FastAPI 已启动");
  }

  const json = await response.json().catch(() => null);

  // 后端约定：HTTP 非 2xx 或 code !== 0 都视为失败
  if (!response.ok || (json && json.code !== 0)) {
    throw new Error((json && json.message) || `请求失败（HTTP ${response.status}）`);
  }

  // 兼容 204 等无响应体的情况
  return json ? json.data : null;
}
