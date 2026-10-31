// 扰动参数配置的共享状态（Pinia store）
//
// ── 为什么必须放进 store ────────────────────────────────────────────────
// 工作台（DashboardView）和扰动配置页（PerturbationConfigView）要显示同一组开关。
// 如果各自用 ref 保存，两边的状态互不相干；放进 Pinia 后，两边读写同一份数据，
// 在工作台拨动开关，配置页立刻同步，反之亦然。
//
// ── 数据结构 ────────────────────────────────────────────────────────────
//   configs[projectId] = { enable_brightness, enable_contrast, enable_noise, ... }
// 一个项目一份配置，切换项目不会互相覆盖。
//
// ── 数据流 ──────────────────────────────────────────────────────────────
//   后端 GET /perturbations/{id} → loadConfig() → setConfig() → configs[projectId]
//   用户拨动开关 → setEnabled()（本地立即生效）→ saveConfig() → 后端 PUT
//   保存成功后用后端返回值再覆盖一次，保证和数据库完全一致（含 updated_at）。
import { computed, reactive, ref } from "vue";
import { defineStore } from "pinia";

import {
  getPerturbationConfig,
  updatePerturbationConfig,
} from "@/api/perturbation";
import { useWorkspaceStore } from "@/store/workspace";

// 开关定义统一放在这里，工作台和配置页共用，避免两边文字或字段名不一致。
// 新增扰动类型时：① 这里加一项 ② DEFAULT_PERTURBATION_CONFIG 加同名字段
// ③ 后端 models/perturbation.py 加同名列（表结构要重建）
export const PERTURBATION_OPTIONS = [
  {
    key: "enable_brightness",
    label: "亮度扰动",
    description: "模拟曝光不足或过曝，改变图像整体亮度",
  },
  {
    key: "enable_contrast",
    label: "对比度扰动",
    description: "模拟设备成像差异，拉伸或压缩图像对比度",
  },
  {
    key: "enable_noise",
    label: "高斯噪声",
    description: "模拟传感器噪声，在图像上叠加高斯随机噪声",
  },
];

// 前端兜底默认值。正常情况下第一次 loadConfig 就会用后端返回的配置覆盖它。
// Object.freeze：防止某个组件误改这个"全局默认值"。
export const DEFAULT_PERTURBATION_CONFIG = Object.freeze({
  enable_brightness: false,
  enable_contrast: false,
  enable_noise: false,
});

// 没有选中项目时用于渲染的只读兜底对象。
// 单独复制一份是为了语义清晰：默认值可以改，空配置是"没有数据"时的只读占位。
const EMPTY_CONFIG = Object.freeze({ ...DEFAULT_PERTURBATION_CONFIG });

