// 外观设置：页面背景 + 内容区小窗口透明度
// 设置保存在 localStorage，刷新页面或重启前端后仍然保留。
import { computed, ref, watch } from "vue";
import { defineStore } from "pinia";

const STORAGE_KEY = "vasorat-appearance";

// 预设背景色都偏浅，避免页面标题在深色背景上不易阅读
export const BACKGROUND_PRESETS = [
  "#f5f7fa",
  "#eef2ff",
  "#e0f2fe",
  "#ecfdf5",
  "#fefce8",
  "#fff1f2",
  "#faf5ff",
  "#f1f5f9",
];

export const DEFAULT_APPEARANCE = {
  // default：使用主题默认底色；color：纯色；image：自定义图片
  backgroundMode: "default",
  backgroundColor: "#eef2ff",
  backgroundImage: "",
  backgroundImageName: "",
  // 0 表示卡片完全不透明，100 表示卡片背景完全透明
  cardTransparency: 0,
};

function loadAppearance() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...DEFAULT_APPEARANCE };

    const saved = JSON.parse(raw);
    return {
      ...DEFAULT_APPEARANCE,
      ...saved,
      cardTransparency: Math.min(
        100,
        Math.max(0, Number(saved.cardTransparency) || 0),
      ),
    };
  } catch {
    // localStorage 被禁用或内容损坏时，静默使用默认外观
    return { ...DEFAULT_APPEARANCE };
  }
}

export const useAppearanceStore = defineStore("appearance", () => {
  const saved = loadAppearance();

  const backgroundMode = ref(saved.backgroundMode);
  const backgroundColor = ref(saved.backgroundColor);
  const backgroundImage = ref(saved.backgroundImage);
  const backgroundImageName = ref(saved.backgroundImageName);
  const cardTransparency = ref(saved.cardTransparency);
  const storageError = ref("");

  // CSS 中直接使用 rgba(255, 255, 255, var(--app-card-opacity))
  const cardOpacity = computed(
    () => 1 - Math.min(100, Math.max(0, cardTransparency.value)) / 100,
  );

  // 背景层样式。图片铺满右侧区域，不使用 fixed，切换页面时不会重新闪动
  const backgroundStyle = computed(() => {
    if (backgroundMode.value === "image" && backgroundImage.value) {
      return {
        backgroundImage: `url("${backgroundImage.value}")`,
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
      };
    }

    if (backgroundMode.value === "color") {
      return { background: backgroundColor.value };
    }

    return { background: "var(--app-bg)" };
  });

  function setBackgroundImage(dataUrl, fileName = "") {
    backgroundImage.value = dataUrl;
    backgroundImageName.value = fileName;
    backgroundMode.value = "image";
  }

  function removeBackgroundImage() {
    backgroundImage.value = "";
    backgroundImageName.value = "";
    if (backgroundMode.value === "image") {
      backgroundMode.value = "default";
    }
  }

  function reset() {
    backgroundMode.value = DEFAULT_APPEARANCE.backgroundMode;
    backgroundColor.value = DEFAULT_APPEARANCE.backgroundColor;
    backgroundImage.value = DEFAULT_APPEARANCE.backgroundImage;
    backgroundImageName.value = DEFAULT_APPEARANCE.backgroundImageName;
    cardTransparency.value = DEFAULT_APPEARANCE.cardTransparency;
    storageError.value = "";
    localStorage.removeItem(STORAGE_KEY);
  }

  // 拖动透明度滑块时会连续触发，延迟写入避免频繁序列化较大的背景图
  let saveTimer = null;

  function persist() {
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          backgroundMode: backgroundMode.value,
          backgroundColor: backgroundColor.value,
          backgroundImage: backgroundImage.value,
          backgroundImageName: backgroundImageName.value,
          cardTransparency: cardTransparency.value,
        }),
      );
      storageError.value = "";
    } catch {
      storageError.value =
        "外观设置保存失败：图片可能过大，浏览器本地存储空间不足。当前设置仅在本次页面中生效。";
    }
  }

  watch(
    [
      backgroundMode,
      backgroundColor,
      backgroundImage,
      backgroundImageName,
      cardTransparency,
    ],
    () => {
      window.clearTimeout(saveTimer);
      saveTimer = window.setTimeout(persist, 200);
    },
  );

  return {
    backgroundMode,
    backgroundColor,
    backgroundImage,
    backgroundImageName,
    cardTransparency,
    cardOpacity,
    backgroundStyle,
    storageError,
    setBackgroundImage,
    removeBackgroundImage,
    reset,
  };
});
