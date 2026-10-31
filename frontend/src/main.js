// 应用入口：注册 Pinia、Router、Element Plus，然后挂载 App
import { createApp } from "vue";
import { createPinia } from "pinia";
import ElementPlus from "element-plus";
import zhCn from "element-plus/es/locale/lang/zh-cn";

// 样式顺序很重要：先加载 Element Plus 默认样式，再加载项目主题覆盖它
import "element-plus/dist/index.css";
import "./styles/variables.css";
import "./styles/main.css";

import App from "./App.vue";
import router from "./router";

const app = createApp(App);

// 全局状态管理。新增 store 时只需在 src/store 下创建文件，无需在这里注册
app.use(createPinia());

// 页面路由，路由表见 src/router/index.js
app.use(router);

// Element Plus 采用全量引入，适合桌面应用（本地加载、不依赖 CDN）
// 如果后期想减小体积，可改成 unplugin-vue-components 按需引入
app.use(ElementPlus, { locale: zhCn });

app.mount("#app");
