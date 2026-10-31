# 初始化：建表、插入种子数据（管理员、默认环境）
from sqlalchemy import func, select

from app.db.base import Base
from app.db.session import SessionLocal, engine
import app.models  # noqa: F401  确保所有模型注册到 Base.metadata
from app.models.user import User


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if not db.scalar(select(func.count()).select_from(User)):
            db.add(User(username="admin", email="admin@example.com"))
            db.commit()