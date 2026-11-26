"""Account hard delete after the pending period (docs/product-rules.md, retention table).

1. Deletion requested more than `deletion_grace_days` ago (default 30): erase the personal data
   (meals, points, pauses, pet, push tokens, notice log, usage) and anonymize the user row (no
   email, name or password). Consent records and the subscription stay because the law asks
   for them to be kept for 5 years.
2. Anonymized more than 5 years ago: delete the user row and what is attached to it.

Both steps are idempotent and safe to run any number of times. Signing in again before the grace
period ends already cancelled the request, so a user with a pending request has not come back.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import timedelta

import structlog

from app.domain import DEFAULT_PREFS
from app.services.context import ServiceContext

log = structlog.get_logger()

LEGAL_RETENTION = timedelta(days=5 * 366)  # consents and subscriptions: 5 years
BATCH_SIZE = 100


@dataclass(frozen=True, slots=True)
class PurgeReport:
    anonymized: int = 0
    removed: int = 0


async def purge_deleted_accounts(ctx: ServiceContext) -> PurgeReport:
    now = ctx.clock.now()
    anonymized = 0
    async with ctx.uow_factory() as uow:
        pending = await uow.retention.list_pending_deletion(
            now - timedelta(days=ctx.deletion_grace_days), BATCH_SIZE
        )
    for user in pending:
        erased = replace(
            user,
            email=f"deleted-{user.id}@deleted.invalid",
            name="",
            password_hash=None,
            timezone="UTC",
            analytics_opt_out=True,
            notifications=DEFAULT_PREFS,
            anonymized_at=now,
        )
        async with ctx.uow_factory() as uow:  # one transaction per account
            await uow.retention.erase_personal_data(erased)
            await uow.commit()
        anonymized += 1

    removed = 0
    async with ctx.uow_factory() as uow:
        expired = await uow.retention.list_anonymized_before(now - LEGAL_RETENTION, BATCH_SIZE)
    for user_id in expired:
        async with ctx.uow_factory() as uow:
            await uow.retention.delete_user(user_id)
            await uow.commit()
        removed += 1

    log.info("account_purge", anonymized=anonymized, removed=removed)
    return PurgeReport(anonymized=anonymized, removed=removed)
