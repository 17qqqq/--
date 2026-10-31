// 项目相关接口，对应后端 app/routers/v1/projects.py
// 新增接口时：在这里加函数 → 页面里 import 调用 → 注释写清参数和返回结构
import { request } from "./request";

/**
 * 分页查询项目
 * @returns {Promise<{ total: number, items: Array }>}
 */
export const listProjects = (page = 1, size = 20) =>
  request("/projects", { query: { page, size } });

/**
 * 创建项目
 * @param {{ name: string, description?: string, owner_id?: number }} payload
 */
export const createProject = (payload) =>
  request("/projects", { method: "POST", body: payload });

/** 查询单个项目详情 */
export const getProject = (id) => request(`/projects/${id}`);

/**
 * 删除项目
 * 后端会级联清理该项目下的模型、用例、计划、报告和扰动配置。
 * @param {number} id
 */
export const deleteProject = (id) =>
  request(`/projects/${id}`, { method: "DELETE" });
