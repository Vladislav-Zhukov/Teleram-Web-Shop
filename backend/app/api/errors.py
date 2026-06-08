from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import ORJSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


ERROR_MESSAGES = {
    "AUTH_REQUIRED": "Требуется авторизация",
    "FORBIDDEN": "Недостаточно прав",
    "BAD_STATUS_TRANSITION": "Переход запрещён правилами жизненного цикла заказа",
    "BAD_STATUS": "Неизвестный статус заказа",
    "NOT_FOUND": "Ресурс не найден",
}


def api_error(status_code: int, code: str, message: str, details: Any | None = None) -> HTTPException:
    payload: dict[str, Any] = {"error": code, "message": message}
    if details is not None:
        payload["details"] = details
    return HTTPException(status_code=status_code, detail=payload)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_handler(_: Request, exc: RequestValidationError):
        return ORJSONResponse(
            status_code=422,
            content={
                "error": "VALIDATION_ERROR",
                "message": "Ошибка валидации запроса",
                "details": exc.errors(),
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(_: Request, exc: StarletteHTTPException):
        # Если detail - dict (новый формат), отдаём как есть
        if isinstance(exc.detail, dict):
            return ORJSONResponse(status_code=exc.status_code, content=exc.detail)

        # Если detail - строка (старый стиль), оборачиваем в единый формат
        if isinstance(exc.detail, str):
            code = exc.detail
            return ORJSONResponse(
                status_code=exc.status_code,
                content={"error": code, "message": ERROR_MESSAGES.get(code, code)},
            )

        return ORJSONResponse(status_code=exc.status_code, content={"error": "HTTP_ERROR"})

    @app.exception_handler(Exception)
    async def unhandled(_: Request, __: Exception):
        return ORJSONResponse(
            status_code=500,
            content={"error": "INTERNAL_ERROR", "message": "Внутренняя ошибка сервера"},
        )