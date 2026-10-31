<!--
  扰动参数配置页
  ─────────────────────────────────────────────────────────────────────
  职责：选择项目 → 读取该项目的三个扰动开关 → 修改 → 保存到后端。
  数据来源：store/perturbation.js（和工作台卡片共用同一份状态）。
  后端接口：GET/PUT /api/v1/perturbations/{project_id}
            （定义在 backend/app/routers/v1/perturbations.py）

  交互链路：
    打开页面 → listProjects() 拿项目列表 → 默认选第一个
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

    <!--
      兜底提示：apiReady 由下面的 PERTURBATION_API_READY 控制。
      现在后端已实现，这个提示不会出现；保留它是为了以后后端没启动时，
      能明确告诉用户"开关只在当前窗口生效"，而不是让用户以为保存成功。
    -->
    <el-alert
      v-if="!apiReady"
      class="api-alert"
      type="warning"
      :closable="false"
      show-icon
      title="后端扰动配置接口尚未实现，当前开关仅保存在本次运行中"
    />

    <el-card shadow="never" class="config-card">
      <div class="toolbar">
        <div class="project-picker">
          <span class="toolbar-label">项目</span>
          <!--
            v-model="projectId"：projectId 是 computed（见 script），
            get 读 workspace.activeProjectId，set 调 store.setActiveProject，
            所以这里选项目 = 全局切换项目，工作台/模型页会跟着变。
            @change：切换项目后立刻按新项目拉一次配置。
          -->
          <el-select
            v-model="projectId"
            :loading="projectsLoading"
            :disabled="projects.length === 0"
            placeholder="请选择项目"
            class="project-select"
            @change="loadConfig"
          >
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </div>

        <div class="toolbar-actions">
          <el-button :disabled="!projectId" @click="resetForm">恢复默认</el-button>
          <el-button type="primary" :loading="saving" :disabled="!projectId" @click="save">
            保存配置
          </el-button>
        </div>
      </div>

      <!-- 项目列表或配置请求进行中时显示整体 loading，避免用户点到半成品状态 -->
      <div v-loading="projectsLoading || configLoading" class="option-list">
        <!--
          没有项目时也保留三个开关，只是禁用。
          这样功能入口始终可见，用户不会以为页面坏了。
        -->
        <div v-if="!projectsLoading && projects.length === 0" class="no-project">
          <span>还没有项目，请先创建项目后再配置扰动参数</span>
          <el-button type="primary" link @click="$router.push('/projects')">去创建项目</el-button>
        </div>

        <!--
          开关列表由 PERTURBATION_OPTIONS 渲染，页面本身不写死三种扰动。
          新增扰动类型：
            1. store/perturbation.js 的 PERTURBATION_OPTIONS 加一项
            2. DEFAULT_PERTURBATION_CONFIG 加同名 key
            3. 后端 models/perturbation.py 加同名列（要重建表）
          注意 option.key 和 config 对象的字段名必须完全一致，
          因为 v-model="config[option.key]" 直接用 key 取值。
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
              :disabled="!projectId"：没有项目时只读，但开关仍然显示。
            -->
            <el-switch v-model="config[option.key]" :disabled="!projectId" />
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
// 页面脚本：只负责"取数据、改状态、提示用户"，
// 真正的请求和竞态处理都在 store/perturbation.js 里。
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import PageHeader from "@/components/PageHeader.vue";
import { listProjects } from "@/api/project";
import {
  PERTURBATION_OPTIONS,
  usePerturbationStore,
} from "@/store/perturbation";

// 功能开关：后端 /api/v1/perturbations/{project_id} 已实现。
// 如果以后要临时停用后端（比如演示时没有启动 FastAPI），
// 把它改成 false，页面就会退回"只在当前窗口生效"的本地模式。
const PERTURBATION_API_READY = true;
const apiReady = PERTURBATION_API_READY;

// 开关文案/字段名统一来自 store，页面不重复定义
const perturbationOptions = PERTURBATION_OPTIONS;

const perturbationStore = usePerturbationStore();

// 页面自己的加载状态：只影响本页的按钮和 loading 遮罩，
// 不放 store，是因为工作台不需要这些状态。
const projects = ref([]);
const projectsLoading = ref(false);
const configLoading = ref(false);
const saving = ref(false);

// 当前项目：可读可写的 computed。
// get 从 workspace store 读，set 写回 workspace，
// 所以 el-select 的 v-model 能直接绑定，工作台/模型页用的是同一个项目。
const projectId = computed({
  get: () => perturbationStore.activeProjectId,
  set: (value) => perturbationStore.setActiveProject(value),
});

// 当前项目的配置对象。注意它来自 store 里的 reactive 对象，
// 模板里 v-model="config[option.key]" 改的就是 Pinia 状态本身，
// 不是本地副本——这正是工作台能实时同步的原因。
const config = computed(() => perturbationStore.getConfig(projectId.value));

/**
 * 加载项目列表，并确定"当前项目"。
 *
 * 为什么先加载项目再加载配置：
 * 配置接口需要 project_id，没有项目就没有配置可读。
 * 项目优先复用 workspace 里已选中的那个，避免从工作台跳过来时被重置成第一个。
 */
async function loadProjects() {
  projectsLoading.value = true;
  try {
    // 后端 size 上限是 100；项目更多时这里需要改为分页或搜索
    const data = await listProjects(1, 100);
    projects.value = data.items;

    // 保持工作台已经选中的项目；项目不存在时才回退到第一个
    const activeExists = data.items.some(
      (project) => project.id === perturbationStore.activeProjectId,
    );
    if (!activeExists) {
      perturbationStore.setActiveProject(data.items[0]?.id ?? null);
    } else {
      // 确保共享 store 里已经有这个项目的配置对象
      perturbationStore.setActiveProject(perturbationStore.activeProjectId);
    }

    await loadConfig();
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    projectsLoading.value = false;
  }
}

/**
 * 读取当前项目的配置。
 *
 * 请求本身在 store.loadConfig() 里：
 * - 后端 GET 会在项目第一次访问时自动创建默认配置
 * - store 内部用请求序号防竞态（快速切项目时丢弃旧结果）
 * 页面只负责 loading 和错误提示。
 */
async function loadConfig() {
  if (!projectId.value) return;

  // 后端未启用时，共享 store 里已经是当前配置，不需要再发请求
  if (!PERTURBATION_API_READY) return;

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

/**
 * 恢复默认：只改本地状态，不写数据库。
 * 用户还需要点「保存配置」才会真正落库——这样误点还能再改回来。
 */
function resetForm() {
  if (!projectId.value) return;
  perturbationStore.resetConfig(projectId.value);
  ElMessage.info("已恢复默认开关，点击“保存配置”后生效");
}

/**
 * 保存配置：调用 store.saveConfig() → PUT 后端 → 用返回值覆盖本地。
 * 成功后后端返回的 updated_at 等字段也会同步到 store，
 * 工作台那张卡片读的是同一份数据，不需要额外刷新。
 */
async function save() {
  if (!projectId.value) return;

  if (!PERTURBATION_API_READY) {
    ElMessage.success("配置已在当前窗口生效（后端接口实现后会持久化）");
    return;
  }

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
.api-alert {
  margin-bottom: 16px;
}

.config-card {
  max-width: 860px;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.project-picker {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toolbar-label {
  font-size: 13px;
  color: #4b5563;
}

.project-select {
  width: 260px;
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
