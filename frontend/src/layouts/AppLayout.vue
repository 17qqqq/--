<template>
  <!-- 整体应用布局：左侧菜单 + 顶部栏 + 内容区 -->
  <el-container class="layout">
    <el-aside :width="appStore.asideWidth" class="aside">
      <div class="brand">
        <img class="brand-logo" src="@/assets/logo.svg" alt="logo" />
        <span v-show="!appStore.sidebarCollapsed" class="brand-name">VasoRAT</span>
      </div>

      <!--
        菜单项与路由一一对应：
        新增页面时，需要在下方 menus 数组里加一项，否则侧边栏看不见入口。
        router 属性让 el-menu 自动调用 router.push，不需要手写点击事件。
      -->
      <el-menu
        :default-active="route.path"
        :collapse="appStore.sidebarCollapsed"
        :collapse-transition="false"
        router
        class="side-menu"
        background-color="#111827"
        text-color="#cbd5e1"
        active-text-color="#ffffff"
      >
        <el-menu-item v-for="item in menus" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.title }}</template>
        </el-menu-item>
      </el-menu>

      <div v-show="!appStore.sidebarCollapsed" class="aside-footer">v0.1.0 · 本地运行</div>
    </el-aside>

    <!--
      .right 同时承载页面背景层、顶栏和内容区。
      背景层是绝对定位的独立图层，始终位于 header/main 和所有卡片下方；
      侧边栏 .aside 不在此容器内，所以不会受到自定义背景影响。
    -->
    <el-container class="right" :style="rightStyle">
      <div
        class="page-background"
        :style="appearanceStore.backgroundStyle"
        aria-hidden="true"
      ></div>

      <el-header class="header">
        <div class="header-left">
          <el-button text circle @click="appStore.toggleSidebar">
            <el-icon :size="18">
              <component :is="appStore.sidebarCollapsed ? Expand : Fold" />
            </el-icon>
          </el-button>
          <span class="header-title">{{ route.meta.title || "测试平台" }}</span>
        </div>

        <div class="header-right">
          <el-button
            text
            class="appearance-button"
            title="自定义页面背景和小窗口透明度"
            @click="appearanceVisible = true"
          >
            <el-icon><Brush /></el-icon>
            <span>外观</span>
          </el-button>
          <el-tag size="small" effect="plain" type="info">本地桌面版</el-tag>
        </div>
      </el-header>

      <el-main class="main">
        <!--
          页面切换动画；每个页面自己负责 .page 内边距。
          - transitionName 由菜单顺序判断：向后翻页用 slide-left，向前返回用 slide-right
          - KeepAlive 缓存页面组件，切回来时保留表单、分页、弹窗等状态
          - :key="currentRoute.path" 保证每个菜单页有独立的缓存实例
        -->
        <router-view v-slot="{ Component, route: currentRoute }">
          <transition :name="transitionName" mode="out-in">
            <keep-alive>
              <component :is="Component" :key="currentRoute.path" />
            </keep-alive>
          </transition>
        </router-view>
      </el-main>

      <AppearanceDrawer v-model="appearanceVisible" />
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
import {
  Brush,
  Calendar,
  Cpu,
  DataAnalysis,
  Document,
  Expand,
  Fold,
  Folder,
  Odometer,
  Setting,
  VideoPlay,
} from "@element-plus/icons-vue";

import AppearanceDrawer from "@/components/AppearanceDrawer.vue";
import { useAppStore } from "@/store/app";
import { useAppearanceStore } from "@/store/appearance";

const route = useRoute();
const appStore = useAppStore();
const appearanceStore = useAppearanceStore();

const appearanceVisible = ref(false);

// 内容区所有卡片共享同一个透明度变量，卡片内部表格也读取它
const rightStyle = computed(() => ({
  "--app-card-opacity": String(appearanceStore.cardOpacity),
}));

// 侧边栏菜单配置。title 同时用于菜单文字，路径必须和 router/index.js 中的 path 一致
const menus = [
  { path: "/dashboard", title: "工作台", icon: Odometer },
  { path: "/projects", title: "项目管理", icon: Folder },
  { path: "/models", title: "模型选择", icon: Cpu },
  { path: "/perturbations", title: "扰动参数配置", icon: Setting },
  { path: "/test-cases", title: "测试用例", icon: Document },
  { path: "/test-plans", title: "测试计划", icon: Calendar },
  { path: "/test-runs", title: "执行记录", icon: VideoPlay },
  { path: "/reports", title: "测试报告", icon: DataAnalysis },
];

