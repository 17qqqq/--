<!--
  扰动参数配置页
  ─────────────────────────────────────────────────────────────────────
  职责：选择项目 → 读取该项目的扰动开关 → 修改 → 保存到后端。
  数据来源：store/perturbation.js（和工作台卡片共用同一份状态）。
  后端接口：GET/PUT /api/v1/perturbations/{project_id}

  交互链路：
    打开页面 → workspace.loadProjects() 拿项目列表 → 默认选第一个
             → GET 配置 → store.setConfig()
    拨动开关 → 直接改 store 里的配置对象（工作台同步变化）
    点保存   → PUT 配置 → 用返回值覆盖 store
    点恢复默认 → 只改本地，保存后才写库
-->
<template>
  <div class="page">
    <PageHeader
      title="扰动参数配置"
      description="为当前项目选择参与鲁棒性测试的扰动类型，开关支持多选。"
    />

    <el-card shadow="never" class="config-card">
      <div class="toolbar">
        <!-- 选项目 = 全局切换项目，工作台/模型页会跟着变 -->
        <ProjectSelect @change="handleProjectChange" />

        <div class="toolbar-actions">
          <el-button :disabled="!projectId" @click="resetForm">恢复默认</el-button>
          <el-button type="primary" :loading="saving" :disabled="!projectId" @click="save">
            保存配置
          </el-button>
        </div>
      </div>

      <!-- 项目列表或配置请求进行中时显示整体 loading，避免用户点到半成品状态 -->
      <div v-loading="workspace.projectsLoading || configLoading" class="option-list">
        <!-- 没有项目时也保留三个开关，只是禁用，功能入口始终可见 -->
        <div
          v-if="!workspace.projectsLoading && workspace.projects.length === 0"
          class="no-project"
        >
          <span>还没有项目，请先创建项目后再配置扰动参数</span>
          <el-button type="primary" link @click="$router.push('/projects')">去创建项目</el-button>
        </div>

        <!--
          开关列表由 PERTURBATION_OPTIONS 渲染，页面本身不写死三种扰动。
          新增扰动类型：
            1. store/perturbation.js 的 PERTURBATION_OPTIONS 加一项
            2. DEFAULT_PERTURBATION_CONFIG 加同名 key
            3. 后端 models/perturbation.py 加同名列（要重建表）
        -->
        <div v-for="option in perturbationOptions" :key="option.key" class="option-row">
          <div class="option-text">
            <div class="option-label">{{ option.label }}</div>
            <div class="option-desc">{{ option.description }}</div>
          </div>
          <div class="option-control">
            <span class="option-status" :class="{ 'is-on': config[option.key] }">
              {{ config[option.key] ? "已启用" : "已关闭" }}
            </span>
            <!--
              v-model 直接绑定 store 里的配置对象：
              拨动开关 = 修改 Pinia 状态，工作台那张卡片的同名开关会立即同步。
              这里不单独发请求，统一由「保存配置」按钮触发 PUT。
            -->
            <el-switch v-model="config[option.key]" :disabled="!projectId" />
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import PageHeader from "@/components/PageHeader.vue";
import ProjectSelect from "@/components/ProjectSelect.vue";
import {
  PERTURBATION_OPTIONS,
  usePerturbationStore,
} from "@/store/perturbation";
import { useWorkspaceStore } from "@/store/workspace";

// 开关文案/字段名统一来自 store，页面不重复定义
const perturbationOptions = PERTURBATION_OPTIONS;

const workspace = useWorkspaceStore();
const perturbationStore = usePerturbationStore();

// 页面自己的加载状态：只影响本页的按钮和 loading 遮罩，不放 store
const configLoading = ref(false);
const saving = ref(false);

// 项目由 ProjectSelect 写入 workspace，这里只读
const projectId = computed(() => perturbationStore.activeProjectId);

// v-model="config[option.key]" 改的就是 Pinia 状态本身，所以工作台能实时同步
const config = computed(() => perturbationStore.getConfig(projectId.value));

async function loadProjects() {
  try {
    await workspace.loadProjects();
    await loadConfig();
  } catch (error) {
    ElMessage.error(error.message);
  }
}

async function loadConfig() {
  if (!projectId.value) return;

  configLoading.value = true;
  try {
    await perturbationStore.loadConfig(projectId.value);
  } catch (error) {
    ElMessage.error(error.message);
    // 读取失败时退回默认开关，避免页面上留着上一个项目的旧值
    perturbationStore.resetConfig(projectId.value);
  } finally {
    configLoading.value = false;
  }
}

function handleProjectChange(value) {
  // 先建好本地配置对象，避免配置加载完成前开关写到只读兜底对象
  perturbationStore.setActiveProject(value);
  loadConfig();
}

// 恢复默认：只改本地状态，点「保存配置」后才真正落库
function resetForm() {
  if (!projectId.value) return;
  perturbationStore.resetConfig(projectId.value);
  ElMessage.info("已恢复默认开关，点击“保存配置”后生效");
}

async function save() {
  if (!projectId.value) return;

  saving.value = true;
  try {
    await perturbationStore.saveConfig(projectId.value);
    ElMessage.success("配置已保存");
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    saving.value = false;
  }
}

onMounted(loadProjects);
</script>

<style scoped>
.config-card {
  max-width: 860px;
}

.toolbar {
  justify-content: space-between;
  margin-bottom: 8px;
}

.toolbar-actions {
  display: flex;
  gap: 8px;
}

.option-list {
  margin-top: 8px;
  border-top: 1px solid #eef2f7;
}

.no-project {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 12px 4px;
  font-size: 13px;
  color: #b45309;
  background: #fffbeb;
  border-bottom: 1px solid #fde68a;
}

.option-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 18px 4px;
  border-bottom: 1px solid #eef2f7;
}

.option-row:last-child {
  border-bottom: none;
}

.option-label {
  font-size: 14px;
  font-weight: 500;
  color: #111827;
}

.option-desc {
  margin-top: 4px;
  font-size: 12px;
  color: #6b7280;
}

.option-control {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: none;
}

.option-status {
  min-width: 42px;
  text-align: right;
  font-size: 12px;
  color: #9ca3af;
}

.option-status.is-on {
  color: var(--el-color-primary);
}
</style>
