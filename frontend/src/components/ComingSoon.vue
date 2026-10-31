<template>
  <!-- 未实现模块的占位视图：明确告诉后来者“缺什么、怎么接” -->
  <div class="page">
    <PageHeader :title="title" :description="description" />

    <el-card shadow="never">
      <el-empty :description="emptyText" :image-size="96">
        <el-tag type="warning" effect="plain">后端接口待实现</el-tag>
      </el-empty>

      <div class="extension-guide">
        <h4>接入步骤</h4>
        <ol>
          <li v-for="(step, index) in steps" :key="index">{{ step }}</li>
        </ol>
        <p v-if="backendHint" class="backend-hint">{{ backendHint }}</p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import PageHeader from "@/components/PageHeader.vue";

defineProps({
  title: { type: String, required: true },
  description: { type: String, default: "" },
  emptyText: { type: String, default: "功能建设中" },
  backendHint: { type: String, default: "" },
  steps: { type: Array, default: () => [] },
});
</script>

<style scoped>
.extension-guide {
  max-width: 720px;
  margin: 0 auto 24px;
  padding: 16px 20px;
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  border-radius: 8px;
  color: #475569;
  font-size: 13px;
  line-height: 1.8;
}

.extension-guide h4 {
  margin: 0 0 8px;
  font-size: 14px;
  color: #334155;
}

.extension-guide ol {
  margin: 0;
  padding-left: 20px;
}

.backend-hint {
  margin: 10px 0 0;
  color: #b45309;
}
</style>
