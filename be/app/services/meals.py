"""List, read, correct and delete meals. Points and limits never change after the fact."""

from __future__ import annotations

import base64
import binascii
from dataclasses import replace
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from app.ports import MealType
from app.ports.repositories import MealCursor, MealRecord
from app.services.common import parse_timezone, require_meal_consent, require_user
from app.services.context import ServiceContext
from app.services.errors import InvalidCursor, MealNotFound, ValidationFailed
from app.services.views import MealPage

MAX_ITEMS = 30
MAX_ITEM_LENGTH = 80
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 50


class MealRange(StrEnum):
    TODAY = "today"
    SEVEN_DAYS = "7d"
    THIRTY_DAYS = "30d"


_RANGE_DAYS = {MealRange.TODAY: 0, MealRange.SEVEN_DAYS: 6, MealRange.THIRTY_DAYS: 29}


def encode_cursor(meal: MealRecord) -> str:
    raw = f"{meal.logged_at.isoformat()}|{meal.id}".encode()
    return base64.urlsafe_b64encode(raw).decode()


def decode_cursor(value: str) -> MealCursor:
    try:
        raw = base64.urlsafe_b64decode(value.encode()).decode()
        logged_at, meal_id = raw.split("|")
        parsed = datetime.fromisoformat(logged_at)
        if parsed.utcoffset() is None:
            raise ValueError("naive cursor")
        return MealCursor(logged_at=parsed, id=UUID(meal_id))
    except (binascii.Error, ValueError, UnicodeDecodeError) as exc:
        raise InvalidCursor from exc


async def list_meals(
    ctx: ServiceContext,
    user_id: UUID,
    *,
    meal_range: MealRange,
    cursor: str | None,
    limit: int = DEFAULT_PAGE_SIZE,
) -> MealPage:
    limit = max(1, min(limit, MAX_PAGE_SIZE))
    decoded = decode_cursor(cursor) if cursor else None
    async with ctx.uow_factory() as uow:
        user = await require_user(uow, user_id)
        await require_meal_consent(uow, user_id)
        today = ctx.clock.today(parse_timezone(user.timezone))
        since = today - timedelta(days=_RANGE_DAYS[meal_range])
        rows = await uow.meals.list_page(user_id, since_day=since, cursor=decoded, limit=limit + 1)
    page = rows[:limit]
    next_cursor = encode_cursor(page[-1]) if len(rows) > limit else None
    return MealPage(items=page, next_cursor=next_cursor)


async def get_meal(ctx: ServiceContext, user_id: UUID, meal_id: UUID) -> MealRecord:
    async with ctx.uow_factory() as uow:
        await require_user(uow, user_id)
        await require_meal_consent(uow, user_id)
        meal = await uow.meals.get(user_id, meal_id)
    if meal is None:
        raise MealNotFound
    return meal


def clean_items(items: list[str]) -> list[str]:
    cleaned = [item.strip() for item in items]
    if len(cleaned) > MAX_ITEMS or any(not 0 < len(item) <= MAX_ITEM_LENGTH for item in cleaned):
        raise ValidationFailed(
            f"Items must have at most {MAX_ITEMS} entries of 1 to {MAX_ITEM_LENGTH} characters."
        )
    return cleaned


async def update_meal(
    ctx: ServiceContext,
    user_id: UUID,
    meal_id: UUID,
    *,
    items: list[str] | None,
    meal_type: MealType | None,
) -> MealRecord:
    cleaned = clean_items(items) if items is not None else None
    async with ctx.uow_factory() as uow:
        await require_user(uow, user_id)
        await require_meal_consent(uow, user_id)
        meal = await uow.meals.get(user_id, meal_id)
        if meal is None:
            raise MealNotFound
        if cleaned is not None:
            meal = replace(meal, items=cleaned, item_count=len(cleaned))
        if meal_type is not None:
            meal = replace(meal, meal_type=meal_type.value)
        await uow.meals.save(meal)
        await uow.commit()
    return meal


async def delete_meal(ctx: ServiceContext, user_id: UUID, meal_id: UUID) -> None:
    """Soft delete. Points, daily usage and lives are intentionally left as they were."""
    async with ctx.uow_factory() as uow:
        await require_user(uow, user_id)
        await require_meal_consent(uow, user_id)
        meal = await uow.meals.get(user_id, meal_id)
        if meal is None:
            raise MealNotFound
        await uow.meals.save(replace(meal, deleted_at=ctx.clock.now()))
        await uow.commit()
