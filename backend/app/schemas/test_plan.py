# 测试计划的请求 / 响应结构
#
# 创建计划时可以一次提交用例 id 列表；更新时 case_ids 传了才会改关联关系。
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.test_case import TestCaseBrief

# 与 app/core/constants.py 的 PLAN_STATUSES 保持一致
PlanStatus = Literal["draft", "ready", "running", "finished"]


class TestPlanCreate(BaseModel):
    project_id: int = Field(..., ge=1)
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=500)

    # 可选：计划使用的模型；不传则执行时使用项目当前启用的模型
    model_id: int | None = Field(None, ge=1)

    # 计划包含的用例 id，必须属于同一项目
    case_ids: list[int] = Field(default_factory=list)


class TestPlanUpdate(BaseModel):
    """局部更新：只改请求体里出现过的字段。"""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    status: PlanStatus | None = None
    model_id: int | None = Field(None, ge=1)
    # 传 [] 表示清空用例；不传表示不动
    case_ids: list[int] | None = None


class TestPlanDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    description: str
    status: str
    model_id: int | None
    # 创建计划时的扰动配置快照
    perturbation_snapshot: dict | None
    cases: list[TestCaseBrief] = []
    created_at: datetime
    updated_at: datetime
