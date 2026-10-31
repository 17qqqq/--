# 模型选择的业务逻辑层
#
# 约定：
# - 一个项目可以登记多个模型，但同一时间只能有一个 is_active=True
# - 项目 / 模型不存在时统一抛 NotFoundError，避免接口返回 500
# - 切换启用模型放在同一个事务里提交
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.project import Project
from app.repositories.model_repo import ModelRepository
from app.schemas.common import PageParams
from app.schemas.model import MLModelCreate


class ModelService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ModelRepository(db)

    def _get_project(self, project_id: int) -> Project:
        project = self.db.get(Project, project_id)
        if not project:
            raise NotFoundError("项目不存在")
        return project

    def list_by_project(self, project_id: int, params: PageParams):
        self._get_project(project_id)
        offset = (params.page - 1) * params.size
        return self.repo.list_by_project(
            project_id=project_id,
            offset=offset,
            limit=params.size,
        )

    def create(self, payload: MLModelCreate):
        self._get_project(payload.project_id)

        data = payload.model_dump()
        # 项目还没有启用模型时，新建的第一个模型自动启用，
        # 避免用户登记完模型后还要多点一次“启用”。
        if self.repo.get_active(payload.project_id) is None:
            data["is_active"] = True

        obj = self.repo.create(**data)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def activate(self, project_id: int, model_id: int):
        self._get_project(project_id)

        model = self.repo.get_by_project(project_id, model_id)
        if not model:
            raise NotFoundError("模型不存在或不属于该项目")

        # 先取消旧模型，再启用目标模型，最后一次性提交
        self.repo.clear_active(project_id)
        model.is_active = True
        self.db.commit()
        self.db.refresh(model)
        return model

    def get_active(self, project_id: int):
        self._get_project(project_id)
        return self.repo.get_active(project_id)
