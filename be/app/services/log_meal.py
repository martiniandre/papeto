"""Log a meal from a photo.

Flow: consent -> daily limit -> vision -> register_log -> persist meal, pet, points and usage.
A failed analysis raises before anything is written, so it never consumes the limit and never
changes lives. The photo bytes only live inside this function call: they are not stored or logged.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from uuid import UUID

from app.domain import PointsReason, can_analyze_photo, register_log
from app.ports import NotFoodError, PhotoNotReadableError, VisionUnavailableError
from app.ports.repositories import MealRecord, PointsEventRecord
from app.services.common import (
    build_pet_view,
    current_plan,
    parse_timezone,
    pause_windows,
    require_meal_consent,
    require_user,
)
from app.services.context import ServiceContext
from app.services.errors import (
    DailyLimitReached,
    NotFood,
    PhotoNotReadable,
    VisionUnavailable,
)
from app.services.get_pet import load_pet
from app.services.views import LogMealResult

DEFAULT_LANGUAGE = "pt-BR"
NEW_FOODS_WINDOW_DAYS = 30


async def log_meal(
    ctx: ServiceContext, user_id: UUID, image: bytes, language: str = DEFAULT_LANGUAGE
) -> LogMealResult:
    # 1. Cheap checks first, in a short transaction without row locks.
    async with ctx.uow_factory() as uow:
        user = await require_user(uow, user_id)
        await require_meal_consent(uow, user_id)
        zone = parse_timezone(user.timezone)
        plan = await current_plan(uow, user_id, ctx.clock.now())
        used = await uow.usage.count(user_id, ctx.clock.today(zone))
    if not can_analyze_photo(plan, used, ctx.rules):
        raise DailyLimitReached

    # 2. Vision call outside any transaction. Failures write nothing.
    try:
        vision = await ctx.vision.analyze(image, language)
    except PhotoNotReadableError as exc:
        raise PhotoNotReadable from exc
    except NotFoodError as exc:
        raise NotFood from exc
    except VisionUnavailableError as exc:
        raise VisionUnavailable from exc

    # 3. Persist under a row lock on the pet; re-check the limit in case of parallel requests.
    async with ctx.uow_factory() as uow:
        now = ctx.clock.now()
        today = ctx.clock.today(zone)
        pet = await load_pet(uow, user_id)
        if not can_analyze_photo(plan, await uow.usage.count(user_id, today), ctx.rules):
            raise DailyLimitReached

        logged_days = await uow.usage.logged_days(user_id)
        windows = await pause_windows(uow, user_id, zone)
        scored = await uow.points.count_on_day(user_id, PointsReason.MEAL_LOGGED, today)
        outcome = register_log(pet.state, logged_days, windows, today, scored, ctx.rules)

        seen = await uow.meals.recent_items(user_id, today - timedelta(days=NEW_FOODS_WINDOW_DAYS))
        new_foods = [item for item in vision.items if item.lower() not in seen]
        meal = MealRecord(
            id=ctx.ids.new_id(),
            user_id=user_id,
            logged_at=now,
            local_day=today,
            meal_type=vision.meal_type.value,
            description=vision.description,
            items=list(vision.items),
            food_groups=list(vision.food_groups),
            item_count=vision.item_count,
            colors=list(vision.colors),
            confidence=vision.confidence,
            plate_share=dict(vision.plate_share),
            new_foods=new_foods,
        )
        await uow.meals.add(meal)
        await uow.usage.increment(user_id, today)
        await uow.points.add_many(
            [
                PointsEventRecord(
                    id=ctx.ids.new_id(),
                    user_id=user_id,
                    reason=award.reason,
                    amount=award.amount,
                    local_day=today,
                    created_at=now,
                )
                for award in outcome.points
            ]
        )
        saved = replace(pet, state=outcome.pet, last_seen_lives=outcome.pet.lives)
        await uow.pets.save(saved)
        view = await build_pet_view(uow, saved, outcome.pet, today, now, (), ctx.rules)
        await uow.commit()
    return LogMealResult(meal=meal, pet=view, events=outcome.events)
