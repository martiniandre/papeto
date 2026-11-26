"""Stable error codes and the error envelope: {"error": {"code": "...", "message": "..."}}.

The app translates `code`, so codes never change once released. Every `ServiceError.code` must be
listed in `STATUS_BY_CODE` (a test enforces it).
"""

from __future__ import annotations

from enum import StrEnum

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.services.errors import ServiceError

log = structlog.get_logger()


class ErrorCode(StrEnum):
    UNAUTHORIZED = "UNAUTHORIZED"
    INVALID_TOKEN = "INVALID_TOKEN"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    EMAIL_ALREADY_REGISTERED = "EMAIL_ALREADY_REGISTERED"
    ADULT_CONFIRMATION_REQUIRED = "ADULT_CONFIRMATION_REQUIRED"
    INVALID_TIMEZONE = "INVALID_TIMEZONE"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MEAL_CONSENT_REQUIRED = "MEAL_CONSENT_REQUIRED"
    DAILY_LIMIT_REACHED = "DAILY_LIMIT_REACHED"
    PHOTO_NOT_READABLE = "PHOTO_NOT_READABLE"
    PHOTO_TOO_LARGE = "PHOTO_TOO_LARGE"
    NOT_FOOD = "NOT_FOOD"
    VISION_UNAVAILABLE = "VISION_UNAVAILABLE"
    PREMIUM_REQUIRED = "PREMIUM_REQUIRED"
    MEAL_NOT_FOUND = "MEAL_NOT_FOUND"
    PET_NOT_FOUND = "PET_NOT_FOUND"
    PET_ALREADY_PAUSED = "PET_ALREADY_PAUSED"
    PET_NOT_PAUSED = "PET_NOT_PAUSED"
    NOT_ENOUGH_ATTRIBUTE_POINTS = "NOT_ENOUGH_ATTRIBUTE_POINTS"
    INVALID_CURSOR = "INVALID_CURSOR"
    INVALID_RESET_TOKEN = "INVALID_RESET_TOKEN"
    NOT_FOUND = "NOT_FOUND"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


STATUS_BY_CODE: dict[str, int] = {
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.INVALID_TOKEN: 401,
    ErrorCode.INVALID_CREDENTIALS: 401,
    ErrorCode.EMAIL_ALREADY_REGISTERED: 409,
    ErrorCode.ADULT_CONFIRMATION_REQUIRED: 422,
    ErrorCode.INVALID_TIMEZONE: 422,
    ErrorCode.VALIDATION_ERROR: 422,
    ErrorCode.MEAL_CONSENT_REQUIRED: 403,
    ErrorCode.DAILY_LIMIT_REACHED: 429,
    ErrorCode.PHOTO_NOT_READABLE: 422,
    ErrorCode.PHOTO_TOO_LARGE: 413,
    ErrorCode.NOT_FOOD: 422,
    ErrorCode.VISION_UNAVAILABLE: 503,
    ErrorCode.PREMIUM_REQUIRED: 402,
    ErrorCode.MEAL_NOT_FOUND: 404,
    ErrorCode.PET_NOT_FOUND: 404,
    ErrorCode.PET_ALREADY_PAUSED: 409,
    ErrorCode.PET_NOT_PAUSED: 409,
    ErrorCode.NOT_ENOUGH_ATTRIBUTE_POINTS: 400,
    ErrorCode.INVALID_CURSOR: 422,
    ErrorCode.INVALID_RESET_TOKEN: 400,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.METHOD_NOT_ALLOWED: 405,
    ErrorCode.INTERNAL_ERROR: 500,
}


class ApiError(Exception):
    """Raised by the API layer itself (auth header, upload checks)."""

    def __init__(self, code: ErrorCode, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def error_response(code: str, message: str, status: int | None = None) -> JSONResponse:
    resolved = status if status is not None else STATUS_BY_CODE.get(code, 500)
    headers = {"WWW-Authenticate": "Bearer"} if resolved == 401 else None
    return JSONResponse(
        status_code=resolved,
        content={"error": {"code": code, "message": message}},
        headers=headers,
    )


async def _service_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ServiceError)
    if exc.code not in STATUS_BY_CODE:
        log.error("unmapped_error_code", code=exc.code)
        return error_response(ErrorCode.INTERNAL_ERROR, "Something went wrong.")
    return error_response(exc.code, exc.message)


async def _api_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ApiError)
    return error_response(exc.code, exc.message)


async def _validation_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    # Only field locations are echoed: input values may hold passwords or emails.
    fields = sorted({".".join(str(part) for part in e["loc"][1:]) or "body" for e in exc.errors()})
    return error_response(ErrorCode.VALIDATION_ERROR, f"Invalid fields: {', '.join(fields)}.")


async def _http_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    if exc.status_code == 404:
        return error_response(ErrorCode.NOT_FOUND, "Resource not found.")
    if exc.status_code == 405:
        return error_response(ErrorCode.METHOD_NOT_ALLOWED, "Method not allowed.")
    if exc.status_code == 401:
        return error_response(ErrorCode.UNAUTHORIZED, "Authentication required.")
    return error_response(ErrorCode.INTERNAL_ERROR, "Something went wrong.", exc.status_code)


async def _unexpected(_: Request, exc: Exception) -> JSONResponse:
    log.error("unhandled_exception", error_type=type(exc).__name__)
    return error_response(ErrorCode.INTERNAL_ERROR, "Something went wrong.")


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ServiceError, _service_error)
    app.add_exception_handler(ApiError, _api_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.add_exception_handler(Exception, _unexpected)
