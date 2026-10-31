<!--当前为执行记录页面的界面代码 -->
<template>
  <ComingSoon
    title="执行记录"
    description="查看测试计划的执行结果与日志"
    empty-text="执行记录页面待开发"
    backend-hint="执行链路属于算法/执行模块，本仓库暂不实现；接入契约见 backend/docs/接入说明.md 与 app/interfaces/。"
    :steps="steps"
  />
</template>

<script setup>
import ComingSoon from "@/components/ComingSoon.vue";

const steps = [
  "新建 app/models/test_run.py，定义 TestRun、RunResult、RunLog 等表",
  "新建 app/schemas/test_run.py，定义执行请求与结果模型",
  "新建 app/services/test_run_service.py（触发执行、写入结果、查询状态）",
  "新建 app/routers/v1/test_runs.py，并注册到 app/routers/v1/__init__.py",
  "执行时按名字调用 app/interfaces/ 下的推理、扰动、指标实现",
  "新建 src/api/testRun.js，把本页替换成执行列表、状态筛选和日志抽屉",
];
</script>
