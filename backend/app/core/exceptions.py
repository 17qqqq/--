# 业务异常类 + 全局异常处理器（统一响应格式）
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(self, message: str = "bad request", code: int = 40000, status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code


class BadRequestError(AppException):
    def __init__(self, message: str = "bad request"):
        super().__init__(message=message, code=40000, status_code=400)


class NotFoundError(AppException):
    def __init__(self, message: str = "resource not found"):
        super().__init__(message=message, code=40400, status_code=404)


class NotImplementedYetError(AppException):
    """功能接口已定义、但具体实现还没接入时使用（HTTP 501）。

    典型场景：报告生成依赖推理/扰动/指标实现，这些模块由其他成员提供。
    返回 501 而不是 500，前端能区分"代码出错"和"尚未接入"。
    """

    def __init__(self, message: str = "该功能尚未接入实现"):
        super().__init__(message=message, code=50100, status_code=501)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def _app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message, "data": None},
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_exception_handler(request: Request, exc: RequestValidationError):
        # 只保留可 JSON 序列化的字段，避免 ctx 中的异常对象导致序列化失败
        errors = [
            {
                "loc": list(err.get("loc", ())),
                "msg": err.get("msg", ""),
                "type": err.get("type", ""),
            }
            for err in exc.errors()
        ]
        if errors:
            first = errors[0]
            message = f"参数校验失败：{'.'.join(map(str, first['loc']))} {first['msg']}"
        else:
            message = "参数校验失败"
        return JSONResponse(
            status_code=422,
            content={"code": 42200, "message": message, "data": {"errors": errors}},
        )