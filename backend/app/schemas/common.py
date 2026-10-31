# 通用模型：分页参数、分页响应、统一响应体、ID 列表
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageParams(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)


class PageResult(BaseModel, Generic[T]):
    total: int
    items: list[T]


class ResponseModel(BaseModel, Generic[T]):
    code: int = 0
    message: str = "ok"
    data: Optional[T] = None