# -*- coding: utf-8 -*-
"""
===================================
全局异常处理中间件
===================================
"""

import logging
import traceback

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware:
    """全局异常处理中间件（純 ASGI，不繼承 BaseHTTPMiddleware）"""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        try:
            await self.app(scope, receive, send)
        except Exception as e:
            logger.error(
                f"未处理的异常: {e}\n"
                f"请求路径: {scope.get('path', '')}\n"
                f"堆栈: {traceback.format_exc()}"
            )
            response = JSONResponse(
                status_code=500,
                content={
                    "error": "internal_error",
                    "message": "服务器内部错误，请稍后重试",
                },
            )
            await response(scope, receive, send)


def add_error_handlers(app) -> None:
    """添加全局异常处理器"""
    from fastapi import HTTPException
    from fastapi.exceptions import RequestValidationError

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        if isinstance(exc.detail, dict) and "error" in exc.detail and "message" in exc.detail:
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": "http_error", "message": str(exc.detail) if exc.detail else "HTTP Error"},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"error": "validation_error", "message": "请求参数验证失败", "detail": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"未处理的异常: {exc}\n请求路径: {request.url.path}\n堆栈: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "message": "服务器内部错误"},
        )
