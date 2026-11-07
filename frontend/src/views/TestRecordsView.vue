<!--
  测试记录页

  由原来的「测试用例 / 测试计划 / 执行记录」三个页面合并而来：
  不再让用户分别维护用例、编排计划、查看执行状态，而是把每次测试产出的
  报告当作一条记录展示，主要结果直接取自报告的 metrics 汇总。

  数据链路：
    指标/执行模块 → POST /api/v1/reports → reports 表
    本页 → GET /api/v1/reports?project_id= → 列表
    「查看报告」→ /reports/{id}?project_id= → 完整报告
-->
<template>
  <div class="page">
    <PageHeader
      title="测试记录"
      description="汇总每次测试的主要结果。点击“查看报告”可进入完整报告。"
    >
      <template #actions>
        <el-button :loading="loading" @click="fetchList">刷新</el-button>
      </template>
    </PageHeader>

    <!-- 与工作台、模型页共用 workspace 里的当前项目 -->
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar">
        <ProjectSelect />
        <span class="toolbar-tip">共 {{ total }} 条记录</span>
      </div>
    </el-card>

    <el-card shadow="never">
      <!-- 服务端分页：后端按报告 id 倒序返回，最新的测试排在最前面 -->
      <el-table :data="rows" v-loading="loading" row-key="id" stripe>
        <el-table-column label="测试" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="record-title">{{ row.title }}</div>
            <div v-if="row.summary" class="record-summary">{{ row.summary }}</div>
          </template>
        </el-table-column>

        <!-- metrics 由指标模块定义结构，这里用通用格式化函数展示主要数值 -->
        <el-table-column label="主要结果" min-width="280" show-overflow-tooltip>
          <template #default="{ row }">{{ formatMetrics(row.metrics) }}</template>
        </el-table-column>

        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusMeta(row.status).type" effect="plain">
              {{ statusMeta(row.status).label }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="测试时间" width="170">
          <template #default="{ row }">
            {{ formatDate(row.generated_at || row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <!-- 真正的超链接：hash 路由生成 /#/reports/{id}?project_id=...，可右键新开 -->
            <router-link
              class="report-link"
              :to="{
                name: 'report-detail',
                params: { id: row.id },
                query: { project_id: projectId },
              }"
            >
              查看报告
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
              测试完成后，报告提交到后端就会出现在这里
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
import { formatDate, formatMetrics, statusMeta } from "@/utils/format";

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
  return "当前项目还没有测试记录";
});

// 竞态保护：快速切换项目时，先发出的请求可能后返回，只让最后一次响应写回页面
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

// 当前项目可能被其他页面改掉；即使本页被 KeepAlive 缓存，监听依然生效
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
.record-title {
  font-size: 13px;
  color: #111827;
}

.record-summary {
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
