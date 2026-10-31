# 扰动参数配置的请求 / 响应模型（Pydantic v2）
#
# 一个接口通常配两个 schema：
#   XxxUpdate  —— 客户端提交上来的数据，只放允许修改的字段
#   XxxDetail  —— 返回给前端的数据，额外包含 id、时间戳等只读字段
#
# 为什么 Update 里所有字段都有默认值：
# 前端目前只提交三个开关，不会提交 params / strength。
# service 层用 model_dump(exclude_unset=True) 只取"请求体里真正出现过"的字段，
# 所以没传的字段不会被覆盖成默认值——默认值只用于通过校验，不用于写库。
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PerturbationConfigUpdate(BaseModel):
    """PUT /perturbations/{project_id} 的请求体。"""

    enable_brightness: bool = False
    enable_contrast: bool = False
    enable_noise: bool = False

    # 预留参数：前端暂时不传，保持 NULL / 100 的默认值即可。
    # dict[str, Any] | None 表示"可以是任意结构的对象，也可以是 null"。
    params: dict[str, Any] | None = None

    # Field(100, ge=0, le=100)：默认 100，且必须在 0-100 之间。
    # 越界时由 FastAPI 统一转成 422，错误信息由 core/exceptions.py 处理。
    strength: int = Field(100, ge=0, le=100)


class PerturbationConfigDetail(BaseModel):
    """GET / PUT 的响应体（放在统一响应结构 ResponseModel.data 里）。"""

    # from_attributes=True：允许用 ORM 对象直接构造，
    # 路由里写 PerturbationConfigDetail.model_validate(obj) 即可，
    # 不需要手工把每个字段抄一遍。
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    enable_brightness: bool
    enable_contrast: bool
    enable_noise: bool

    # 数据库里是 NULL，序列化到 JSON 就是 null；
    # 前端 store 的 setConfig 会把它一起存进配置对象。
    params: dict[str, Any] | None = None
    strength: int

    created_at: datetime
    updated_at: datetime

    # 注意：没有暴露 is_deleted 之类的内部字段——Detail 只放前端需要的列。
    # 以后加敏感字段（如内部路径）时，也不要直接加到这里。
