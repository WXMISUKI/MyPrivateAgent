"""Request-scoped middleware: request ID injection and unified error handling."""

from __future__ import annotations

import contextvars
import uuid
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

_request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)

REQUEST_ID_HEADER = "X-Request-ID"


def get_request_id() -> Optional[str]:
    return _request_id_var.get()


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming_id = request.headers.get(REQUEST_ID_HEADER)
        request_id = incoming_id or uuid.uuid4().hex
        token = _request_id_var.set(request_id)
        try:
            response = await call_next(request)
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            _request_id_var.reset(token)


import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request as StarletteRequest

_middleware_logger = logging.getLogger(__name__)


def _error_body(code: str, message: str, status: int, details: object = None) -> dict:
    body = {
        "error": {
            "code": code,
            "message": message,
            "status": status,
            "request_id": get_request_id() or "-",
        }
    }
    if details is not None:
        body["error"]["details"] = details
    return body


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: StarletteRequest, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=_error_body("VALIDATION_ERROR", "请求参数校验失败", 422, exc.errors()),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: StarletteRequest, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body("HTTP_ERROR", str(exc.detail), exc.status_code),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: StarletteRequest, exc: Exception):
        _middleware_logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content=_error_body("INTERNAL_ERROR", "服务器内部错误", 500),
        )
