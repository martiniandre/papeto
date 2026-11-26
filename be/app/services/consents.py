"""Record consent decisions. Rows are append-only; the latest per type is the current state.

Revoking `analytics` turns the analytics opt-out on (and accepting it turns it off). Revoking
`meal_data` makes meal endpoints answer 403 `MEAL_CONSENT_REQUIRED` right away (the latest consent
row is what `require_meal_consent` reads) and tells the app to offer export and deletion.
"""

from __future__ import annotations

from dataclasses import replace
from uuid import UUID

from app.domain import ProductEvent
from app.ports.repositories import ConsentRecord, ConsentType
from app.services.analytics import track
from app.services.common import require_user
from app.services.context import ServiceContext
from app.services.views import ConsentResult

MEAL_REVOKED_ACTIONS = ("export", "delete_meals", "delete_account")


async def record_consent(
    ctx: ServiceContext,
    user_id: UUID,
    *,
    consent_type: ConsentType,
    version: str,
    accepted: bool,
) -> ConsentResult:
    record = ConsentRecord(
        id=ctx.ids.new_id(),
        user_id=user_id,
        type=consent_type,
        version=version,
        accepted=accepted,
        created_at=ctx.clock.now(),
    )
    async with ctx.uow_factory() as uow:
        user = await require_user(uow, user_id)
        await uow.consents.add(record)
        if consent_type is ConsentType.ANALYTICS and user.analytics_opt_out == accepted:
            user = replace(user, analytics_opt_out=not accepted)
            await uow.users.save(user)
        await uow.commit()
    if accepted:  # after the opt-out above, so a fresh "no" to analytics emits nothing
        await track(ctx, user, ProductEvent.CONSENTS_ACCEPTED, {"type": consent_type.value})
    revoked_meals = consent_type is ConsentType.MEAL_DATA and not accepted
    return ConsentResult(
        record=record, suggested_actions=MEAL_REVOKED_ACTIONS if revoked_meals else ()
    )
