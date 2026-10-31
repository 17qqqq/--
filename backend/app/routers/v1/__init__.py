# v1 版本路由汇总
#
# 每个业务模块一个 router 文件，在这里统一 include，
# main.py 只需要挂一次 api_router。
#
# prefix 统一用资源复数；多词资源用连字符（/test-cases）。
# 前端 api/*.js 里的路径必须和这里保持一致。
from fastapi import APIRouter

from app.routers.v1 import (
    models,
    perturbations,
    ping,
    projects,
    reports,
    test_cases,
    test_plans,
)

api_router = APIRouter()
api_router.include_router(ping.router, tags=["system"])
api_router.include_router(projects.router, prefix="/projects", tags=["项目"])
api_router.include_router(models.router, prefix="/models", tags=["模型选择"])
api_router.include_router(
    perturbations.router, prefix="/perturbations", tags=["扰动参数"]
)
api_router.include_router(
    test_cases.router, prefix="/test-cases", tags=["测试用例"]
)
api_router.include_router(
    test_plans.router, prefix="/test-plans", tags=["测试计划"]
)
api_router.include_router(reports.router, prefix="/reports", tags=["测试报告"])
