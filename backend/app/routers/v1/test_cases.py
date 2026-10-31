# 测试用例接口
#
# 路由层只做参数解析和响应包装，业务规则在
# app/services/test_case_service.py。
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import PageParams, PageResult, ResponseModel
from app.schemas.test_case import TestCaseCreate, TestCaseDetail, TestCaseUpdate
from app.services.test_case_service import TestCaseService

router = APIRouter()


@router.get("", response_model=ResponseModel[PageResult[TestCaseDetail]])
def list_test_cases(
    project_id: int,
    params: PageParams = Depends(),
    enabled: bool | None = None,
    db: Session = Depends(get_db),
):
    """分页查询某个项目下的测试用例。

    enabled 可不传：不传返回全部；传 true/false 只看启用/停用的用例。
    计划页选用例时传 true，天然过滤掉停用样本。
    """
    total, items = TestCaseService(db).list(project_id, params, enabled)
    return ResponseModel(
        data=PageResult[TestCaseDetail](
            total=total,
            items=[TestCaseDetail.model_validate(item) for item in items],
        )
    )


@router.post("", response_model=ResponseModel[TestCaseDetail])
def create_test_case(payload: TestCaseCreate, db: Session = Depends(get_db)):
    """新增测试用例（只登记路径，不上传文件）。"""
    obj = TestCaseService(db).create(payload)
    return ResponseModel(data=TestCaseDetail.model_validate(obj))


@router.get("/{case_id}", response_model=ResponseModel[TestCaseDetail])
def get_test_case(
    case_id: int,
    project_id: int,
    db: Session = Depends(get_db),
):
    """查询单个用例。project_id 用于校验归属，避免跨项目访问。"""
    obj = TestCaseService(db).get(project_id, case_id)
    return ResponseModel(data=TestCaseDetail.model_validate(obj))


@router.put("/{case_id}", response_model=ResponseModel[TestCaseDetail])
def update_test_case(
    case_id: int,
    project_id: int,
    payload: TestCaseUpdate,
    db: Session = Depends(get_db),
):
    """局部更新用例；只改请求体里出现过的字段。"""
    obj = TestCaseService(db).update(project_id, case_id, payload)
    return ResponseModel(data=TestCaseDetail.model_validate(obj))


@router.delete("/{case_id}", response_model=ResponseModel[None])
def delete_test_case(
    case_id: int,
    project_id: int,
    db: Session = Depends(get_db),
):
    """删除用例；计划里的关联行由数据库外键级联清理。"""
    TestCaseService(db).delete(project_id, case_id)
    return ResponseModel(data=None)
