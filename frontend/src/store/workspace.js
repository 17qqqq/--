// 当前工作项目：模型选择、扰动配置、工作台共用同一个项目上下文。
//
// 放在单独 store 里，避免“模型页选了项目 B、扰动卡片还停在项目 A”的情况。
import { ref } from "vue";
import { defineStore } from "pinia";

export const useWorkspaceStore = defineStore("workspace", () => {
  const activeProjectId = ref(null);

  function setActiveProject(projectId) {
    activeProjectId.value =
      projectId === null || projectId === undefined || projectId === ""
        ? null
        : projectId;
  }

  return { activeProjectId, setActiveProject };
});
