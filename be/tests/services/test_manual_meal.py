"""RF-95 manual meal entry: same pet and points rules as a photo log, never the AI photo limit."""

from __future__ import annotations

import pytest

from app.domain import Mood, PetEvent
from app.ports import MealType
from app.ports.repositories import ConsentType, MealSource
from app.services.consents import record_consent
from app.services.errors import DailyLimitReached, MealConsentRequired, ValidationFailed
from app.services.get_pet import get_pet
from app.services.log_meal import log_manual_meal, log_meal
from tests.support.builders import PHOTO, make_user, make_world


async def test_manual_log_counts_for_the_pet_and_points() -> None:
    world = make_world()
    user_id = await make_user(world)
    result = await log_manual_meal(
        world.ctx, user_id, items=[" arroz ", "feijão"], meal_type=MealType.LUNCH
    )
    assert result.meal.source is MealSource.MANUAL
    assert result.meal.items == ["arroz", "feijão"]
    assert result.meal.item_count == 2
    assert result.meal.meal_type == "lunch"
    assert result.meal.new_foods == ["arroz", "feijão"]
    assert (result.pet.points, result.pet.streak_days, result.pet.mood) == (10, 1, Mood.HAPPY)
    assert result.events == ()


async def test_manual_log_does_not_consume_the_photo_limit() -> None:
    world = make_world()
    user_id = await make_user(world)
    await log_manual_meal(world.ctx, user_id, items=["pão"], meal_type=MealType.BREAKFAST)
    assert world.factory.store.usage == {}
    await log_meal(world.ctx, user_id, PHOTO)
    await log_meal(world.ctx, user_id, PHOTO)
    with pytest.raises(DailyLimitReached):
        await log_meal(world.ctx, user_id, PHOTO)
    # The photo limit never blocks a manual log.
    result = await log_manual_meal(world.ctx, user_id, items=["fruta"], meal_type=MealType.SNACK)
    assert result.pet.lives == 2


async def test_manual_and_photo_logs_share_the_daily_points_cap() -> None:
    world = make_world()
    user_id = await make_user(world)
    await log_meal(world.ctx, user_id, PHOTO)
    for item in ("a", "b", "c"):
        result = await log_manual_meal(world.ctx, user_id, items=[item], meal_type=MealType.SNACK)
    assert result.pet.points == 30  # at most 3 scored meals per local day


async def test_manual_log_keeps_the_day_from_being_missed() -> None:
    world = make_world()
    user_id = await make_user(world)
    await log_manual_meal(world.ctx, user_id, items=["sopa"], meal_type=MealType.DINNER)
    world.next_day()
    pet = await get_pet(world.ctx, user_id)
    assert (pet.lives, pet.streak_days, pet.events) == (2, 1, ())
    world.next_day()
    result = await log_manual_meal(world.ctx, user_id, items=["sopa"], meal_type=MealType.DINNER)
    assert (result.pet.lives, result.pet.streak_days) == (1, 1)  # the empty day still cost one


async def test_manual_log_wakes_a_fainted_pet() -> None:
    world = make_world()
    user_id = await make_user(world)
    world.next_day(3)
    assert (await get_pet(world.ctx, user_id)).mood is Mood.FAINTED
    result = await log_manual_meal(world.ctx, user_id, items=["ovo"], meal_type=MealType.LUNCH)
    assert result.events == (PetEvent.WAKE_UP,)
    assert (result.pet.lives, result.pet.points) == (1, 15)


async def test_manual_log_requires_meal_consent() -> None:
    world = make_world()
    user_id = await make_user(world, meal_consent=False)
    with pytest.raises(MealConsentRequired):
        await log_manual_meal(world.ctx, user_id, items=["ovo"], meal_type=MealType.LUNCH)
    await record_consent(
        world.ctx, user_id, consent_type=ConsentType.MEAL_DATA, version="1.0", accepted=True
    )
    await log_manual_meal(world.ctx, user_id, items=["ovo"], meal_type=MealType.LUNCH)


@pytest.mark.parametrize("items", [[], ["   "], ["x" * 81], ["ok"] * 31])
async def test_manual_log_validates_items(items: list[str]) -> None:
    world = make_world()
    user_id = await make_user(world)
    with pytest.raises(ValidationFailed):
        await log_manual_meal(world.ctx, user_id, items=items, meal_type=MealType.LUNCH)
    assert world.factory.store.meals == {}
    assert world.factory.store.points == []
