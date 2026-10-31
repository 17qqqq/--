<!--当前为模型选择页面的界面代码 -->
<template>
  <div class="page">
    <PageHeader
      title="模型选择"
      description="为当前项目登记待测试的模型，并选择本次测试使用的模型。"
    >
      <template #actions>
        <el-button :loading="modelStore.loading" @click="refresh">刷新</el-button>
        <el-button type="primary" :disabled="!projectId" @click="openCreate">
          新建模型
        </el-button>
      </template>
    </PageHeader>

    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar">
        <div class="project-picker">
          <span class="toolbar-label">项目</span>
          <el-select
            v-model="projectId"
            :loading="projectsLoading"
            :disabled="projects.length === 0"
            placeholder="请选择项目"
            class="project-select"
            @change="handleProjectChange"
          >
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </div>

        <div class="active-model">
          <span class="toolbar-label">当前模型</span>
          <el-tag v-if="modelStore.activeModel" type="success" effect="plain">
            {{ modelStore.activeModel.name }}
            <template v-if="modelStore.activeModel.version">
              · {{ modelStore.activeModel.version }}
            </template>
          </el-tag>
          <span v-else class="muted">未启用</span>
        </div>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-table
        v-loading="modelStore.loading"
        :data="modelStore.models"
        row-key="id"
        :row-class-name="rowClassName"
      >
        <el-table-column prop="name" label="模型名称" min-width="150" show-overflow-tooltip />
        <el-table-column label="版本" width="110">
          <template #default="{ row }">{{ row.version || "-" }}</template>
        </el-table-column>
        <el-table-column prop="framework" label="框架" width="110" />
        <el-table-column label="文件路径" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">{{ row.file_path || "-" }}</template>
        </el-table-column>
        <el-table-column label="描述" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">{{ row.description || "-" }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_active" type="success" effect="plain">启用中</el-tag>
            <el-tag v-else type="info" effect="plain">未启用</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="!row.is_active"
              type="primary"
              link
              :loading="activatingId === row.id"
              :disabled="!projectId"
              @click="handleActivate(row)"
            >
              启用
            </el-button>
            <span v-else class="muted">当前使用</span>
          </template>
        </el-table-column>

        <template #empty>
          <el-empty
            :description="projects.length ? '当前项目还没有模型' : '还没有项目，请先创建项目'"
            :image-size="90"
          >
            <el-button
              v-if="!projects.length"
              type="primary"
              @click="$router.push('/projects')"
            >
              去创建项目
            </el-button>
            <el-button v-else type="primary" @click="openCreate">新建模型</el-button>
          </el-empty>
        </template>
      </el-table>
    </el-card>

    <!-- 新建模型：文件路径先手填，后续可以改成上传接口 -->
    <el-dialog
      v-model="dialogVisible"
      title="新建模型"
      width="520px"
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="96px">
        <el-form-item label="模型名称" prop="name">
          <el-input v-model="form.name" placeholder="例如：unet_vessel_v1" maxlength="100" />
        </el-form-item>
        <el-form-item label="版本" prop="version">
          <el-input v-model="form.version" placeholder="例如：1.0.0" maxlength="50" />
        </el-form-item>
        <el-form-item label="框架" prop="framework">
          <el-select v-model="form.framework" class="full-width">
            <el-option label="PyTorch" value="pytorch" />
            <el-option label="ONNX" value="onnx" />
            <el-option label="TensorFlow" value="tensorflow" />
          </el-select>
        </el-form-item>
        <el-form-item label="文件路径" prop="file_path">
          <el-input
            v-model="form.file_path"
            placeholder="可选，例如：storage/models/1/unet.pth"
            maxlength="500"
          />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="模型用途、训练数据等说明"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">
          创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";

import PageHeader from "@/components/PageHeader.vue";
import { listProjects } from "@/api/project";
import { useModelStore } from "@/store/model";
import { useWorkspaceStore } from "@/store/workspace";

const workspace = useWorkspaceStore();
const modelStore = useModelStore();

const projects = ref([]);
const projectsLoading = ref(false);
const dialogVisible = ref(false);
const submitting = ref(false);
const activatingId = ref(null);
const formRef = ref(null);

const projectId = computed({
  get: () => workspace.activeProjectId,
  set: (value) => workspace.setActiveProject(value),
});

const form = reactive({
  name: "",
  version: "",
  framework: "pytorch",
  file_path: "",
  description: "",
});

const rules = {
  name: [{ required: true, message: "请输入模型名称", trigger: "blur" }],
};

async function loadProjects() {
  projectsLoading.value = true;
  try {
    const data = await listProjects(1, 100);
    projects.value = data.items;

    // 保留工作台/配置页已选中的项目，只有它不存在时才回退到第一个
    const activeExists = data.items.some(
      (project) => project.id === workspace.activeProjectId,
    );
    if (!activeExists) {
      workspace.setActiveProject(data.items[0]?.id ?? null);
    }

    await modelStore.loadModels();
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    projectsLoading.value = false;
  }
}

async function refresh() {
  try {
    await modelStore.loadModels();
  } catch (error) {
    ElMessage.error(error.message);
  }
}

function handleProjectChange() {
  modelStore.loadModels().catch((error) => ElMessage.error(error.message));
}

function openCreate() {
  if (!projectId.value) return;
  dialogVisible.value = true;
}

function resetForm() {
  formRef.value?.resetFields();
  form.name = "";
  form.version = "";
  form.framework = "pytorch";
  form.file_path = "";
  form.description = "";
}

async function submit() {
  try {
    await formRef.value.validate();
  } catch {
    return;
  }

  submitting.value = true;
  try {
    await modelStore.createModel({ ...form });
    ElMessage.success("模型已创建");
    dialogVisible.value = false;
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    submitting.value = false;
  }
}

async function handleActivate(row) {
  activatingId.value = row.id;
  try {
    await modelStore.activate(row.id);
    ElMessage.success(`已启用模型：${row.name}`);
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    activatingId.value = null;
  }
}

function rowClassName({ row }) {
  return row.is_active ? "active-model-row" : "";
}

onMounted(loadProjects);
</script>

<style scoped>
.toolbar-card {
  margin-bottom: 16px;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.project-picker,
.active-model {
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

.muted {
  font-size: 13px;
  color: #9ca3af;
}

.full-width {
  width: 100%;
}

:deep(.active-model-row) td {
  background: #f0fdf4 !important;
}
</style>
