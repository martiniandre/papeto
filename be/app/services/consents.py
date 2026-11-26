"""Record consent decisions. Rows are append-only; the latest per type is the current state."""

from __future__ import annotations

from uuid import UUID

from app.ports.repositories import ConsentRecord, ConsentType
from app.services.common import require_user
from app.services.context import ServiceContext


async def record_consent(
    ctx: ServiceContext,
    user_id: UUID,
    *,
    consent_type: ConsentType,
    version: str,
    accepted: bool,
) -> ConsentRecord:
    record = ConsentRecord(
        id=ctx.ids.new_id(),
        user_id=user_id,
        type=consent_type,
        version=version,
        accepted=accepted,
        created_at=ctx.clock.now(),
    )
    async with ctx.uow_factory() as uow:
        await require_user(uow, user_id)
        await uow.consents.add(record)
        await uow.commit()
    return record
