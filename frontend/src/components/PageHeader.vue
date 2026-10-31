<template>
  <!-- 页面标题区：所有业务页统一使用，保证间距和排版一致 -->
  <div class="page-header">
    <div class="page-header-text">
      <h2 class="page-title">{{ title }}</h2>
      <p v-if="description" class="page-description">{{ description }}</p>
    </div>

    <div class="page-header-actions">
      <!-- 右侧操作按钮通过具名插槽传入，例如“新建项目”“刷新” -->
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, default: "" },
});
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #111827;
}

.page-description {
  margin: 6px 0 0;
  font-size: 13px;
  color: #6b7280;
}

.page-header-actions {
  flex: none;
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