// 切换方向：菜单顺序靠后 = 前进（slide-left），靠前 = 后退（slide-right）
const transitionName = ref("slide-left");

function getMenuIndex(path) {
  return menus.findIndex(
    (item) => path === item.path || path.startsWith(`${item.path}/`),
  );
}

let lastMenuIndex = getMenuIndex(route.path);

watch(
  () => route.path,
  (newPath) => {
    const nextIndex = getMenuIndex(newPath);

    // 未匹配菜单的页面不参与方向判断，避免 404/临时路由把方向打乱
    if (nextIndex === -1) return;

    if (lastMenuIndex !== -1 && nextIndex !== lastMenuIndex) {
      transitionName.value =
        nextIndex > lastMenuIndex ? "slide-left" : "slide-right";
    }

    lastMenuIndex = nextIndex;
  },
);
</script>

<style scoped>
.layout {
  height: 100vh;
}

.aside {
  display: flex;
  flex-direction: column;
  background: var(--app-aside-bg);
  transition: width 0.2s ease;
  overflow: hidden;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  height: var(--app-header-height);
  padding: 0 18px;
  color: #fff;
  white-space: nowrap;
  flex: none;
}

.brand-logo {
  width: 28px;
  height: 28px;
  flex: none;
}

.brand-name {
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.side-menu {
  flex: 1;
  border-right: none;
  overflow-y: auto;
}

.side-menu:not(.el-menu--collapse) {
  width: var(--app-aside-width);
}

/* 让选中菜单和品牌主色一致；Element Plus 默认会再叠一层背景色，所以用 !important */
:deep(.el-menu-item.is-active) {
  background: var(--el-color-primary) !important;
}

:deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.06) !important;
}

.aside-footer {
  flex: none;
  padding: 12px 18px;
  font-size: 12px;
  color: #64748b;
  white-space: nowrap;
}

.right {
  position: relative;
  min-width: 0;
  background: var(--app-bg);
}

/* 自定义背景独立成层，z-index: 0；header 和 main 都在它上面 */
.page-background {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background-color: var(--app-bg);
}

.header {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--app-header-height);
  padding: 0 16px;
  background: rgba(255, 255, 255, 0.86);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--app-border);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-title {
  font-size: 15px;
  font-weight: 600;
  color: #111827;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.appearance-button {
  gap: 4px;
}

.main {
  position: relative;
  z-index: 1;
  padding: 0;
  background: transparent;
  overflow-x: hidden;
  overflow-y: auto;
}

/*
  小窗口透明度：
  --app-card-opacity 由外观设置写入，1 = 不透明，0 = 完全透明。
  这里只作用于 .right 内部，因此侧边栏不受影响。
*/
.right :deep(.el-card) {
  background-color: rgba(255, 255, 255, var(--app-card-opacity, 1));
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  transition: background-color 0.2s ease;
}

/* 卡片里的表格原本是白底，改为透明后才能透出背景图 */
.right :deep(.el-card .el-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: transparent;
  --el-table-expanded-cell-bg-color: transparent;
}

/*
  页面切换动画（自定义 transition 类，名字保持 slide-left / slide-right）
  - slide-left：向前切换，旧页向左退出，新页从右边进入
  - slide-right：向后切换，方向相反
  - mode="out-in" 保证两个页面不会同时占位，避免高度抖动
*/
.slide-left-enter-active,
.slide-left-leave-active,
.slide-right-enter-active,
.slide-right-leave-active {
  transition: transform 0.24s ease, opacity 0.24s ease;
  will-change: transform, opacity;
}

.slide-left-enter-from {
  opacity: 0;
  transform: translateX(32px);
}

.slide-left-leave-to {
  opacity: 0;
  transform: translateX(-32px);
}

.slide-right-enter-from {
  opacity: 0;
  transform: translateX(-32px);
}

.slide-right-leave-to {
  opacity: 0;
  transform: translateX(32px);
}
</style>
