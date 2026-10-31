// 路由表：所有页面在这里注册
import { createRouter, createWebHashHistory } from "vue-router";

import AppLayout from "@/layouts/AppLayout.vue";

const routes = [
  {
    path: "/",
    component: AppLayout,
    // 打开应用默认进入工作台
    redirect: "/dashboard",
    children: [
      {
        path: "dashboard",
        name: "dashboard",
        component: () => import("@/views/DashboardView.vue"),
        meta: { title: "工作台" },
      },
      {
        path: "projects",
        name: "projects",
        component: () => import("@/views/ProjectListView.vue"),
        meta: { title: "项目管理" },
      },
      {
        path: "models",
        name: "models",
        component: () => import("@/views/ModelSelectView.vue"),
        meta: { title: "模型选择" },
      },
      {
        path: "perturbations",
        name: "perturbations",
        component: () => import("@/views/PerturbationConfigView.vue"),
        meta: { title: "扰动参数配置" },
      },
      {
        path: "test-cases",
        name: "test-cases",
        component: () => import("@/views/TestCaseView.vue"),
        meta: { title: "测试用例" },
      },
      {
        path: "test-plans",
        name: "test-plans",
        component: () => import("@/views/TestPlanView.vue"),
        meta: { title: "测试计划" },
      },
      {
        path: "test-runs",
        name: "test-runs",
        component: () => import("@/views/TestRunView.vue"),
        meta: { title: "执行记录" },
      },
      {
        path: "reports",
        name: "reports",
        component: () => import("@/views/ReportView.vue"),
        meta: { title: "测试报告" },
      },
    ],
  },
  // 未匹配的地址统一回到工作台，避免桌面窗口出现空白页
  { path: "/:pathMatch(.*)*", redirect: "/dashboard" },
];

const router = createRouter({
  // 桌面应用 / pywebview 环境使用 hash 模式最稳：
  // 地址形如 http://127.0.0.1:8000/#/projects，不依赖服务端路由回退。
  // 如果将来部署到有 Nginx fallback 的 Web 环境，可改为 createWebHistory()。
  history: createWebHashHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
});

// 根据路由 meta 自动更新窗口标题
router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · 测试平台` : "测试平台";
});

export default router;
