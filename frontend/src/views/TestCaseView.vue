<!-- 测试用例页面：管理当前项目下的待测样本（原图 + 金标准掩码） -->
<template>
  <div class="page">
    <PageHeader
      title="测试用例"
      description="管理当前项目的待测样本。每条用例登记一张原图和一张金标准掩码的路径。"
    >
      <template #actions>
        <el-button :loading="loading" @click="fetchList">刷新</el-button>
        <el-button type="primary" :disabled="!projectId" @click="openCreate">
          新建用例
        </el-button>
      </template>
    </PageHeader>

    <!-- 项目上下文：与模型选择、扰动配置共用 workspace 里的当前项目 -->
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar">
        <ProjectSelect @change="handleProjectChange" />

        <el-input
          v-model="keyword"
          class="filter-input"
          placeholder="按名称筛选当前页"
          clearable
        />
        <span class="toolbar-tip">共 {{ total }} 个用例</span>
      </div>
    </el-card>

    <el-card shadow="never">
      <!--
        服务端分页：page / size 传给后端，后端返回 total 和当前页 items。
        keyword 只过滤当前页（后端暂未提供搜索参数），避免误导用户以为搜了全库。
      -->
      <el-table :data="filteredRows" v-loading="loading" row-key="id" stripe>
        <el-table-column prop="name" label="用例名称" min-width="140" show-overflow-tooltip />

        <el-table-column label="原图路径" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">{{ row.image_path || "-" }}</template>
        </el-table-column>

        <el-table-column label="掩码路径" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">{{ row.mask_path || "-" }}</template>
        </el-table-column>

        <el-table-column label="描述" min-width="120" show-overflow-tooltip>
          <template #default="{ row }">{{ row.description || "-" }}</template>
        </el-table-column>

        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <!-- 用 :model-value 而不是 v-model：等更新成功后再改 row.enabled，失败时开关不会留在错误状态 -->
            <div class="enabled-cell">
              <el-switch
                :model-value="row.enabled"
                :loading="togglingId === row.id"
                @change="(value) => toggleEnabled(row, value)"
              />
              <span class="muted">{{ row.enabled ? "启用" : "停用" }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="创建时间" width="170">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>

        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openEdit(row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
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
            <el-button v-else-if="projectId" type="primary" @click="openCreate">
              新建用例
            </el-button>
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

    <!-- 新建 / 编辑共用一个弹窗，editingId 为空表示新建 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑用例' : '新建用例'"
      width="560px"
      :close-on-click-modal="false"
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="92px">
        <el-form-item label="用例名称" prop="name">
          <el-input
            v-model="form.name"
            maxlength="100"
            show-word-limit
            placeholder="例如：001_左眼"
          />
        </el-form-item>

        <el-form-item label="原图路径" prop="image_path">
          <el-input
            v-model="form.image_path"
            maxlength="500"
            placeholder="相对 backend/，例如：storage/datasets/1/001.png"
          />
        </el-form-item>

        <el-form-item label="掩码路径" prop="mask_path">
          <el-input
            v-model="form.mask_path"
            maxlength="500"
            placeholder="金标准血管掩码，例如：storage/datasets/1/001_mask.png"
          />
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            maxlength="500"
            show-word-limit
            placeholder="可选，例如：拍摄设备、分辨率等"
          />
        </el-form-item>

        <el-form-item label="参与测试" prop="enabled">
          <el-switch v-model="form.enabled" />
          <span class="form-tip">停用后不会被新计划选到，已加入的计划不受影响</span>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">
          {{ editingId ? "保存" : "创建" }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";

import PageHeader from "@/components/PageHeader.vue";
import ProjectSelect from "@/components/ProjectSelect.vue";
import {
  createTestCase,
  deleteTestCase,
  listTestCases,
  updateTestCase,
} from "@/api/testCase";
import { useWorkspaceStore } from "@/store/workspace";
import { formatDate } from "@/utils/format";

const workspace = useWorkspaceStore();

// 项目由 ProjectSelect 写入 workspace，这里只读
const projectId = computed(() => workspace.activeProjectId);

// ---- 列表状态 ----
const rows = ref([]);
const total = ref(0);
const page = ref(1);
const size = ref(10);
const loading = ref(false);
const keyword = ref("");
const togglingId = ref(null);

const filteredRows = computed(() => {
  const key = keyword.value.trim().toLowerCase();
  if (!key) return rows.value;
  return rows.value.filter((row) => row.name.toLowerCase().includes(key));
});

const emptyText = computed(() => {
  if (!workspace.projects.length) return "还没有项目，请先创建项目";
  if (!projectId.value) return "请先选择顶部的项目";
  return "当前项目还没有用例，点击“新建用例”开始";
});

// 竞态保护：快速切换项目时，先发出的请求可能后返回。
// 每次请求领一个序号，只有最后一次发出的响应才允许写回页面。
let loadSeq = 0;

async function loadProjects() {
  try {
    await workspace.loadProjects();
    if (workspace.activeProjectId) {
      await fetchList();
    }
  } catch (error) {
    ElMessage.error(error.message);
  }
}

async function fetchList() {
  // 没有选中项目时不发请求；自增序号让在途的旧请求作废
  if (!projectId.value) {
    loadSeq += 1;
    rows.value = [];
    total.value = 0;
    return;
  }

  const seq = ++loadSeq;
  loading.value = true;
  try {
    const data = await listTestCases(projectId.value, {
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

function handleProjectChange() {
  page.value = 1;
  keyword.value = "";
  fetchList();
}

function handleSizeChange() {
  page.value = 1;
  fetchList();
}

// ---- 状态切换 ----
async function toggleEnabled(row, value) {
  if (!projectId.value) return;
  togglingId.value = row.id;
  try {
    const updated = await updateTestCase(row.id, projectId.value, {
      enabled: value,
    });
    row.enabled = updated.enabled;
    ElMessage.success(value ? `已启用：${row.name}` : `已停用：${row.name}`);
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    togglingId.value = null;
  }
}

// ---- 删除 ----
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `删除后，已加入测试计划的关联也会一并移除（计划本身保留）。确定删除用例「${row.name}」吗？`,
      "删除用例",
      {
        type: "warning",
        confirmButtonText: "删除",
        cancelButtonText: "取消",
      },
    );
  } catch {
    return; // 用户点了取消
  }

  try {
    await deleteTestCase(row.id, projectId.value);
    ElMessage.success("用例已删除");
    // 删掉当前页最后一条时回退一页，避免停在空页
    if (rows.value.length === 1 && page.value > 1) {
      page.value -= 1;
    }
    await fetchList();
  } catch (error) {
    ElMessage.error(error.message);
  }
}

// ---- 新建 / 编辑弹窗 ----
const dialogVisible = ref(false);
const submitting = ref(false);
const editingId = ref(null);
const formRef = ref(null);

const emptyForm = {
  name: "",
  description: "",
  image_path: "",
  mask_path: "",
  enabled: true,
};
const form = reactive({ ...emptyForm });

// 规则与后端 TestCaseCreate / TestCaseUpdate 保持一致
const rules = {
  name: [
    { required: true, whitespace: true, message: "请输入用例名称", trigger: "blur" },
    { max: 100, message: "最多 100 个字符", trigger: "blur" },
  ],
  description: [{ max: 500, message: "最多 500 个字符", trigger: "blur" }],
  image_path: [{ max: 500, message: "最多 500 个字符", trigger: "blur" }],
  mask_path: [{ max: 500, message: "最多 500 个字符", trigger: "blur" }],
};

function resetForm() {
  editingId.value = null;
  Object.assign(form, emptyForm);
  formRef.value?.clearValidate();
}

function openCreate() {
  if (!projectId.value) return;
  resetForm();
  dialogVisible.value = true;
}

function openEdit(row) {
  resetForm();
  editingId.value = row.id;
  form.name = row.name;
  form.description = row.description;
  form.image_path = row.image_path;
  form.mask_path = row.mask_path;
  form.enabled = row.enabled;
  dialogVisible.value = true;
}

async function submit() {
  const valid = await formRef.value?.validate().catch(() => false);
  if (!valid || !projectId.value) return;

  const payload = {
    name: form.name.trim(),
    description: form.description.trim(),
    image_path: form.image_path.trim(),
    mask_path: form.mask_path.trim(),
    enabled: form.enabled,
  };

  submitting.value = true;
  try {
    if (editingId.value) {
      // 更新是局部语义，但整份表单提交也没问题：字段都在 TestCaseUpdate 里
      await updateTestCase(editingId.value, projectId.value, payload);
      ElMessage.success("用例已更新");
    } else {
      await createTestCase({ project_id: projectId.value, ...payload });
      ElMessage.success("用例已创建");
      // 列表按 id 升序，新建的用例落在最后一页；直接翻过去，避免"建完看不见"
      page.value = Math.max(1, Math.ceil((total.value + 1) / size.value));
    }
    dialogVisible.value = false;
    await fetchList();
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    submitting.value = false;
  }
}

onMounted(loadProjects);
</script>

<style scoped>
.enabled-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.muted {
  font-size: 13px;
  color: #6b7280;
}

.form-tip {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
}
</style>
