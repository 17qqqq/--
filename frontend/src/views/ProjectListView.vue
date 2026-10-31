<!--当前为项目管理页面的界面代码 -->
<template>
  <div class="page">
    <PageHeader title="项目管理" description="管理测试项目。当前页面已接通后端真实的创建和分页查询接口。">
      <template #actions>
        <el-button type="primary" @click="openCreate">新建项目</el-button>
      </template>
    </PageHeader>

    <el-card shadow="never">
      <div class="toolbar">
        <el-input
          v-model="keyword"
          class="filter-input"
          placeholder="按名称筛选当前页"
          clearable
        />
        <span class="toolbar-tip">共 {{ total }} 个项目</span>
        <el-button :loading="loading" @click="fetchList">刷新</el-button>
      </div>

      <!--
        分页是服务端分页：page / size 传给后端，后端返回 total 和当前页 items。
        如果以后后端支持按名称搜索，把 keyword 也作为查询参数传给 listProjects。
      -->
      <el-table :data="filteredRows" v-loading="loading" row-key="id" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="项目名称" min-width="180" show-overflow-tooltip />
        <el-table-column
          prop="description"
          label="描述"
          min-width="240"
          show-overflow-tooltip
        >
          <template #default="{ row }">{{ row.description || "-" }}</template>
        </el-table-column>
        <el-table-column prop="owner_id" label="负责人 ID" width="110" />
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>

        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>

        <template #empty>
          <el-empty description="暂无项目，点击右上角“新建项目”开始" :image-size="80" />
        </template>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="size"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @current-change="fetchList"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <!-- 新建项目弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      title="新建项目"
      width="480px"
      :close-on-click-modal="false"
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="84px">
        <el-form-item label="项目名称" prop="name">
          <el-input
            v-model="form.name"
            maxlength="100"
            show-word-limit
            placeholder="例如：登录模块回归"
          />
        </el-form-item>

        <el-form-item label="项目描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            maxlength="500"
            show-word-limit
            placeholder="可选"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";

import PageHeader from "@/components/PageHeader.vue";
import { createProject, deleteProject, listProjects } from "@/api/project";
import { useWorkspaceStore } from "@/store/workspace";

const workspace = useWorkspaceStore();

// ---- 列表状态 ----
const rows = ref([]);
const total = ref(0);
const page = ref(1);
const size = ref(10);
const loading = ref(false);
const keyword = ref("");

// 当前接口不支持服务端搜索，这里只过滤“当前页”，避免误导用户以为搜了全库
const filteredRows = computed(() => {
  const key = keyword.value.trim().toLowerCase();
  if (!key) return rows.value;
  return rows.value.filter((row) => row.name.toLowerCase().includes(key));
});

function formatDate(value) {
  return value ? value.replace("T", " ").slice(0, 19) : "-";
}

async function fetchList() {
  loading.value = true;
  try {
    const data = await listProjects(page.value, size.value);
    rows.value = data.items;
    total.value = data.total;
  } catch (error) {
    ElMessage.error(error.message);
    rows.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
}

function handleSizeChange() {
  page.value = 1;
  fetchList();
}

// ---- 新建项目 ----
const dialogVisible = ref(false);
const submitting = ref(false);
const formRef = ref();
const form = reactive({
  name: "",
  description: "",
});

const rules = {
  name: [
    { required: true, message: "请输入项目名称", trigger: "blur" },
    { max: 100, message: "最多 100 个字符", trigger: "blur" },
  ],
  description: [{ max: 500, message: "最多 500 个字符", trigger: "blur" }],
};

function openCreate() {
  dialogVisible.value = true;
}

function resetForm() {
  form.name = "";
  form.description = "";
  formRef.value?.clearValidate();
}

async function submit() {
  const valid = await formRef.value.validate().catch(() => false);
  if (!valid) return;

  submitting.value = true;
  try {
    await createProject({
      name: form.name.trim(),
      description: form.description.trim(),
      // 登录功能接入前先固定为种子管理员；接入后改成 userStore.userInfo.id
      owner_id: 1,
    });
    ElMessage.success("项目创建成功");
    dialogVisible.value = false;
    page.value = 1;
    await fetchList();
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    submitting.value = false;
  }
}

// ---- 删除项目 ----
// 后端会级联删除项目下的所有数据，所以确认文案必须写清后果。
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `删除后，该项目下的模型、测试用例、测试计划、报告和扰动配置都会一并删除，且无法恢复。确定删除「${row.name}」吗？`,
      "删除项目",
      {
        type: "warning",
        confirmButtonText: "删除",
        cancelButtonText: "取消",
      },
    );
  } catch {
    return; // 用户点了取消
  }

  // 删除的是当前工作项目时，清空选中，避免其他页面继续请求已删除的项目
  const wasActive = workspace.activeProjectId === row.id;

  try {
    await deleteProject(row.id);
    ElMessage.success("项目已删除");
    if (wasActive) {
      workspace.setActiveProject(null);
    }
    // 删掉当前页最后一条时回退一页，避免停在空页
    if (rows.value.length === 1 && page.value > 1) {
      page.value -= 1;
    }
    await fetchList();
    // 列表里还有项目时，自动把第一个设为当前项目
    if (wasActive) {
      workspace.setActiveProject(rows.value[0]?.id ?? null);
    }
  } catch (error) {
    ElMessage.error(error.message);
  }
}

onMounted(fetchList);
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.filter-input {
  width: 260px;
}

.toolbar-tip {
  margin-left: auto;
  font-size: 13px;
  color: #6b7280;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
