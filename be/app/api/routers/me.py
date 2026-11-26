"""Consents and account routes."""

from __future__ import annotations

from datetime import time

from fastapi import APIRouter

from app.api.deps import Ctx, UserId
from app.api.schemas.account import (
    ConsentOut,
    ConsentRequest,
    ExportResponse,
    MePatch,
    MeResponse,
    NotificationsPatch,
)
from app.services import account
from app.services.consents import record_consent

router = APIRouter(tags=["account"])


def _parse_hhmm(value: str | None) -> time | None:
    return time.fromisoformat(value) if value is not None else None


@router.post("/consents", status_code=201)
async def post_consent(body: ConsentRequest, ctx: Ctx, user_id: UserId) -> ConsentOut:
    record = await record_consent(
        ctx, user_id, consent_type=body.type, version=body.version, accepted=body.accepted
    )
    return ConsentOut.from_record(record)


@router.get("/me")
async def get_me(ctx: Ctx, user_id: UserId) -> MeResponse:
    return MeResponse.from_view(await account.get_me(ctx, user_id))


@router.patch("/me")
async def patch_me(body: MePatch, ctx: Ctx, user_id: UserId) -> MeResponse:
    prefs = body.notifications or NotificationsPatch()
    view = await account.update_me(
        ctx,
        user_id,
        timezone=body.timezone,
        analytics_opt_out=body.analytics_opt_out,
        meal_reminder=prefs.meal_reminder,
        sleepy_notice=prefs.sleepy_notice,
        weekly_summary=prefs.weekly_summary,
        quiet_hours_start=_parse_hhmm(prefs.quiet_hours_start),
        quiet_hours_end=_parse_hhmm(prefs.quiet_hours_end),
    )
    return MeResponse.from_view(view)


@router.delete("/me", status_code=202)
async def delete_me(ctx: Ctx, user_id: UserId) -> MeResponse:
    """Starts the 30-day pending deletion. Signing in again cancels it."""
    return MeResponse.from_view(await account.request_deletion(ctx, user_id))


@router.get("/me/export")
async def export_me(ctx: Ctx, user_id: UserId) -> ExportResponse:
    return ExportResponse.from_export(await account.export_user(ctx, user_id))
