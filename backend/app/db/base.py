# 声明式 Base，导入所有 model 供 Alembic autogenerate 使用
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。模型注册由 init_db / alembic env 负责导入。"""