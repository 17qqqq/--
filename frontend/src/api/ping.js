// 连通性检测接口
import { request } from "./request";

export const ping = () => request("/ping");