export const usePerturbationStore = defineStore("perturbation", () => {
  // 当前项目来自 workspace，模型选择页、扰动配置页、工作台共用同一个项目上下文
  const workspace = useWorkspaceStore();

  // readonly：组件只能通过 setActiveProject 改项目，避免各处直接赋值导致不同步
  const activeProjectId = computed(() => workspace.activeProjectId);

  // projectId -> 配置对象。
  // 用 reactive 而不是 ref：v-model 会直接改 configs[key].xxx，
  // reactive 能追踪对象属性的增删改，两个页面都会自动重新渲染。
  const configs = reactive({});

  // 已从后端加载过配置的项目 id。工作台刷新时用来跳过重复请求；
  // 目前即使重复请求也不会有副作用（GET 是幂等的），保留它方便以后优化。
  const loadedProjectId = ref(null);

  // 请求序号：防止"快速切换项目"时，先发的请求后返回，把新项目的数据覆盖掉。
  // 每次请求自增，回来时序号不一致就丢弃结果。
  let requestSeq = 0;

  // 确保 configs 里有这个项目的对象，没有就建一个默认的。
  // 写操作（拨开关、保存）调用它；只在读取路径上不调用，见下面的 getConfig。
  function ensureConfig(projectId) {
    // 统一把 null / undefined / "" 都当作"没有项目"
    if (projectId === null || projectId === undefined || projectId === "") {
      return null;
    }
    // 对象的 key 永远是字符串，所以数字 id 要转成 String 再存
    const key = String(projectId);
    if (!configs[key]) {
      // 展开复制，避免多个项目共享同一个对象引用
      configs[key] = { ...DEFAULT_PERTURBATION_CONFIG };
    }
    return configs[key];
  }

  // 只读获取，不创建新 key。
  // 注意：不要在模板 / computed 里调用 ensureConfig——渲染过程中修改响应式状态
  // 会触发额外的更新，甚至造成循环渲染。渲染只读，交互才写。
  function getConfig(projectId) {
    if (projectId === null || projectId === undefined || projectId === "") {
      return EMPTY_CONFIG;
    }
    return configs[String(projectId)] || EMPTY_CONFIG;
  }

  // 切换当前项目：workspace 是唯一的数据源，这里顺带初始化配置对象
  function setActiveProject(projectId) {
    workspace.setActiveProject(projectId);
    ensureConfig(workspace.activeProjectId);
  }

  // 读取某个开关，供工作台的 :model-value 使用
  function isEnabled(projectId, key) {
    return Boolean(getConfig(projectId)[key]);
  }

  // 本地修改一个开关（不请求后端）。
  // 工作台的 el-switch 用 model-value + update 事件绑定到它；
  // 配置页的开关则是直接 v-model 到 config 对象上，效果相同。
  function setEnabled(projectId, key, value) {
    const config = ensureConfig(projectId);
    if (!config) return;
    config[key] = Boolean(value);
  }

  // 用后端返回的完整配置整体覆盖本地状态。
  // Object.assign 的第二个参数是默认值：后端以后少返回某个字段时，
  // 本地也不会出现 undefined，开关会退回 false 而不是显示异常。
  function setConfig(projectId, config) {
    const target = ensureConfig(projectId);
    if (!target || !config) return;
    Object.assign(target, DEFAULT_PERTURBATION_CONFIG, config);
  }

  // 恢复默认开关（只改本地，点「保存配置」后才写库）
  function resetConfig(projectId) {
    const target = ensureConfig(projectId);
    if (!target) return;
    Object.assign(target, DEFAULT_PERTURBATION_CONFIG);
  }

  // 从后端读取配置。后端 GET 会在项目第一次访问时自动创建默认配置，
  // 所以这里不需要先判断"有没有配置"。
  // 失败时异常向上抛，由调用方决定是提示用户还是静默（工作台选择静默）。
  async function loadConfig(projectId = workspace.activeProjectId) {
    if (!projectId) {
      loadedProjectId.value = null;
      return null;
    }

    const seq = ++requestSeq;
    const data = await getPerturbationConfig(projectId);

    // 请求期间又切换了项目：丢弃这次结果，返回当前项目已有的本地配置
    if (seq !== requestSeq) return getConfig(projectId);

    setConfig(projectId, data);
    loadedProjectId.value = projectId;
    return data;
  }

  // 保存当前项目的开关。
  // 只提交这几个字段：后端用 exclude_unset 处理，没传的字段保持原值。
  // params / strength 目前是预留列，前端不做修改，但要把读到的值原样带回去，
  // 避免以后后端把"缺省"理解成"清空"。
  async function saveConfig(projectId = workspace.activeProjectId) {
    if (!projectId) return null;

    const {
      enable_brightness,
      enable_contrast,
      enable_noise,
      params,
      strength,
    } = getConfig(projectId);

    const data = await updatePerturbationConfig(projectId, {
      enable_brightness,
      enable_contrast,
      enable_noise,
      params,
      strength,
    });
    // 用后端返回值覆盖本地：这样 updated_at 等字段和数据库完全一致
    setConfig(projectId, data);
    loadedProjectId.value = projectId;
    return data;
  }

  // 暴露给组件的 API。只导出需要用的，内部函数（ensureConfig）不暴露，
  // 避免组件绕过"渲染只读"的约定。
  return {
    activeProjectId,
    configs,
    loadedProjectId,
    getConfig,
    setActiveProject,
    isEnabled,
    setEnabled,
    setConfig,
    resetConfig,
    loadConfig,
    saveConfig,
  };
});
