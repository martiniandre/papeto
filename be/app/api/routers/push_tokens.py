"""Push token routes."""

from __future__ import annotations

from fastapi import APIRouter, Response

from app.api.deps import Ctx, UserId
from app.api.schemas.push_tokens import PushTokenOut, PushTokenRequest
from app.services.push_tokens import register_push_token, remove_push_token

router = APIRouter(prefix="/push-tokens", tags=["push"])


@router.post("", status_code=201)
async def post_push_token(body: PushTokenRequest, ctx: Ctx, user_id: UserId) -> PushTokenOut:
    record = await register_push_token(ctx, user_id, token=body.token, platform=body.platform.value)
    return PushTokenOut.from_record(record)


@router.delete("/{token}", status_code=204)
async def delete_push_token(token: str, ctx: Ctx, user_id: UserId) -> Response:
    await remove_push_token(ctx, user_id, token)
    return Response(status_code=204)
