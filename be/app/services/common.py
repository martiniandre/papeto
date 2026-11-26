"""Helpers shared by use cases."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.domain import (
    DEFAULT_RULES,
    PauseWindow,
    PetEvent,
    PetRulesConfig,
    PetState,
    Plan,
    compute_mood,
    pause_window_from_instants,
    settle,
)
from app.ports.repositories import ConsentType, PetRecord, UnitOfWork, UserRecord
from app.services.errors import InvalidTimezone, InvalidToken, MealConsentRequired
from app.services.views import PetView

_ACTIVE_STATUSES = frozenset({"active", "trialing"})


def parse_timezone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError, OSError) as exc:
        raise InvalidTimezone from exc


async def require_user(uow: UnitOfWork, user_id: UUID) -> UserRecord:
    user = await uow.users.get(user_id)
    if user is None:
        raise InvalidToken
    return user


async def current_plan(uow: UnitOfWork, user_id: UUID, now: datetime) -> Plan:
    subscription = await uow.subscriptions.get(user_id)
    if subscription is None or subscription.status not in _ACTIVE_STATUSES:
        return Plan.FREE
    if subscription.current_period_end is not None and subscription.current_period_end <= now:
        return Plan.FREE
    return Plan.PREMIUM


async def require_meal_consent(uow: UnitOfWork, user_id: UUID) -> None:
    latest = await uow.consents.latest_by_type(user_id)
    consent = latest.get(ConsentType.MEAL_DATA)
    if consent is None or not consent.accepted:
        raise MealConsentRequired


async def pause_windows(uow: UnitOfWork, user_id: UUID, timezone: ZoneInfo) -> list[PauseWindow]:
    windows: list[PauseWindow] = []
    for pause in await uow.pauses.list_for_user(user_id):
        window = pause_window_from_instants(pause.started_at, pause.ends_at, timezone)
        if window is not None:
            windows.append(window)
    return windows


async def settled_state(
    uow: UnitOfWork, user_id: UUID, pet: PetRecord, timezone: ZoneInfo, today: date
) -> PetState:
    """The pet state after applying missed days up to `today` (not saved)."""
    logged_days = await uow.usage.logged_days(user_id)
    windows = await pause_windows(uow, user_id, timezone)
    return settle(pet.state, logged_days, windows, today)


async def build_pet_view(
    uow: UnitOfWork,
    pet: PetRecord,
    state: PetState,
    today: date,
    now: datetime,
    events: tuple[PetEvent, ...] = (),
    rules: PetRulesConfig = DEFAULT_RULES,
) -> PetView:
    return PetView(
        name=pet.name,
        color=pet.color,
        lives=state.lives,
        max_lives=rules.max_lives,
        streak_days=state.streak_days,
        points=await uow.points.total(pet.user_id),
        mood=compute_mood(state, today, now),
        events=events,
    )
