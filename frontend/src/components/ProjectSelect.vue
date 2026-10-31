<!-- 项目选择器：直接读写 workspace 的当前项目，选中后发出 change -->
<template>
  <div class="project-picker">
    <span class="toolbar-label">项目</span>
    <el-select
      v-model="projectId"
      :loading="workspace.projectsLoading"
      :disabled="!workspace.projects.length"
      placeholder="请选择项目"
      class="project-select"
      @change="$emit('change', $event)"
    >
      <el-option
        v-for="project in workspace.projects"
        :key="project.id"
        :label="project.name"
        :value="project.id"
      />
    </el-select>
  </div>
</template>

<script setup>
import { computed } from "vue";

import { useWorkspaceStore } from "@/store/workspace";

defineEmits(["change"]);

const workspace = useWorkspaceStore();

const projectId = computed({
  get: () => workspace.activeProjectId,
  set: (value) => workspace.setActiveProject(value),
});
</script>

<style scoped>
.project-picker {
  display: flex;
  align-items: center;
  gap: 10px;
}

.project-select {
  width: 240px;
}
</style>
