"""Use-case tests against the in-memory UnitOfWork and fake adapters (no database)."""

from __future__ import annotations

import pytest

from app.domain import Mood, PetEvent
from app.ports.repositories import ConsentType
from app.services import auth as auth_service
from app.services.consents import record_consent
from app.services.errors import (
    DailyLimitReached,
    EmailAlreadyRegistered,
    InvalidCredentials,
    MealConsentRequired,
    NotFood,
    PetAlreadyPaused,
    PetNotPaused,
    PhotoNotReadable,
    PremiumRequired,
    VisionUnavailable,
)
from app.services.get_pet import get_pet
from app.services.log_meal import log_meal
from app.services.meals import MealRange, delete_meal, list_meals, update_meal
from app.services.pause_pet import pause_pet, resume_pet
from tests.support.builders import PHOTO, make_premium, make_user, make_world


async def test_register_creates_pet_with_two_lives_and_rejects_duplicates() -> None:
    world = make_world()
    user_id = await make_user(world, meal_consent=False)
    pet = await get_pet(world.ctx, user_id)
    assert (pet.lives, pet.max_lives, pet.points, pet.mood) == (2, 4, 0, Mood.TIRED)
    with pytest.raises(EmailAlreadyRegistered):
        await make_user(world, meal_consent=False)


async def test_login_and_wrong_password() -> None:
    world = make_world()
    await make_user(world)
    tokens = await auth_service.login(
        world.ctx, email="ANA@example.com", password="correct-horse-1"
    )
    assert tokens.access_token
    with pytest.raises(InvalidCredentials):
        await auth_service.login(world.ctx, email="ana@example.com", password="nope-nope-nope")


async def test_meal_requires_active_consent() -> None:
    world = make_world()
    user_id = await make_user(world, meal_consent=False)
    with pytest.raises(MealConsentRequired):
        await log_meal(world.ctx, user_id, PHOTO)
    await record_consent(
        world.ctx, user_id, consent_type=ConsentType.MEAL_DATA, version="1.0", accepted=True
    )
    await log_meal(world.ctx, user_id, PHOTO)
    await record_consent(
        world.ctx, user_id, consent_type=ConsentType.MEAL_DATA, version="1.0", accepted=False
    )
    with pytest.raises(MealConsentRequired):
        await log_meal(world.ctx, user_id, PHOTO)
    with pytest.raises(MealConsentRequired):
        await list_meals(world.ctx, user_id, meal_range=MealRange.TODAY, cursor=None)


async def test_log_meal_awards_points_and_streak() -> None:
    world = make_world()
    user_id = await make_user(world)
    result = await log_meal(world.ctx, user_id, PHOTO)
    assert result.pet.points == 10
    assert result.pet.streak_days == 1
    assert result.pet.mood is Mood.HAPPY
    assert result.meal.new_foods == result.meal.items  # first time every item is seen


async def test_daily_limit_blocks_third_photo_without_touching_lives() -> None:
    world = make_world()
    user_id = await make_user(world)
    await log_meal(world.ctx, user_id, b"a")
    await log_meal(world.ctx, user_id, b"b")
    with pytest.raises(DailyLimitReached):
        await log_meal(world.ctx, user_id, b"c")
    pet = await get_pet(world.ctx, user_id)
    assert pet.lives == 2
    assert pet.points == 20
    world.next_day()
    await log_meal(world.ctx, user_id, b"c")  # new local day, limit is back


async def test_failed_analysis_does_not_consume_limit_or_change_lives() -> None:
    world = make_world()
    user_id = await make_user(world)
    for payload, error in [
        (b"", PhotoNotReadable),
        (b"NOTFOOD", NotFood),
        (b"UNAVAILABLE", VisionUnavailable),
        (b"", PhotoNotReadable),
    ]:
        with pytest.raises(error):
            await log_meal(world.ctx, user_id, payload)
    assert world.factory.store.usage == {}
    assert world.factory.store.meals == {}
    assert world.factory.store.points == []
    await log_meal(world.ctx, user_id, b"a")
    await log_meal(world.ctx, user_id, b"b")  # both successes still allowed after 4 failures
    assert (await get_pet(world.ctx, user_id)).lives == 2


