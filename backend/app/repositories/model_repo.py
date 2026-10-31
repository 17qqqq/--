# 模型表的数据访问层
#
# 这里只写“怎么查、怎么改”，不判断“该不该启用”“项目是否存在”这类业务规则。
# 业务规则统一放在 app/services/model_service.py。
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.ml_model import MLModel
from app.repositories.base import BaseRepository


class ModelRepository(BaseRepository[MLModel]):
    def __init__(self, db: Session):
        super().__init__(MLModel, db)

    def list_by_project(
        self, project_id: int, offset: int = 0, limit: int = 20
    ) -> tuple[int, list[MLModel]]:
        return self.paginate(
            offset,
            limit,
            condition=MLModel.project_id == project_id,
        )

    def get_by_project(self, project_id: int, model_id: int) -> MLModel | None:
        # 用 project_id 一起过滤，避免 A 项目的接口操作到 B 项目的模型
        return self.db.scalar(
            select(MLModel).where(
                MLModel.id == model_id,
                MLModel.project_id == project_id,
            )
        )

    def get_active(self, project_id: int) -> MLModel | None:
        return self.db.scalar(
            select(MLModel).where(
                MLModel.project_id == project_id,
                MLModel.is_active.is_(True),
            )
        )

    def clear_active(self, project_id: int) -> None:
        # 切换启用模型前先全部置 False，再单独启用目标模型
        self.db.execute(
            update(MLModel)
            .where(MLModel.project_id == project_id, MLModel.is_active.is_(True))
            .values(is_active=False)
        )
