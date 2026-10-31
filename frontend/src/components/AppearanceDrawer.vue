<template>
  <!--
    外观设置抽屉。
    页面背景由 AppLayout 中的背景层渲染，这里只负责修改 Pinia store。
  -->
  <el-drawer
    v-model="visible"
    title="外观设置"
    size="380px"
    append-to-body
    class="appearance-drawer"
  >
    <div class="appearance-body">
      <el-alert
        v-if="appearanceStore.storageError"
        class="storage-alert"
        type="warning"
        :closable="false"
        show-icon
        :title="appearanceStore.storageError"
      />

      <section class="setting-section">
        <h3 class="section-title">页面背景</h3>
        <p class="section-desc">
          背景作用于侧边栏以外的区域，并位于所有卡片下方。
        </p>

        <el-radio-group
          v-model="appearanceStore.backgroundMode"
          class="mode-group"
        >
          <el-radio-button value="default">默认</el-radio-button>
          <el-radio-button value="color">纯色</el-radio-button>
          <el-radio-button value="image">图片</el-radio-button>
        </el-radio-group>

        <!-- 纯色背景 -->
        <div v-if="appearanceStore.backgroundMode === 'color'" class="color-block">
          <div class="color-row">
            <el-color-picker
              v-model="appearanceStore.backgroundColor"
              :predefine="BACKGROUND_PRESETS"
            />
            <code>{{ appearanceStore.backgroundColor }}</code>
          </div>

          <div class="color-presets" aria-label="预设背景色">
            <button
              v-for="color in BACKGROUND_PRESETS"
              :key="color"
              type="button"
              class="color-swatch"
              :class="{ active: appearanceStore.backgroundColor === color }"
              :style="{ backgroundColor: color }"
              :title="color"
              :aria-label="`使用背景色 ${color}`"
              @click="appearanceStore.backgroundColor = color"
            />
          </div>
        </div>

        <!-- 自定义图片背景 -->
        <div v-if="appearanceStore.backgroundMode === 'image'" class="image-block">
          <input
            ref="fileInput"
            class="hidden-input"
            type="file"
            accept="image/*"
            @change="handleFileChange"
          />

          <div
            v-if="appearanceStore.backgroundImage"
            v-loading="processing"
            class="image-preview"
            :style="{ backgroundImage: `url(${appearanceStore.backgroundImage})` }"
          >
            <span class="preview-tag">预览</span>
          </div>

          <button
            v-else
            type="button"
            class="image-picker"
            :disabled="processing"
            @click="pickFile"
          >
            <el-icon :size="24"><Picture /></el-icon>
            <span>{{ processing ? "正在处理图片..." : "选择本地图片" }}</span>
          </button>

          <div class="image-actions">
            <el-button :loading="processing" @click="pickFile">
              {{ appearanceStore.backgroundImage ? "更换图片" : "选择图片" }}
            </el-button>
            <el-button
              v-if="appearanceStore.backgroundImage"
              :disabled="processing"
              @click="appearanceStore.removeBackgroundImage"
            >
              移除图片
            </el-button>
          </div>

          <p v-if="appearanceStore.backgroundImageName" class="file-name">
            {{ appearanceStore.backgroundImageName }}
          </p>
          <p class="hint">
            支持 JPG / PNG / WebP；大尺寸图片会自动压缩后保存到本地。
          </p>
        </div>
      </section>

      <el-divider />

      <section class="setting-section">
        <div class="section-heading">
          <h3 class="section-title">小窗口透明度</h3>
          <span class="value-badge">
            {{ appearanceStore.cardTransparency }}%
          </span>
        </div>
        <p class="section-desc">
          作用于内容区的所有卡片。0% 为不透明，100% 为完全透明。
        </p>

        <el-slider
          v-model="appearanceStore.cardTransparency"
          :min="0"
          :max="100"
          :step="1"
          :show-tooltip="false"
        />

        <div class="slider-scale">
          <span>不透明</span>
          <span>完全透明</span>
        </div>

        <div class="quick-values">
          <el-button
            v-for="value in quickTransparency"
            :key="value"
            size="small"
            plain
            :type="appearanceStore.cardTransparency === value ? 'primary' : 'default'"
            @click="appearanceStore.cardTransparency = value"
          >
            {{ value }}%
          </el-button>
        </div>
      </section>

      <el-divider />

      <el-button class="reset-button" @click="handleReset">
        恢复默认外观
      </el-button>
    </div>
  </el-drawer>
</template>

<script setup>
import { ref } from "vue";
import { ElMessage } from "element-plus";
import { Picture } from "@element-plus/icons-vue";

import {
  BACKGROUND_PRESETS,
  useAppearanceStore,
} from "@/store/appearance";

