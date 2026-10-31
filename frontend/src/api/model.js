// 模型选择相关接口，对应后端 app/routers/v1/models.py
//
// 后端当前是骨架，业务逻辑补齐前这些接口会返回 501。
// 页面接入时只需要 import 这些函数，不要直接写 fetch。
import { request } from "./request";

/**
 * 分页查询某个项目下的模型
 * @param {number} projectId
 * @param {number} page
 * @param {number} size
 * @returns {Promise<{ total: number, items: Array }>}
 */
export const listModels = (projectId, page = 1, size = 20) =>
  request("/models", { query: { project_id: projectId, page, size } });

/**
 * 查询项目当前启用的模型
 * @param {number} projectId
 */
export const getActiveModel = (projectId) =>
  request("/models/active", { query: { project_id: projectId } });

/**
 * 登记一个模型
 * @param {{
 *   project_id: number,
 *   name: string,
 *   version?: string,
 *   framework?: string,
 *   file_path?: string,
 *   description?: string
 * }} payload
 */
export const createModel = (payload) =>
  request("/models", { method: "POST", body: payload });

/**
 * 启用指定模型
 * @param {number} modelId
 * @param {number} projectId
 */
export const activateModel = (modelId, projectId) =>
  request(`/models/${modelId}/activate`, {
    method: "PUT",
    query: { project_id: projectId },
  });