async def test_missed_days_faint_the_pet_and_a_log_wakes_it() -> None:
    world = make_world()
    user_id = await make_user(world)
    world.next_day(3)  # days 0, 1 and 2 missed: 2 lives gone
    pet = await get_pet(world.ctx, user_id)
    assert (pet.lives, pet.mood) == (0, Mood.FAINTED)
    assert pet.events == (PetEvent.LIFE_LOST,)
    assert (await get_pet(world.ctx, user_id)).events == ()  # events are one-shot
    result = await log_meal(world.ctx, user_id, PHOTO)
    assert PetEvent.WAKE_UP in result.events
    assert result.pet.lives == 1
    assert result.pet.points == 15  # +10 meal, +5 wake up
    assert result.pet.mood is Mood.HAPPY


async def test_seven_day_streak_gives_a_life_and_celebrates() -> None:
    world = make_world()
    user_id = await make_user(world)
    events: list[tuple[PetEvent, ...]] = []
    for index in range(7):
        if index:
            world.next_day()
        events.append((await log_meal(world.ctx, user_id, PHOTO)).events)
    assert events[-1] == (PetEvent.CELEBRATE,)
    assert (await get_pet(world.ctx, user_id)).lives == 3


async def test_pause_is_premium_and_protects_lives() -> None:
    world = make_world()
    user_id = await make_user(world)
    with pytest.raises(PremiumRequired):
        await pause_pet(world.ctx, user_id, days=3)
    await make_premium(world, user_id)
    paused = await pause_pet(world.ctx, user_id, days=3)
    assert paused.mood is Mood.PAUSED
    with pytest.raises(PetAlreadyPaused):
        await pause_pet(world.ctx, user_id, days=1)
    world.next_day(2)
    assert (await get_pet(world.ctx, user_id)).lives == 2  # no loss while paused
    resumed = await resume_pet(world.ctx, user_id)
    assert resumed.mood is not Mood.PAUSED
    with pytest.raises(PetNotPaused):
        await resume_pet(world.ctx, user_id)


async def test_correct_and_delete_never_change_points() -> None:
    world = make_world()
    user_id = await make_user(world)
    meal = (await log_meal(world.ctx, user_id, PHOTO)).meal
    updated = await update_meal(
        world.ctx, user_id, meal.id, items=["tapioca", "egg"], meal_type=None
    )
    assert updated.items == ["tapioca", "egg"]
    assert updated.item_count == 2
    await delete_meal(world.ctx, user_id, meal.id)
    page = await list_meals(world.ctx, user_id, meal_range=MealRange.SEVEN_DAYS, cursor=None)
    assert page.items == []
    pet = await get_pet(world.ctx, user_id)
    assert pet.points == 10
    # Deleting does not give the limit back.
    await log_meal(world.ctx, user_id, b"b")
    with pytest.raises(DailyLimitReached):
        await log_meal(world.ctx, user_id, b"c")


async def test_list_meals_paginates_with_cursor() -> None:
    world = make_world()
    user_id = await make_user(world)
    for index in range(2):
        await log_meal(world.ctx, user_id, bytes([index + 1]))
    first = await list_meals(world.ctx, user_id, meal_range=MealRange.TODAY, cursor=None, limit=1)
    assert len(first.items) == 1
    assert first.next_cursor is not None
    second = await list_meals(
        world.ctx, user_id, meal_range=MealRange.TODAY, cursor=first.next_cursor, limit=1
    )
    assert len(second.items) == 1
    assert second.next_cursor is None
    assert first.items[0].id != second.items[0].id
