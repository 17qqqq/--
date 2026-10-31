// 测试用例相关接口，对应后端 app/routers/v1/test_cases.py
//
// 所有用例都属于某个项目，所以除了创建（project_id 在 body 里），
// 其余接口都要带 project_id 查询参数，后端用它校验归属。
import { request } from "./request";

/**
 * 分页查询某个项目的测试用例
 * @param {number} projectId
 * @param {{ page?: number, size?: number, enabled?: boolean }} options
 *   enabled 不传表示全部；true/false 只看启用/停用
 * @returns {Promise<{ total: number, items: Array }>}
 */
export const listTestCases = (projectId, { page = 1, size = 20, enabled } = {}) =>
  request("/test-cases", {
    query: { project_id: projectId, page, size, enabled },
  });

/**
 * 新建用例
 * @param {{
 *   project_id: number, name: string, description?: string,
 *   image_path?: string, mask_path?: string, enabled?: boolean
 * }} payload
 */
export const createTestCase = (payload) =>
  request("/test-cases", { method: "POST", body: payload });

/** 查询单个用例详情 */
export const getTestCase = (id, projectId) =>
  request(`/test-cases/${id}`, { query: { project_id: projectId } });

/**
 * 局部更新用例：只改 payload 里出现过的字段
 * @param {number} id
 * @param {number} projectId
 * @param {object} payload 可含 name/description/image_path/mask_path/enabled
 */
export const updateTestCase = (id, projectId, payload) =>
  request(`/test-cases/${id}`, {
    method: "PUT",
    query: { project_id: projectId },
    body: payload,
  });

/** 删除用例；已加入计划的关联行由数据库级联清理 */
export const deleteTestCase = (id, projectId) =>
  request(`/test-cases/${id}`, {
    method: "DELETE",
    query: { project_id: projectId },
  });
