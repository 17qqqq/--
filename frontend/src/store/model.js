// 模型列表的共享状态。
//
// 模型选择页和工作台小卡片都读这里的 models，
// 因此在模型页启用/新建模型后，返回工作台看到的是同一份数据。
import { computed, ref } from "vue";
import { defineStore } from "pinia";

import {
  activateModel as apiActivateModel,
  createModel as apiCreateModel,
  listModels,
} from "@/api/model";
import { useWorkspaceStore } from "@/store/workspace";

export const useModelStore = defineStore("model", () => {
  const workspace = useWorkspaceStore();

  const models = ref([]);
  const loading = ref(false);

  // 防止快速切换项目时，旧请求的结果覆盖新项目
  let requestSeq = 0;

  const activeProjectId = computed(() => workspace.activeProjectId);
  const activeModel = computed(
    () => models.value.find((model) => model.is_active) || null,
  );

  async function loadModels(projectId = workspace.activeProjectId) {
    if (!projectId) {
      requestSeq += 1;
      models.value = [];
      loading.value = false;
      return [];
    }

    const seq = ++requestSeq;
    loading.value = true;
    try {
      const data = await listModels(projectId, 1, 100);
      if (seq !== requestSeq) return models.value;

      models.value = data.items;
      return models.value;
    } catch (error) {
      if (seq === requestSeq) {
        models.value = [];
      }
      throw error;
    } finally {
      if (seq === requestSeq) {
        loading.value = false;
      }
    }
  }

  async function createModel(payload) {
    if (!workspace.activeProjectId) {
      throw new Error("请先选择项目");
    }
    const created = await apiCreateModel({
      ...payload,
      project_id: workspace.activeProjectId,
    });
    await loadModels(workspace.activeProjectId);
    return created;
  }

  async function activate(modelId) {
    if (!workspace.activeProjectId) {
      throw new Error("请先选择项目");
    }
    const result = await apiActivateModel(modelId, workspace.activeProjectId);
    await loadModels(workspace.activeProjectId);
    return result;
  }

  function reset() {
    requestSeq += 1;
    models.value = [];
    loading.value = false;
  }

  return {
    models,
    loading,
    activeProjectId,
    activeModel,
    loadModels,
    createModel,
    activate,
    reset,
  };
});
