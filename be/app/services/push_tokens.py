"""Register, refresh and remove the device tokens used for push notifications."""

from __future__ import annotations

from uuid import UUID

from app.ports.repositories import PushTokenRecord
from app.services.common import require_user
from app.services.context import ServiceContext


async def register_push_token(
    ctx: ServiceContext, user_id: UUID, *, token: str, platform: str
) -> PushTokenRecord:
    """Upsert by token. Re-registering the same token only updates its owner and platform."""
    record = PushTokenRecord(
        id=ctx.ids.new_id(),
        user_id=user_id,
        token=token,
        platform=platform,
        created_at=ctx.clock.now(),
    )
    async with ctx.uow_factory() as uow:
        await require_user(uow, user_id)
        await uow.push_tokens.upsert(record)
        await uow.commit()
    return record


async def remove_push_token(ctx: ServiceContext, user_id: UUID, token: str) -> None:
    async with ctx.uow_factory() as uow:
        await require_user(uow, user_id)
        await uow.push_tokens.delete(user_id, token)
        await uow.commit()
