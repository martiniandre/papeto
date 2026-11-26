"""FastAPI dependencies: the service context, the readiness probe and the authenticated user."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.errors import ApiError, ErrorCode
from app.ports import InvalidTokenError, TokenKind
from app.services.context import ServiceContext
from app.services.errors import InvalidToken

ReadinessCheck = Callable[[], Awaitable[dict[str, bool]]]

_bearer = HTTPBearer(auto_error=False)


def get_ctx(request: Request) -> ServiceContext:
    ctx: ServiceContext = request.app.state.ctx
    return ctx


def get_readiness(request: Request) -> ReadinessCheck:
    check: ReadinessCheck = request.app.state.readiness
    return check


def get_max_upload_bytes(request: Request) -> int:
    limit: int = request.app.state.max_upload_bytes
    return limit


Ctx = Annotated[ServiceContext, Depends(get_ctx)]


def current_user_id(
    ctx: Ctx,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> UUID:
    if credentials is None:
        raise ApiError(ErrorCode.UNAUTHORIZED, "Authentication required.")
    try:
        return ctx.auth.decode_token(credentials.credentials, TokenKind.ACCESS)
    except InvalidTokenError as exc:
        raise InvalidToken from exc


UserId = Annotated[UUID, Depends(current_user_id)]
