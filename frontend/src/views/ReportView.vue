<!--
  测试报告列表页

  后端对应 app/routers/v1/reports.py：
    列表 GET /reports?project_id=&page=&size=
    详情 GET /reports/{id}?project_id=
  报告数据由指标/执行模块计算后提交，本页和报告详情页只负责展示。
-->
<template>
  <div class="page">
    <PageHeader
      title="测试报告"
      description="查看每次测试生成的完整报告，包括汇总指标和逐条指标明细。"
    >
      <template #actions>
        <el-button :loading="loading" @click="fetchList">刷新</el-button>
      </template>
    </PageHeader>

    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar">
        <ProjectSelect />
        <span class="toolbar-tip">共 {{ total }} 份报告</span>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-table :data="rows" v-loading="loading" row-key="id" stripe>
        <el-table-column label="报告标题" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">
            <router-link
              class="report-title-link"
              :to="{
                name: 'report-detail',
                params: { id: row.id },
                query: { project_id: projectId },
              }"
            >
              {{ row.title }}
            </router-link>
            <div v-if="row.summary" class="report-summary">{{ row.summary }}</div>
          </template>
        </el-table-column>

        <el-table-column label="关联计划" width="110">
          <template #default="{ row }">
            {{ row.test_plan_id ? `#${row.test_plan_id}` : "-" }}
          </template>
        </el-table-column>

        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusMeta(row.status).type" effect="plain">
              {{ statusMeta(row.status).label }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="指标明细" width="100">
          <template #default="{ row }">{{ row.snapshots?.length || "-" }}</template>
        </el-table-column>

        <el-table-column label="生成时间" width="170">
          <template #default="{ row }">
            {{ formatDate(row.generated_at || row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <router-link
              class="report-link"
              :to="{
                name: 'report-detail',
                params: { id: row.id },
                query: { project_id: projectId },
              }"
            >
              查看详情
            </router-link>
          </template>
        </el-table-column>

        <template #empty>
          <el-empty :description="emptyText" :image-size="90">
            <el-button
              v-if="!workspace.projects.length"
              type="primary"
              @click="$router.push('/projects')"
            >
              去创建项目
            </el-button>
            <span v-else-if="projectId" class="empty-hint">
              报告由指标/执行模块计算后提交
            </span>
          </el-empty>
        </template>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="size"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @current-change="fetchList"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { ElMessage } from "element-plus";

import PageHeader from "@/components/PageHeader.vue";
import ProjectSelect from "@/components/ProjectSelect.vue";
import { listReports } from "@/api/report";
import { useWorkspaceStore } from "@/store/workspace";
import { formatDate, statusMeta } from "@/utils/format";

const workspace = useWorkspaceStore();

// 项目由 ProjectSelect 写入 workspace，这里只读
const projectId = computed(() => workspace.activeProjectId);

const rows = ref([]);
const total = ref(0);
const page = ref(1);
const size = ref(10);
const loading = ref(false);

const emptyText = computed(() => {
  if (!workspace.projects.length) return "还没有项目，请先创建项目";
  if (!projectId.value) return "请先选择顶部的项目";
  return "当前项目还没有测试报告";
});

// 与测试记录页相同的竞态保护：只允许最后一次请求写回页面
let loadSeq = 0;

async function fetchList() {
  if (!projectId.value) {
    loadSeq += 1;
    rows.value = [];
    total.value = 0;
    return;
  }

  const seq = ++loadSeq;
  loading.value = true;
  try {
    const data = await listReports(projectId.value, {
      page: page.value,
      size: size.value,
    });
    if (seq !== loadSeq) return;
    rows.value = data.items;
    total.value = data.total;
  } catch (error) {
    if (seq !== loadSeq) return;
    ElMessage.error(error.message);
    rows.value = [];
    total.value = 0;
  } finally {
    if (seq === loadSeq) loading.value = false;
  }
}

async function loadProjects() {
  try {
    await workspace.loadProjects();
  } catch (error) {
    ElMessage.error(error.message);
  }
}

function handleSizeChange() {
  page.value = 1;
  fetchList();
}

// 项目变化（含从其他页面切换后返回）时自动刷新列表
watch(
  projectId,
  () => {
    page.value = 1;
    fetchList();
  },
  { immediate: true },
);

onMounted(loadProjects);
</script>

<style scoped>
.report-title-link {
  font-size: 13px;
  color: var(--el-color-primary);
  text-decoration: none;
}

.report-title-link:hover {
  text-decoration: underline;
}

.report-summary {
  margin-top: 2px;
  font-size: 12px;
  color: #909399;
}

.report-link {
  font-size: 13px;
  color: var(--el-color-primary);
  text-decoration: none;
}

.report-link:hover {
  text-decoration: underline;
}

.empty-hint {
  font-size: 12px;
  color: #909399;
}
</style>
