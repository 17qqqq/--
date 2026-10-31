// Vite 配置：开发服务器、路径别名、后端代理、构建输出
import { fileURLToPath, URL } from "node:url";

import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],

  resolve: {
    alias: {
      // 统一用 @ 指向 src，避免出现 ../../../ 这种相对路径
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },

  server: {
    host: "127.0.0.1",
    port: 5173,
    // 开发时把 /api 转发给 FastAPI，前端代码里只写相对路径 /api/v1
    // 这样开发环境和打包后的桌面环境写法完全一致，不需要改代码
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },

  build: {
    // 打包产物由 FastAPI / pywebview 直接托管
    outDir: "dist",
    // 桌面应用本地加载，不需要 CDN，保留 sourcemap 方便排查
    sourcemap: false,
  },
});
