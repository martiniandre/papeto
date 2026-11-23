"""Auth routes: register, login, refresh."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import Ctx
from app.api.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.services import auth as auth_service

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
