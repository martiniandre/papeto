"""Log a meal, from a photo or by hand (RF-95).

Photo flow: consent -> daily limit -> vision -> register_log -> persist meal, pet, points and usage.
A failed analysis raises before anything is written, so it never consumes the limit and never
changes lives. The photo bytes only live inside this function call: they are not stored or logged.

Manual flow: consent -> register_log -> persist. Same pet and points rules as a photo log, but it
never calls the vision provider and never consumes the AI photo limit.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from app.domain import (
    PetEvent,
    Plan,
    PointsReason,
    ProductEvent,
    can_analyze_photo,
    level_events,
    level_for_points,
    pick_tip,
    register_log,
    settle,
)
from app.ports import (
    MealType,
    NotFoodError,
    PhotoNotReadableError,
    PhotoTooLargeError,
    VisionUnavailableError,
)
from app.ports.repositories import MealRecord, MealSource, PointsEventRecord, UnitOfWork
from app.services.analytics import life_change_events, track_all
from app.services.common import (
    build_pet_view,
    current_plan,
    parse_timezone,
    pause_windows,
    require_adult_user,
    require_meal_consent,
)
from app.services.context import ServiceContext
from app.services.errors import (
    DailyLimitReached,
    NotFood,
    PhotoNotReadable,
    PhotoTooLarge,
    ValidationFailed,
    VisionUnavailable,
)
from app.services.get_pet import load_pet
from app.services.meals import clean_items
from app.services.views import LogMealResult

DEFAULT_LANGUAGE = "pt-BR"
NEW_FOODS_WINDOW_DAYS = 30
MANUAL_CONFIDENCE = 1.0  # the user chose the items; there is no model uncertainty


async def _persist_log(
    ctx: ServiceContext,
    uow: UnitOfWork,
    user_id: UUID,
    *,
    today: date,
    now: datetime,
    zone: ZoneInfo,
    meal: MealRecord,
) -> LogMealResult:
    """Apply the pet log transition and save meal, points and pet. The caller records usage."""
    pet = await load_pet(uow, user_id)
    logged_days = await uow.usage.logged_days(user_id)
    windows = await pause_windows(uow, user_id, zone)
    scored = await uow.points.count_on_day(user_id, PointsReason.MEAL_LOGGED, today)
    outcome = register_log(pet.state, logged_days, windows, today, scored, ctx.rules)
    points_before = await uow.points.total(user_id)
    level_before = level_for_points(points_before, ctx.rules)
    level = level_for_points(points_before + sum(a.amount for a in outcome.points), ctx.rules)
    baseline = pet.last_seen_level if pet.last_seen_level is not None else level_before
    events = outcome.events + level_events(baseline, level)

    seen = await uow.meals.recent_items(user_id, today - timedelta(days=NEW_FOODS_WINDOW_DAYS))
    meal = replace(meal, new_foods=[item for item in meal.items if item.lower() not in seen])
    await uow.meals.add(meal)
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
    saved = replace(
        pet, state=outcome.pet, last_seen_lives=outcome.pet.lives, last_seen_level=level
    )
    await uow.pets.save(saved)
    view = await build_pet_view(uow, saved, outcome.pet, today, now, (), ctx.rules, zone)
    pending = life_change_events(
        pet.last_seen_lives, settle(pet.state, logged_days, windows, today).lives
    )
    if PetEvent.WAKE_UP in outcome.events:
        pending.append((ProductEvent.PET_WOKE_UP, {}))
    pending.append((ProductEvent.MEAL_LOGGED, {"source": meal.source.value}))
    return LogMealResult(meal=meal, pet=view, events=events, pending_events=tuple(pending))


async def log_meal(
    ctx: ServiceContext, user_id: UUID, image: bytes, language: str = DEFAULT_LANGUAGE
) -> LogMealResult:
    # 1. Cheap checks first, in a short transaction without row locks.
    async with ctx.uow_factory() as uow:
        user = await require_adult_user(uow, user_id)
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
    except PhotoTooLargeError as exc:
        raise PhotoTooLarge from exc
    except NotFoodError as exc:
        raise NotFood from exc
    except VisionUnavailableError as exc:
        raise VisionUnavailable from exc

    # 3. Persist under a row lock on the pet; re-check the limit in case of parallel requests.
    async with ctx.uow_factory() as uow:
        now = ctx.clock.now()
        today = ctx.clock.today(zone)
        await load_pet(uow, user_id)  # take the pet row lock before re-reading usage
        if not can_analyze_photo(plan, await uow.usage.count(user_id, today), ctx.rules):
            raise DailyLimitReached
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
            new_foods=[],
            source=MealSource.PHOTO,
            vision_provider=ctx.vision.provider_name,
            model_version=ctx.vision.model_version,
            prompt_version=ctx.vision.prompt_version,
        )
        result = await _persist_log(ctx, uow, user_id, today=today, now=now, zone=zone, meal=meal)
        await uow.usage.increment(user_id, today)
        await uow.commit()
    await track_all(ctx, user, result.pending_events)
    if plan is Plan.PREMIUM:
        result = replace(result, pet_tip=pick_tip(meal.food_groups, today))
    return result


async def log_manual_meal(
    ctx: ServiceContext, user_id: UUID, *, items: list[str], meal_type: MealType
) -> LogMealResult:
    """RF-95: register a meal from items chosen by hand. Never touches the AI photo limit."""
    cleaned = clean_items(items)
    if not cleaned:
        raise ValidationFailed("Choose at least one item.")
    async with ctx.uow_factory() as uow:
        user = await require_adult_user(uow, user_id)
        await require_meal_consent(uow, user_id)
        zone = parse_timezone(user.timezone)
        now = ctx.clock.now()
        today = ctx.clock.today(zone)
        meal = MealRecord(
            id=ctx.ids.new_id(),
            user_id=user_id,
            logged_at=now,
            local_day=today,
            meal_type=meal_type.value,
            description="",
            items=cleaned,
            food_groups=[],
            item_count=len(cleaned),
            colors=[],
            confidence=MANUAL_CONFIDENCE,
            plate_share={},
            new_foods=[],
            source=MealSource.MANUAL,
        )
        result = await _persist_log(ctx, uow, user_id, today=today, now=now, zone=zone, meal=meal)
        await uow.usage.increment_manual(user_id, today)
        await uow.commit()
    await track_all(ctx, user, result.pending_events)
    return result
