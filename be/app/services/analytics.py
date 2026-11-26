"""Emit RF-70 product events. Respects the user's opt-out; never lets analytics break a request.

The analytics id is an HMAC of the user id with a server secret: stable (so funnels and the
"logged within 7 days after fainting" metric can be computed), random-looking, and not reversible
or linkable to a name or email without the secret. Properties are enums, counts and booleans only.
"""

from __future__ import annotations

import hashlib
import hmac
from collections.abc import Iterable
from uuid import UUID

from app.domain import ProductEvent
from app.ports.repositories import UserRecord
from app.services.context import ServiceContext

Properties = dict[str, str | int | bool]


def analytics_id(ctx: ServiceContext, user_id: UUID) -> str:
    digest = hmac.new(ctx.analytics_id_secret.encode(), user_id.bytes, hashlib.sha256)
    return digest.hexdigest()[:32]


async def track(
    ctx: ServiceContext, user: UserRecord, event: ProductEvent, properties: Properties | None = None
) -> None:
    """Send one event unless the user opted out. Call after the transaction committed."""
    if user.analytics_opt_out:
        return
    try:
        await ctx.analytics.track(analytics_id(ctx, user.id), event.value, properties or {})
    except Exception as exc:  # analytics must never fail a request
        ctx.error_reporter.capture(exc)


def life_change_events(
    last_seen_lives: int | None, lives_now: int
) -> list[tuple[ProductEvent, Properties]]:
    """`life_lost` (and `pet_fainted` at zero) when lives dropped since the last seen value."""
    if last_seen_lives is None or lives_now >= last_seen_lives:
        return []
    events: list[tuple[ProductEvent, Properties]] = [
        (ProductEvent.LIFE_LOST, {"lives_left": lives_now})
    ]
    if lives_now == 0:
        events.append((ProductEvent.PET_FAINTED, {}))
    return events


async def track_all(
    ctx: ServiceContext, user: UserRecord, events: Iterable[tuple[ProductEvent, Properties]]
) -> None:
    for event, properties in events:
        await track(ctx, user, event, properties)
