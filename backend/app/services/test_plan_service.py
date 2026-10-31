# 测试计划的业务逻辑
#
# 计划本身只做"编排"：选模型、选用例、快照扰动配置。
# 真正的执行（跑图、施加扰动、推理、算指标）由执行模块通过
# app/interfaces 里的接口接入，不在本模块实现。
#
# 类里有名为 list 的方法，会遮蔽内置 list，因此开启延迟注解。
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.ml_model import MLModel
from app.models.project import Project
from app.repositories.test_case_repo import TestCaseRepository
from app.repositories.test_plan_repo import TestPlanRepository
from app.schemas.common import PageParams
from app.schemas.test_plan import TestPlanCreate, TestPlanUpdate
from app.services.perturbation_service import PerturbationService


class TestPlanService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TestPlanRepository(db)
        self.case_repo = TestCaseRepository(db)

    # ── 校验工具 ────────────────────────────────────────────────────────
    def _ensure_project(self, project_id: int) -> None:
        if not self.db.get(Project, project_id):
            raise NotFoundError("项目不存在")

    def _ensure_model(self, project_id: int, model_id: int | None) -> None:
        """模型可以为空；不为空时必须属于当前项目。"""
        if model_id is None:
            return
        model = self.db.get(MLModel, model_id)
        if not model or model.project_id != project_id:
            raise BadRequestError("模型不存在或不属于该项目")

    def _resolve_cases(self, project_id: int, case_ids: list[int]):
        """把 id 列表换成用例对象，并校验它们都属于当前项目。

        去重后再查，避免前端重复勾选导致关联表主键冲突；
        数量对不上说明有非法 id，直接拒绝。
        """
        unique_ids = list(dict.fromkeys(case_ids))  # 保序去重
        if not unique_ids:
            return []

        cases = self.case_repo.list_by_ids(project_id, unique_ids)
        if len(cases) != len(unique_ids):
            raise BadRequestError("存在不属于该项目的测试用例")
        # 按请求顺序返回，保证计划里用例顺序稳定
        case_map = {case.id: case for case in cases}
        return [case_map[case_id] for case_id in unique_ids]

    def _build_snapshot(self, project_id: int) -> dict:
        """把当前扰动配置复制一份存进计划。

        之后用户修改项目的扰动开关，不会影响已经建好的计划——
        历史计划应该按"创建时的配置"执行，这样报告才可复现。
        """
        config = PerturbationService(self.db).get_or_create(project_id)
        return {
            "enable_brightness": config.enable_brightness,
            "enable_contrast": config.enable_contrast,
            "enable_noise": config.enable_noise,
            "params": config.params,
            "strength": config.strength,
        }

    # ── 增删改查 ────────────────────────────────────────────────────────
    def create(self, payload: TestPlanCreate):
        self._ensure_project(payload.project_id)
        self._ensure_model(payload.project_id, payload.model_id)

        data = payload.model_dump(exclude={"case_ids"})
        obj = self.repo.create(
            **data,
            perturbation_snapshot=self._build_snapshot(payload.project_id),
        )
        obj.cases = self._resolve_cases(payload.project_id, payload.case_ids)

        self.db.commit()
        self.db.refresh(obj)
        return obj

    def list(self, project_id: int, params: PageParams):
        self._ensure_project(project_id)
        offset = (params.page - 1) * params.size
        return self.repo.list_by_project(project_id, offset=offset, limit=params.size)

    def get(self, project_id: int, plan_id: int):
        self._ensure_project(project_id)
        obj = self.repo.get_by_project(project_id, plan_id)
        if not obj:
            raise NotFoundError("测试计划不存在")
        return obj

    def update(self, project_id: int, plan_id: int, payload: TestPlanUpdate):
        obj = self.get(project_id, plan_id)

        data = payload.model_dump(exclude_unset=True)
        # case_ids 不是数据库列，需要单独处理关联关系
        case_ids = data.pop("case_ids", None)

        if "model_id" in data:
            self._ensure_model(project_id, data["model_id"])

        for key, value in data.items():
            setattr(obj, key, value)

        # 传 [] 表示清空；没传（None）表示不动
        if case_ids is not None:
            obj.cases = self._resolve_cases(project_id, case_ids)

        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, project_id: int, plan_id: int) -> None:
        obj = self.get(project_id, plan_id)
        self.repo.delete(obj)
        self.db.commit()
