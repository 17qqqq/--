from typing import Generic, Optional, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, obj_id: int) -> Optional[ModelType]:
        return self.db.get(self.model, obj_id)

    def paginate(
        self,
        offset: int = 0,
        limit: int = 20,
        *,
        condition=None,
        order_by=None,
    ) -> tuple[int, list[ModelType]]:
        """按条件分页查询，返回 (总数, 当前页数据)。

        condition 是 SQLAlchemy 过滤表达式，例如 TestCase.project_id == 1；
        order_by 是排序表达式，不传则按主键升序。
        子类的 list_by_project 只需传条件，不用重写 count + select。
        """
        count_stmt = select(func.count()).select_from(self.model)
        page_stmt = select(self.model)
        if condition is not None:
            count_stmt = count_stmt.where(condition)
            page_stmt = page_stmt.where(condition)

        total = self.db.scalar(count_stmt) or 0
        items = self.db.scalars(
            page_stmt.order_by(order_by if order_by is not None else self.model.id)
            .offset(offset)
            .limit(limit)
        ).all()
        return total, list(items)

    def list(self, offset: int = 0, limit: int = 20) -> tuple[int, list[ModelType]]:
        return self.paginate(offset, limit)

    def create(self, **kwargs) -> ModelType:
        obj = self.model(**kwargs)
        self.db.add(obj)
        self.db.flush()
        return obj

    def update(self, obj: ModelType, **kwargs) -> ModelType:
        for k, v in kwargs.items():
            setattr(obj, k, v)
        self.db.flush()
        return obj

    def delete(self, obj: ModelType) -> None:
        self.db.delete(obj)
        self.db.flush()