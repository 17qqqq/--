// 测试报告接口，对应后端 app/routers/v1/reports.py
//
// 报告由指标/执行模块计算后通过 POST /reports 写入，前端只负责查询：
//   GET /reports?project_id=&page=&size=  列表（测试记录页、报告列表页）
//   GET /reports/{id}?project_id=         详情（含 snapshots 指标明细）
import { request } from "./request";

/**
 * 分页查询某个项目的报告；一条报告就是一次测试的结果
 * @returns {Promise<{ total: number, items: Array }>}
 */
export const listReports = (projectId, { page = 1, size = 20 } = {}) =>
  request("/reports", { query: { project_id: projectId, page, size } });

/** 查询报告详情，包含全部指标明细 */
export const getReport = (id, projectId) =>
  request(`/reports/${id}`, { query: { project_id: projectId } });
