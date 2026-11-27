"""Profile, pending deletion and export."""

from __future__ import annotations

from dataclasses import replace
from datetime import time, timedelta
from uuid import UUID

from app.domain import NotificationPrefs, ProductEvent
from app.ports.repositories import UserExport
from app.services.analytics import track
from app.services.common import current_plan, parse_timezone, require_user
from app.services.context import ServiceContext
from app.services.views import MeView


async def get_me(ctx: ServiceContext, user_id: UUID) -> MeView:
    async with ctx.uow_factory() as uow:
        user = await require_user(uow, user_id)
        plan = await current_plan(uow, user_id, ctx.clock.now())
        consents = await uow.consents.latest_by_type(user_id)
    scheduled = (
        user.deletion_requested_at + timedelta(days=ctx.deletion_grace_days)
        if user.deletion_requested_at
        else None
    )
    return MeView(user=user, plan=plan, consents=consents, deletion_scheduled_for=scheduled)


async def update_me(
    ctx: ServiceContext,
    user_id: UUID,
    *,
    timezone: str | None,
    analytics_opt_out: bool | None,
    adult_confirmed: bool | None = None,
    meal_reminder: bool | None = None,
    sleepy_notice: bool | None = None,
    weekly_summary: bool | None = None,
    quiet_hours_start: time | None = None,
    quiet_hours_end: time | None = None,
) -> MeView:
    if timezone is not None:
        parse_timezone(timezone)
    async with ctx.uow_factory() as uow:
        user = await require_user(uow, user_id)
        if timezone is not None:
            user = replace(user, timezone=timezone)
        if analytics_opt_out is not None:
            user = replace(user, analytics_opt_out=analytics_opt_out)
        if adult_confirmed and user.adult_confirmed_at is None:
            # Only `true` is accepted (the schema enforces it); the first confirmation is kept.
            user = replace(user, adult_confirmed_at=ctx.clock.now())
        current = user.notifications
        prefs = NotificationPrefs(
            meal_reminder=current.meal_reminder if meal_reminder is None else meal_reminder,
            sleepy_notice=current.sleepy_notice if sleepy_notice is None else sleepy_notice,
            weekly_summary=current.weekly_summary if weekly_summary is None else weekly_summary,
            quiet_hours_start=quiet_hours_start or current.quiet_hours_start,
            quiet_hours_end=quiet_hours_end or current.quiet_hours_end,
        )
        user = replace(user, notifications=prefs)
        await uow.users.save(user)
        await uow.commit()
    return await get_me(ctx, user_id)


async def request_deletion(ctx: ServiceContext, user_id: UUID) -> MeView:
    """Start the pending deletion (the hard delete after the grace period is a later worker job)."""
    async with ctx.uow_factory() as uow:
        user = await require_user(uow, user_id)
        if user.deletion_requested_at is None:
            await uow.users.save(replace(user, deletion_requested_at=ctx.clock.now()))
            await uow.commit()
            await track(ctx, user, ProductEvent.ACCOUNT_DELETION_REQUESTED)
    return await get_me(ctx, user_id)


async def export_user(ctx: ServiceContext, user_id: UUID) -> UserExport:
    """Everything stored about the user. Always free, never behind Premium or consent."""
    async with ctx.uow_factory() as uow:
        user = await require_user(uow, user_id)
        await track(ctx, user, ProductEvent.EXPORT_REQUESTED)
        return UserExport(
            user=user,
            consents=await uow.consents.list_all(user_id),
            pet=await uow.pets.get(user_id),
            pauses=await uow.pauses.list_for_user(user_id),
            meals=await uow.meals.list_all(user_id),
            points=await uow.points.list_all(user_id),
            subscription=await uow.subscriptions.get(user_id),
        )
