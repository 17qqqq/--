from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import PageParams, PageResult, ResponseModel
from app.schemas.project import ProjectCreate, ProjectDetail
from app.services.project_service import ProjectService

router = APIRouter()


@router.post("", response_model=ResponseModel[ProjectDetail])
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    obj = ProjectService(db).create(payload)
    return ResponseModel(data=ProjectDetail.model_validate(obj))


@router.get("", response_model=ResponseModel[PageResult[ProjectDetail]])
def list_projects(params: PageParams = Depends(), db: Session = Depends(get_db)):
    total, items = ProjectService(db).list(params)
    return ResponseModel(
        data=PageResult[ProjectDetail](
            total=total,
            items=[ProjectDetail.model_validate(i) for i in items],
        )
    )


@router.get("/{project_id}", response_model=ResponseModel[ProjectDetail])
def get_project(project_id: int, db: Session = Depends(get_db)):
    obj = ProjectService(db).get(project_id)
    return ResponseModel(data=ProjectDetail.model_validate(obj))


@router.delete("/{project_id}", response_model=ResponseModel[None])
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """删除项目，并级联清理它名下的模型、用例、计划、报告和扰动配置。"""
    ProjectService(db).delete(project_id)
    return ResponseModel(data=None)