// 父组件通过 v-model 控制抽屉显示
const visible = defineModel({ type: Boolean, default: false });

const appearanceStore = useAppearanceStore();

const quickTransparency = [0, 25, 50, 75];

const fileInput = ref(null);
const processing = ref(false);

function pickFile() {
  if (processing.value) return;
  fileInput.value?.click();
}

function readAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error("读取图片失败"));
    reader.readAsDataURL(file);
  });
}

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error("无法解析该图片"));
    image.src = src;
  });
}

// 背景图直接存 localStorage，体积过大会挤占空间，所以先缩小并转成 JPEG
async function prepareImage(file) {
  if (!file.type.startsWith("image/")) {
    throw new Error("请选择图片文件");
  }
  if (file.size > 20 * 1024 * 1024) {
    throw new Error("图片不能超过 20MB");
  }

  const original = await readAsDataUrl(file);
  const image = await loadImage(original);
  const maxSide = 1920;
  const sourceSide = Math.max(image.naturalWidth, image.naturalHeight);
  const scale = Math.min(1, maxSide / sourceSide);

  // 小图不压缩，保留原始格式和清晰度
  if (scale === 1 && file.size <= 1.5 * 1024 * 1024) {
    return original;
  }

  const width = Math.max(1, Math.round(image.naturalWidth * scale));
  const height = Math.max(1, Math.round(image.naturalHeight * scale));
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;

  const context = canvas.getContext("2d");
  if (!context) throw new Error("当前浏览器不支持图片压缩");

  // JPEG 不支持透明，先铺一层白底，避免 PNG 透明区变黑
  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, width, height);
  context.drawImage(image, 0, 0, width, height);

  return canvas.toDataURL("image/jpeg", 0.86);
}

async function handleFileChange(event) {
  const file = event.target.files?.[0];
  // 允许重复选择同一个文件
  event.target.value = "";
  if (!file) return;

  processing.value = true;
  try {
    const dataUrl = await prepareImage(file);
    appearanceStore.setBackgroundImage(dataUrl, file.name);
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    processing.value = false;
  }
}

function handleReset() {
  appearanceStore.reset();
  ElMessage.success("已恢复默认外观");
}
</script>

<style scoped>
.appearance-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.storage-alert {
  margin-bottom: 12px;
}

.setting-section {
  padding: 4px 0;
}

.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.section-desc {
  margin: 6px 0 14px;
  font-size: 12px;
  line-height: 1.6;
  color: #6b7280;
}

.value-badge {
  min-width: 46px;
  padding: 2px 8px;
  font-size: 12px;
  color: var(--el-color-primary);
  text-align: center;
  background: var(--el-color-primary-light-9);
  border-radius: 999px;
}

.mode-group {
  width: 100%;
}

.mode-group :deep(.el-radio-button) {
  flex: 1;
}

.mode-group :deep(.el-radio-button__inner) {
  width: 100%;
}

.color-block,
.image-block {
  margin-top: 14px;
}

.color-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.color-row code {
  font-size: 12px;
  color: #4b5563;
}

.color-presets {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
}

.color-swatch {
  width: 30px;
  height: 30px;
  padding: 0;
  cursor: pointer;
  border: 1px solid rgba(17, 24, 39, 0.12);
  border-radius: 8px;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.color-swatch:hover {
  transform: translateY(-1px);
}

.color-swatch.active {
  box-shadow: 0 0 0 2px #fff, 0 0 0 4px var(--el-color-primary);
}

.hidden-input {
  display: none;
}

.image-preview,
.image-picker {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 150px;
  overflow: hidden;
  background-position: center;
  background-size: cover;
  border-radius: 10px;
}

.image-preview {
  position: relative;
  border: 1px solid var(--app-border);
}

.preview-tag {
  position: absolute;
  right: 10px;
  bottom: 10px;
  padding: 2px 8px;
  font-size: 11px;
  color: #fff;
  background: rgba(17, 24, 39, 0.6);
  border-radius: 999px;
}

.image-picker {
  flex-direction: column;
  gap: 8px;
  font-size: 13px;
  color: #6b7280;
  cursor: pointer;
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  transition: border-color 0.15s ease, color 0.15s ease;
}

.image-picker:hover:not(:disabled) {
  color: var(--el-color-primary);
  border-color: var(--el-color-primary);
}

.image-picker:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.image-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.file-name {
  margin: 8px 0 0;
  overflow: hidden;
  font-size: 12px;
  color: #4b5563;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hint {
  margin: 6px 0 0;
  font-size: 12px;
  line-height: 1.6;
  color: #9ca3af;
}

.slider-scale {
  display: flex;
  justify-content: space-between;
  margin-top: -4px;
  font-size: 11px;
  color: #9ca3af;
}

.quick-values {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.reset-button {
  width: 100%;
}
</style>
