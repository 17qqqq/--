# 测试用例的请求 / 响应结构
#
# 命名规则同其他模块：类名 = ORM 类名 + 动作（Create / Update / Detail）。
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TestCaseCreate(BaseModel):
    project_id: int = Field(..., ge=1)
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=500)
    image_path: str = Field("", max_length=500)
    mask_path: str = Field("", max_length=500)
    enabled: bool = True


class TestCaseUpdate(BaseModel):
    """局部更新：只改请求体里出现过的字段。"""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    image_path: str | None = Field(None, max_length=500)
    mask_path: str | None = Field(None, max_length=500)
    enabled: bool | None = None


class TestCaseBrief(BaseModel):
    """计划详情里展示用例时只带必要字段，避免响应过大。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class TestCaseDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    description: str
    image_path: str
    mask_path: str
    enabled: bool
    created_at: datetime
    updated_at: datetime
