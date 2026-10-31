// 扰动参数配置接口，对应后端 app/routers/v1/perturbations.py
//
// 页面不直接写 fetch，统一走这里的函数：
//   PerturbationConfigView.vue —— 读写当前项目的开关
//   store/perturbation.js      —— 工作台和配置页共享的 loadConfig / saveConfig
//
// 后端返回结构（ResponseModel 包装）：
//   { code: 0, message: "ok", data: { id, project_id, enable_*, params, strength, ... } }
// request() 已经帮我们解包成 data，所以下面函数的返回值就是配置对象本身。
import { request } from "./request";

/**
 * 获取指定项目的扰动配置
 * 后端在项目第一次访问时会自动创建默认配置（三个开关 false、params null、strength 100）
 * @param {number} projectId
 * @returns {Promise<{
 *   id: number, project_id: number,
 *   enable_brightness: boolean, enable_contrast: boolean, enable_noise: boolean,
 *   params: object|null, strength: number,
 *   created_at: string, updated_at: string
 * }>}
 */
export const getPerturbationConfig = (projectId) =>
  request(`/perturbations/${projectId}`);

/**
 * 保存指定项目的扰动配置（三个开关均为 bool）
 * 只传出现过的字段即可，未传字段后端保持原值
 * @param {number} projectId
 * @param {{ enable_brightness?: boolean, enable_contrast?: boolean, enable_noise?: boolean,
 *           params?: object|null, strength?: number }} payload
 * @returns {Promise<object>} 保存后的完整配置
 */
export const updatePerturbationConfig = (projectId, payload) =>
  request(`/perturbations/${projectId}`, { method: "PUT", body: payload });
