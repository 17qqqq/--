<template>
  <div class="page">
    <PageHeader title="眼底血管分割模型鲁棒性自动测试平台" description="测试平台运行概览，数据来自本地 FastAPI 服务。">
      <template #actions>
        <el-button :loading="refreshing" @click="refresh">刷新数据</el-button>
      </template>
    </PageHeader>

    <el-row :gutter="16">
      <el-col v-for="card in cards" :key="card.key" :xs="24" :sm="12" :lg="6">
        <!-- 模型选择卡片：以列表展示当前项目的全部模型，和模型页共用 modelStore -->
        <el-card v-if="card.key === 'model'" shadow="never" class="stat-card model-card">
          <div class="card-title-row">
            <span class="stat-label">{{ card.label }}</span>
            <el-button link type="primary" @click="$router.push('/models')">
              管理
            </el-button>
          </div>

          <div v-loading="modelStore.loading" class="model-list">
            <div v-if="modelStore.models.length === 0" class="model-empty">
              暂无模型
            </div>
            <div
              v-for="model in modelStore.models"
              :key="model.id"
              class="model-row"
              :class="{ 'is-active': model.is_active }"
              :title="[model.file_path, model.description].filter(Boolean).join(' | ') || model.name"
            >
              <div class="model-main">
                <span class="model-name">{{ model.name }}</span>
                <span class="model-meta">
                  {{ model.version || "未标注版本" }} · {{ model.framework }}
                </span>
              </div>
              <el-tag v-if="model.is_active" size="small" type="success" effect="plain">
                启用中
              </el-tag>
            </div>
          </div>

          <div class="stat-hint model-hint">
            <span v-if="modelStore.models.length">{{ modelStore.models.length }} 个</span>
          </div>
        </el-card>

        <!--
          扰动参数配置卡片：
          - 开关状态来自 Pinia store（和配置页是同一份数据，天然同步）
          - 拨动开关会立即写回后端（togglePerturbation），刷新后仍然保持
          - 没有选中项目时开关禁用，但保留显示，功能入口始终可见
        -->
        <el-card v-else-if="card.key === 'perturbation'" shadow="never" class="stat-card perturbation-card">
          <div class="card-title-row">
            <span class="stat-label">{{ card.label }}</span>
            <el-button link type="primary" @click="$router.push('/perturbations')">
              管理
            </el-button>
          </div>

          <div class="dash-options">
            <div v-for="option in perturbationOptions" :key="option.key" class="dash-option">
              
              <span class="dash-option-name">{{ option.label }}</span>
              <el-switch
                size="small"
                :model-value="perturbationStore.isEnabled(activeProjectId, option.key)"
                :disabled="!activeProjectId"
                @update:model-value="
                // 工作台直接改开关时同步写回后端，避免回到配置页被覆盖
                  (value) => togglePerturbation(option.key, value)
                "
              />
            </div>
            <!--测试与缺陷检测和 鲁棒性指标统计没有设计，暂时为空 -->
          </div>
             <!-- 项目选择暂时为空 -->
          <div class="stat-hint dash-hint">
            <span>{{ activeProjectName ? `项目：${activeProjectName}` : "暂无项目" }}</span>
            <el-button link type="primary" @click="$router.push('/perturbations')">
              详细配置
            </el-button>
          </div>
        </el-card>

        <el-card v-else shadow="never" class="stat-card">
          <div class="stat-label">{{ card.label }}</div>
          <div class="stat-value">{{ card.value }}</div>
          <div class="stat-hint">{{ card.hint }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="lower">
      <el-col :xs="24" :lg="16">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>项目选择</span>
              <div class="card-header-right">
                <span class="muted">共 {{ projectTotal }} 个</span>
                <el-button text type="primary" @click="$router.push('/projects')">
                  查看全部
                </el-button>
              </div>
            </div>
          </template>

          <el-table :data="recentProjects" v-loading="loading" size="small" row-key="id">
            <el-table-column prop="name" label="项目名称" min-width="160" show-overflow-tooltip />
            <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
            <el-table-column label="创建时间" width="170">
              <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
            </el-table-column>

            <!-- 用表格自带的空插槽，避免出现两层空状态 -->
            <template #empty>
              <el-empty description="还没有项目，去项目管理页创建第一个吧" :image-size="80" />
            </template>
          </el-table>
        </el-card>
      </el-col>
       <!-- 系统状态显示 -->
      <el-col :xs="24" :lg="8">
        <el-card shadow="never">
          <template #header><span>系统状态</span></template>

          <div class="status-row">
            <span>后端服务</span>
            <el-tag :type="backendOnline ? 'success' : 'danger'" effect="plain">
              {{ backendOnline ? "已连接" : "未连接" }}
            </el-tag>
          </div>
          <div class="status-row">
            <span>接口地址</span>
            <code>/api/v1</code>
          </div>
          <div class="status-row">
            <span>数据库</span>
            <code>SQLite</code>
          </div>

          <el-alert
            v-if="!backendOnline"
            class="status-alert"
            type="error"
            :closable="false"
            show-icon
            title="请确认 FastAPI 已在 127.0.0.1:8000 启动"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import PageHeader from "@/components/PageHeader.vue";
import { ping } from "@/api/ping";
import { listProjects } from "@/api/project";
import { useModelStore } from "@/store/model";
import {
  PERTURBATION_OPTIONS,
  usePerturbationStore,
} from "@/store/perturbation";
import { useWorkspaceStore } from "@/store/workspace";

const workspaceStore = useWorkspaceStore();
const perturbationStore = usePerturbationStore();
const modelStore = useModelStore();

const refreshing = ref(false);
const loading = ref(false);
const backendOnline = ref(false);
const projectTotal = ref(0);
const recentProjects = ref([]);
const allProjects = ref([]);

const perturbationOptions = PERTURBATION_OPTIONS;

// 工作台、模型页、配置页共用同一个项目上下文
const activeProjectId = computed(() => workspaceStore.activeProjectId);
const activeProjectName = computed(() => {
  const activeId = workspaceStore.activeProjectId;
  const project = allProjects.value.find((item) => item.id === activeId);
  // 项目列表请求失败时保留编号，避免开关可用但项目名显示为空
  return project?.name || (activeId ? `项目 #${activeId}` : "");
});

// 顶部卡片。模型和扰动配置使用自定义内容，其余先保留占位
const cards = computed(() => [
  { key: "model", label: "模型选择" },
  { key: "perturbation", label: "扰动参数配置" },
  { key: "plans", label: "测试与缺陷检测", value: "--", hint: "后端接口待实现" },
  { key: "runs", label: "鲁棒性指标统计", value: "--", hint: "后端接口待实现" },
]);

function formatDate(value) {
  return value ? value.replace("T", " ").slice(0, 19) : "-";
}

/**
 * 工作台开关的写操作。
 *
 * 顺序很重要：
 * 1. 先改 store —— 开关立即响应，配置页（如果开着）同步变化，不用等网络
 * 2. 再 saveConfig() 写回后端 —— 否则切到配置页会重新 GET，
 *    把工作台刚改的状态覆盖掉
 *
 * 保存失败时只提示，不回滚本地开关：
 * 用户可以再拨一次重试，或去配置页点保存。
 */
async function togglePerturbation(key, value) {
  if (!activeProjectId.value) return;

  perturbationStore.setEnabled(activeProjectId.value, key, value);
  try {
    await perturbationStore.saveConfig();
  } catch (error) {
    ElMessage.error(`扰动配置保存失败：${error.message}`);
  }
}

// 顶部聚合数据。扰动开关的写操作通过 store 完成，和配置页共用状态
async function refresh() {
  refreshing.value = true;
  loading.value = true;

  try {
    // allSettled：即使后端没启动，也不会因为一个接口失败导致整个页面空白。
    // 这里取 100 条（后端上限），既能展示最近 5 条，也能找到当前选中的项目名称。
    const [pingResult, projectResult] = await Promise.allSettled([
      ping(),
      listProjects(1, 100),
    ]);

    backendOnline.value = pingResult.status === "fulfilled";

    if (projectResult.status === "fulfilled") {
      const items = projectResult.value.items;
      projectTotal.value = projectResult.value.total;
      allProjects.value = items;
      recentProjects.value = items.slice(0, 5);

      // 保持模型页/配置页选中的项目；只有它不存在时才回退到第一个项目
      const activeExists = items.some(
        (project) => project.id === workspaceStore.activeProjectId,
      );
      if (!activeExists) {
        workspaceStore.setActiveProject(items[0]?.id ?? null);
      }

      // 工作台模型卡片和模型选择页共用 modelStore
      await modelStore.loadModels().catch(() => {});

      // 读取当前项目已保存的扰动开关。
      // 这里用 catch(() => {}) 静默失败：工作台是概览页，
      // 后端挂了时不应该整页报错，开关停在默认关闭状态即可
      // （系统状态卡片会单独显示“未连接”）。
      await perturbationStore.loadConfig().catch(() => {});
    } else {
      projectTotal.value = 0;
      allProjects.value = [];
      recentProjects.value = [];
      modelStore.reset();
    }
  } finally {
    refreshing.value = false;
    loading.value = false;
  }
}
//css部分
onMounted(refresh);
</script>

<style scoped>
.stat-card {
  height: 100%;
  box-sizing: border-box;
  margin-bottom: 16px;
}

.card-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* 工作台模型列表：卡片高度有限，超出后内部滚动 */
.model-list {
  max-height: 96px;
  margin-top: 2px;
  overflow-y: auto;
}

.model-empty {
  padding: 16px 0;
  text-align: center;
  font-size: 12px;
  color: #9ca3af;
}

.model-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 4px 0;
  border-bottom: 1px dashed #eef2f7;
}

