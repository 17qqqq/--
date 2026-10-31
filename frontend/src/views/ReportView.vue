<!--当前为测试报告的界面代码 -->
<template>
  <ComingSoon
    title="测试报告"
    description="汇总执行结果，生成并导出测试报告"
    empty-text="测试报告页面待开发"
    backend-hint="app/models/report.py 与 app/schemas/report.py 已有占位，app/services/report_service.py 为空，后端还没有 reports 路由。"
    :steps="steps"
  />
</template>

<script setup>
import ComingSoon from "@/components/ComingSoon.vue";

const steps = [
  "在 app/models/report.py 中实现 Report、ReportSnapshot 模型",
  "补全 app/schemas/report.py 的报告结构与导出参数",
  "实现 app/services/report_service.py（聚合执行数据、生成报告内容）",
  "新建 app/routers/v1/reports.py 并注册路由，提供生成/查询/导出接口",
  "新建 src/api/report.js，把本页替换成报告列表与预览页面",
];
</script>
