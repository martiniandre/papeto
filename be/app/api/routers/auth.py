"""Auth routes: register, login, refresh, forgot and reset password."""

from __future__ import annotations

from fastapi import APIRouter, Response

from app.api.deps import Ctx
from app.api.schemas.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.services import auth as auth_service
from app.services.password_reset import request_password_reset, reset_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
async def register(body: RegisterRequest, ctx: Ctx) -> TokenResponse:
    pair = await auth_service.register(
        ctx,
        email=body.email,
        password=body.password,
        name=body.name,
        timezone=body.timezone,
        adult_confirmed=body.adult_confirmed,
    )
    return TokenResponse.from_pair(pair)


@router.post("/login")
async def login(body: LoginRequest, ctx: Ctx) -> TokenResponse:
    return TokenResponse.from_pair(
        await auth_service.login(ctx, email=body.email, password=body.password)
    )


@router.post("/refresh")
async def refresh(body: RefreshRequest, ctx: Ctx) -> TokenResponse:
    return TokenResponse.from_pair(
        await auth_service.refresh(ctx, refresh_token=body.refresh_token)
    )


@router.post("/password/forgot", status_code=202)
async def forgot_password(body: ForgotPasswordRequest, ctx: Ctx) -> ForgotPasswordResponse:
    """Always 202 with the same body: the response never reveals whether the email exists."""
    await request_password_reset(ctx, email=body.email)
    return ForgotPasswordResponse()


@router.post("/password/reset", status_code=204)
async def reset(body: ResetPasswordRequest, ctx: Ctx) -> Response:
    await reset_password(ctx, token=body.token, new_password=body.password)
    return Response(status_code=204)
