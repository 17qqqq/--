# 测试计划接口
#
# 计划 = 项目 + 模型 + 用例集合 + 扰动配置快照。
# 创建/更新时由 service 校验归属并写快照；执行由其他模块接入，
# 本路由不涉及推理。
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import PageParams, PageResult, ResponseModel
from app.schemas.test_plan import TestPlanCreate, TestPlanDetail, TestPlanUpdate
from app.services.test_plan_service import TestPlanService

router = APIRouter()


@router.get("", response_model=ResponseModel[PageResult[TestPlanDetail]])
def list_test_plans(
    project_id: int,
    params: PageParams = Depends(),
    db: Session = Depends(get_db),
):
    """分页查询某个项目下的测试计划（按创建时间倒序）。"""
    total, items = TestPlanService(db).list(project_id, params)
    return ResponseModel(
        data=PageResult[TestPlanDetail](
            total=total,
            items=[TestPlanDetail.model_validate(item) for item in items],
        )
    )


@router.post("", response_model=ResponseModel[TestPlanDetail])
def create_test_plan(payload: TestPlanCreate, db: Session = Depends(get_db)):
    """创建计划：自动快照当前扰动配置，并按 case_ids 建立关联。"""
    obj = TestPlanService(db).create(payload)
    return ResponseModel(data=TestPlanDetail.model_validate(obj))


@router.get("/{plan_id}", response_model=ResponseModel[TestPlanDetail])
def get_test_plan(
    plan_id: int,
    project_id: int,
    db: Session = Depends(get_db),
):
    """查询单个计划，包含关联用例列表。"""
    obj = TestPlanService(db).get(project_id, plan_id)
    return ResponseModel(data=TestPlanDetail.model_validate(obj))


@router.put("/{plan_id}", response_model=ResponseModel[TestPlanDetail])
def update_test_plan(
    plan_id: int,
    project_id: int,
    payload: TestPlanUpdate,
    db: Session = Depends(get_db),
):
    """局部更新计划。

    - 修改开关/状态：传 status
    - 重新选用例：传 case_ids（[] 表示清空，不传表示不变）
    - 注意：不会重新快照扰动配置，历史计划保持创建时的配置
    """
    obj = TestPlanService(db).update(project_id, plan_id, payload)
    return ResponseModel(data=TestPlanDetail.model_validate(obj))


@router.delete("/{plan_id}", response_model=ResponseModel[None])
def delete_test_plan(
    plan_id: int,
    project_id: int,
    db: Session = Depends(get_db),
):
    """删除计划；计划-用例关联行由数据库外键级联清理。"""
    TestPlanService(db).delete(project_id, plan_id)
    return ResponseModel(data=None)
