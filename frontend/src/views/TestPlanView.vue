<!--当前为测试计划的界面代码 -->
<template>
  <ComingSoon
    title="测试计划"
    description="编排测试计划，关联用例并安排执行"
    empty-text="测试计划页面待开发"
    backend-hint="对应后端 app/routers/v1/test_plans.py，目前为空文件；services 下也还没有 test_plan_service.py。"
    :steps="steps"
  />
</template>

<script setup>
import ComingSoon from "@/components/ComingSoon.vue";

const steps = [
  "在 app/models/test_plan.py 中实现 TestPlan、PlanCase 模型（计划与用例的多对多关系）",
  "在 app/schemas/test_plan.py 中定义请求/响应模型",
  "新建 app/services/test_plan_service.py 与对应 repository",
  "在 app/routers/v1/test_plans.py 中实现接口并注册路由",
  "新建 src/api/testPlan.js，把本页替换成计划列表、用例选择和排期表单",
];
</script>
