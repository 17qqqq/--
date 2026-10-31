# 模型选择相关的请求 / 响应结构
#
# 命名规则（全项目统一）：
#   类名 = ORM 模型类名 + 动作（Create / Update / Detail）
#   所以这里用 MLModel*，与 app/models/ml_model.py 的 MLModel 对应；
#   接口路径仍然叫 /models，前端也只关心字段，不关心类名。
#
# 其他约定：
# - Create 只包含客户端能提交的字段
# - Detail 用于接口返回，包含 id、is_active、时间戳等只读字段
# - 不直接返回 ORM 对象，统一在 router 里用 model_validate 转换
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MLModelCreate(BaseModel):
    project_id: int = Field(..., ge=1)
    name: str = Field(..., min_length=1, max_length=100)
    version: str = Field("", max_length=50)
    framework: str = Field("pytorch", max_length=20)
    # 文件路径由后端校验；如果以后做上传接口，这里会由上传结果自动填入
    file_path: str = Field("", max_length=500)
    description: str = Field("", max_length=500)


class MLModelDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    version: str
    framework: str
    file_path: str
    description: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
