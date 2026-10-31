# 测试平台前端

Vue 3 + Vite + Vue Router + Pinia + Element Plus。

当前已完成应用骨架、整体布局、工作台、项目管理、模型选择、扰动参数配置和测试用例页；计划、执行、报告三个页面仍是带接入说明的占位页。

## 快速启动

先在项目根目录启动后端：

```bash
cd backend
py -3.11 -m uvicorn app.main:app --reload --port 8000
```

再启动前端：

```bash
cd frontend
npm install        # 首次运行
npm run dev
```

打开 http://127.0.0.1:5173/ 。开发服务器会把 `/api` 代理到 `127.0.0.1:8000`，所以前端代码里不需要写死后端地址。

生产构建：

```bash
npm run build      # 产物在 frontend/dist
npm run preview    # 本地预览构建结果
```

## 目录结构

```text
frontend/
├── index.html              # 唯一 HTML 入口，只放挂载点
├── vite.config.js          # 别名 @、开发端口、后端代理
├── public/                 # 原样复制到 dist 的静态文件（favicon 等）
└── src/
    ├── main.js             # 注册 Pinia / Router / Element Plus
    ├── App.vue             # 根组件，只渲染 router-view
    ├── api/                # 接口封装，页面不直接写 fetch
    │   ├── request.js      # 统一请求、查询参数、错误处理
    │   ├── ping.js
    │   └── project.js
    ├── layouts/
    │   └── AppLayout.vue   # 侧边栏 + 顶栏 + 内容区
    ├── router/
    │   └── index.js        # 路由表
    ├── store/              # Pinia 全局状态（app / appearance / model / perturbation / workspace）
    │   └── app.js          # 侧边栏折叠等 UI 状态
    ├── views/              # 页面级组件
    ├── components/         # 可复用组件
    ├── assets/             # 需要参与构建的图片、Logo
    └── styles/
        ├── variables.css   # 主题变量（主色、布局尺寸）
        └── main.css        # 全局基础样式
```

## 扩展指南

### 1. 新增一个页面

以“环境管理”为例：

1. 新建 `src/views/EnvironmentView.vue`，页面结构参考 `ProjectListView.vue`。
2. 在 `src/router/index.js` 的 `children` 里加一条：

   ```js
   {
     path: "environments",
     name: "environments",
     component: () => import("@/views/EnvironmentView.vue"),
     meta: { title: "环境管理" },
   }
   ```

3. 在 `src/layouts/AppLayout.vue` 的 `menus` 数组里加入口：

   ```js
   { path: "/environments", title: "环境管理", icon: Setting },
   ```

   图标从 `@element-plus/icons-vue` 导入，可去 Element Plus 官网图标页挑选。

### 2. 新增接口调用

1. 在 `src/api/` 下新建文件（如 `environment.js`），调用 `request`：

   ```js
   import { request } from "./request";

   export const listEnvironments = (page = 1, size = 20) =>
     request("/environments", { query: { page, size } });
   ```

2. 页面里 `import { listEnvironments } from "@/api/environment"` 后调用。
3. 后端需要在 `app/routers/v1/` 新增路由，并注册到 `app/routers/v1/__init__.py`。
4. 后端统一响应体是 `{ code, message, data }`，`request` 会自动返回 `data`，非 0 code 会抛错。

### 3. 新增全局状态

在 `src/store/` 下新建文件，使用 Pinia setup store：

```js
import { ref } from "vue";
import { defineStore } from "pinia";

export const useEnvironmentStore = defineStore("environment", () => {
  const currentId = ref(null);
  return { currentId };
});
```

页面里：

```js
import { useEnvironmentStore } from "@/store/environment";
const store = useEnvironmentStore();
```

### 4. 修改主题 / 视觉

- 主色、圆角、布局宽度：改 `src/styles/variables.css`。
- 页面内局部样式：写在对应 `.vue` 的 `<style scoped>`。
- 全局复位、滚动条、字体：改 `src/styles/main.css`。
- Element Plus 组件默认样式不要直接覆盖组件内部类名，优先用它的 CSS 变量。

### 5. 页面与组件怎么分工

- `views/`：一个路由对应一个页面，负责取数和页面编排。
- `components/`：可复用的展示组件，比如 `PageHeader`、`ComingSoon`；不要在里面直接调接口。
- 复杂页面可以拆成 `views/projects/ProjectFormDialog.vue` 这类子组件。

## 与后端、桌面化的关系

- 开发期：Vite 代理 `/api` 到 8000 端口。
- 打包后：`npm run build` 生成 `dist/`，由 FastAPI 用 `StaticFiles` 托管，同时提供 `/api/v1`，前后端同源。
- 桌面窗口：后续用 pywebview 打开本地 FastAPI 服务地址，用户看到的是独立窗口而不是浏览器。
- 路由使用 hash 模式（`/#/projects`），不依赖服务端路由回退，桌面环境更稳。

## 常见问题

| 现象 | 原因 |
| --- | --- |
| 页面能开但数据报“无法连接后端服务” | FastAPI 没启动，或端口不是 8000 |
| 所有接口 404 | 后端路由前缀不是 `/api/v1`，检查 `backend/app/core/config.py` |
| 修改后端代码没生效 | 后端启动时没加 `--reload` |
| 打包后接口地址不对 | 检查 `.env` 里的 `VITE_API_BASE`，默认 `/api/v1` 不要改成绝对地址 |
| 换电脑后跑不起来 | 先 `npm install`，Node 需要 20.19+ 或 22.12+（Vite 8 的要求） |
