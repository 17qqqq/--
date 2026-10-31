// 当前工作项目：模型选择、扰动配置、工作台共用同一个项目上下文。
//
// 放在单独 store 里，避免“模型页选了项目 B、扰动卡片还停在项目 A”的情况。
// 项目列表也由这里统一加载，各页面不再各自请求、各自写回退逻辑。
import { ref } from "vue";
import { defineStore } from "pinia";

import { listProjects } from "@/api/project";

export const useWorkspaceStore = defineStore("workspace", () => {
  const activeProjectId = ref(null);
  const projects = ref([]);
  const projectTotal = ref(0);
  const projectsLoading = ref(false);

  function setActiveProject(projectId) {
    activeProjectId.value =
      projectId === null || projectId === undefined || projectId === ""
        ? null
        : projectId;
  }

  /**
   * 拉取项目列表，并校正当前项目：当前项目已不存在时回退到第一个。
   * 失败时清空列表并把异常抛给调用方，由页面决定是否提示。
   */
  async function loadProjects() {
    projectsLoading.value = true;
    try {
      // 后端 size 上限是 100；项目更多时这里要改成分页或搜索
      const data = await listProjects(1, 100);
      projects.value = data.items;
      projectTotal.value = data.total;

      if (!data.items.some((project) => project.id === activeProjectId.value)) {
        setActiveProject(data.items[0]?.id ?? null);
      }
      return data;
    } catch (error) {
      projects.value = [];
      projectTotal.value = 0;
      throw error;
    } finally {
      projectsLoading.value = false;
    }
  }

  return {
    activeProjectId,
    projects,
    projectTotal,
    projectsLoading,
    setActiveProject,
    loadProjects,
  };
});
