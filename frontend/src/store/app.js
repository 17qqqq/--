// 应用级 UI 状态：侧边栏折叠、窗口尺寸等
// Pinia setup store 写法：用 ref/computed/function 定义，最后 return 暴露出去
import { computed, ref } from "vue";
import { defineStore } from "pinia";

export const useAppStore = defineStore("app", () => {
  const sidebarCollapsed = ref(false);

  // 需要新增全局 UI 状态时，在这里加 ref，并在 return 中暴露
  const asideWidth = computed(() => (sidebarCollapsed.value ? "64px" : "220px"));

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value;
  }

  return { sidebarCollapsed, asideWidth, toggleSidebar };
});
