<!--
  测试报告详情页

  路由：/reports/:id?project_id=项目ID
  project_id 放在查询参数里，是因为后端详情接口需要按项目做归属校验；
  从报告列表或测试记录页进入时都会带上它。
-->
<template>
  <div class="page">
    <PageHeader
      title="报告详情"
      description="报告内容由指标/执行模块计算，本页只负责展示。"
    >
      <template #actions>
        <el-button @click="goBack">返回报告列表</el-button>
      </template>
    </PageHeader>

    <el-alert
      v-if="error"
      class="detail-alert"
      type="error"
      :closable="false"
      show-icon
      :title="error"
    />

    <el-card v-else v-loading="loading" shadow="never" class="detail-card">
      <template v-if="report">
        <div class="report-head">
          <div class="report-head-text">
            <h3 class="report-title">{{ report.title }}</h3>
            <p v-if="report.summary" class="report-summary">{{ report.summary }}</p>
          </div>
          <el-tag :type="statusMeta(report.status).type" effect="plain">
            {{ statusMeta(report.status).label }}
          </el-tag>
        </div>

        <el-descriptions :column="2" border class="report-meta">
          <el-descriptions-item label="项目">{{ projectName }}</el-descriptions-item>
          <el-descriptions-item label="关联计划">
            {{ report.test_plan_id ? `#${report.test_plan_id}` : "-" }}
          </el-descriptions-item>
          <el-descriptions-item label="执行记录">
            {{ report.test_run_id ? `#${report.test_run_id}` : "-" }}
          </el-descriptions-item>
          <el-descriptions-item label="生成时间">
            {{ formatDate(report.generated_at) }}
          </el-descriptions-item>
        </el-descriptions>

        <h4 class="section-title">主要指标</h4>
        <div v-if="metrics.length" class="metric-list">
          <div v-for="item in metrics" :key="item.key" class="metric-row">
            <span class="metric-key">{{ item.key }}</span>
            <span class="metric-value">{{ item.value }}</span>
          </div>
        </div>
        <p v-else class="muted">报告没有提交汇总指标</p>

        <h4 class="section-title">指标明细</h4>
        <el-table :data="report.snapshots" size="small" row-key="id">
          <el-table-column prop="perturbation_type" label="扰动类型" min-width="120" />
          <el-table-column prop="metric_name" label="指标" min-width="120" />
          <el-table-column label="指标值" width="110">
            <template #default="{ row }">{{ formatMetricValue(row.metric_value) }}</template>
          </el-table-column>
          <el-table-column label="基准值" width="110">
            <template #default="{ row }">
              {{ row.baseline_value == null ? "-" : formatMetricValue(row.baseline_value) }}
            </template>
          </el-table-column>
          <el-table-column label="用例 ID" width="100">
            <template #default="{ row }">{{ row.case_id ?? "-" }}</template>
          </el-table-column>

          <template #empty>
            <el-empty description="没有指标明细" :image-size="70" />
          </template>
        </el-table>
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import PageHeader from "@/components/PageHeader.vue";
import { getReport } from "@/api/report";
import { useWorkspaceStore } from "@/store/workspace";
import {
  formatDate,
  formatMetricValue,
  metricRows,
  statusMeta,
} from "@/utils/format";

const route = useRoute();
const router = useRouter();
const workspace = useWorkspaceStore();

const report = ref(null);
const loading = ref(false);
const error = ref("");

const reportId = computed(() => Number(route.params.id));
// 链接里带了 project_id；直接访问时回退到当前项目
const projectId = computed(
  () => Number(route.query.project_id) || workspace.activeProjectId,
);

const projectName = computed(() => {
  const project = workspace.projects.find((item) => item.id === projectId.value);
  return project?.name || `#${projectId.value}`;
});

const metrics = computed(() => metricRows(report.value?.metrics));

async function load() {
  error.value = "";
  report.value = null;

  if (!reportId.value) {
    error.value = "报告编号无效";
    return;
  }
  if (!projectId.value) {
    error.value = "缺少项目参数，请从报告列表进入";
    return;
  }

  loading.value = true;
  try {
    report.value = await getReport(reportId.value, projectId.value);
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
}

function goBack() {
  router.push({
    name: "reports",
    query: projectId.value ? { project_id: projectId.value } : {},
  });
}

onMounted(async () => {
  // 直接刷新详情页时 workspace 里还没有项目，能选项目名就顺手加载一次
  if (!workspace.projects.length) {
    await workspace.loadProjects().catch(() => {});
  }
  // 让返回列表时仍停在这份报告所属的项目
  if (projectId.value) {
    workspace.setActiveProject(projectId.value);
  }
  await load();
});
</script>

<style scoped>
.detail-alert {
  margin-bottom: 16px;
}

.detail-card {
  min-height: 160px;
}

.report-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.report-head-text {
  min-width: 0;
}

.report-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.report-summary {
  margin: 6px 0 0;
  font-size: 13px;
  line-height: 1.6;
  color: #6b7280;
}

.report-meta {
  margin-top: 16px;
}

.section-title {
  margin: 20px 0 10px;
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.metric-list {
  border: 1px solid #eef2f7;
  border-radius: 6px;
}

.metric-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 8px 12px;
  font-size: 13px;
  border-bottom: 1px solid #eef2f7;
}

.metric-row:last-child {
  border-bottom: none;
}

.metric-key {
  color: #4b5563;
}

.metric-value {
  color: #111827;
  text-align: right;
}

.muted {
  font-size: 13px;
  color: #9ca3af;
}
</style>