.model-row:last-child {
  border-bottom: none;
}

.model-main {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.model-name {
  max-width: 170px;
  overflow: hidden;
  font-size: 13px;
  color: #374151;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.model-row.is-active .model-name {
  font-weight: 600;
  color: #15803d;
}

.model-meta {
  overflow: hidden;
  font-size: 11px;
  color: #9ca3af;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.model-hint {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

/* 工作台上的扰动开关：只保留项目名 + 开关，保持卡片紧凑 */
.dash-options {
  margin-top: 4px;
}

.dash-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 3px 0;
  font-size: 13px;
  color: #374151;
}

.dash-option-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dash-hint {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.dash-hint .el-button {
  height: auto;
  padding: 0;
  font-size: 12px;
}

.stat-label {
  font-size: 13px;
  color: #6b7280;
}

.stat-value {
  margin-top: 8px;
  font-size: 28px;
  font-weight: 600;
  color: #111827;
}

.stat-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #9ca3af;
}

.lower {
  margin-top: 8px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.muted {
  font-size: 12px;
  color: #9ca3af;
}

.status-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  font-size: 13px;
  color: #4b5563;
  border-bottom: 1px dashed #eef2f7;
}

.status-row:last-of-type {
  border-bottom: none;
}

.status-row code {
  font-size: 12px;
  color: #2563eb;
}

.status-alert {
  margin-top: 12px;
}
</style>
