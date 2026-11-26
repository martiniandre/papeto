"""RF-70 product events, RF-98 support hint wiring and consent revocation (in-memory UoW)."""

from __future__ import annotations

from dataclasses import replace

import pytest

from app.domain import PetRulesConfig
from app.ports import MealType
from app.ports.repositories import ConsentType
from app.providers.fake_misc import RecordingAnalytics
from app.services.account import export_user, request_deletion, update_me
from app.services.consents import record_consent
from app.services.errors import MealConsentRequired
from app.services.get_pet import get_pet, update_pet
from app.services.log_meal import log_manual_meal, log_meal
from app.services.meals import MealRange, delete_all_meals, list_meals
from tests.support.builders import PHOTO, World, make_user, make_world

FORBIDDEN_VALUES = ("ana@example.com", "Ana", "Bolinha", "arroz")
FAINT_AND_RETURN = ["life_lost", "pet_fainted", "pet_woke_up", "meal_logged"]


def _world() -> tuple[World, RecordingAnalytics]:
    world = make_world()
    sink = RecordingAnalytics()
    world.ctx = replace(world.ctx, analytics=sink)
    return world, sink


async def _manual(world: World, user_id: object, item: str = "pão") -> None:
    await log_manual_meal(
        world.ctx,
        user_id,  # type: ignore[arg-type]
        items=[item],
        meal_type=MealType.LUNCH,
    )


async def test_funnel_events_and_privacy_of_payload() -> None:
    world, sink = _world()
    user_id = await make_user(world)
    await update_pet(world.ctx, user_id, name="Bolinha", color=None)
    await update_pet(world.ctx, user_id, name="Outro", color=None)  # only the first naming counts
    await _manual(world, user_id, "arroz")
    await log_meal(world.ctx, user_id, PHOTO)
    await export_user(world.ctx, user_id)
    await request_deletion(world.ctx, user_id)
    assert sink.names() == [
        "signup_completed",
        "consents_accepted",
        "pet_named",
        "meal_logged",
        "meal_logged",
        "export_requested",
        "account_deletion_requested",
    ]
    sources = [p["source"] for _, n, p in sink.events if n == "meal_logged"]
    assert sources == ["manual", "photo"]
    ids = {anon for anon, _, _ in sink.events}
    assert len(ids) == 1
    assert str(user_id) not in next(iter(ids))
    blob = repr(sink.events)
    assert not any(value in blob for value in FORBIDDEN_VALUES)


async def test_opt_out_emits_nothing() -> None:
    world, sink = _world()
    user_id = await make_user(world)
    sink.events.clear()
    await update_me(world.ctx, user_id, timezone=None, analytics_opt_out=True)
    await _manual(world, user_id)
    await export_user(world.ctx, user_id)
    assert sink.events == []


async def test_analytics_consent_toggles_the_opt_out() -> None:
    world, sink = _world()
    user_id = await make_user(world)
    sink.events.clear()
    await record_consent(
        world.ctx, user_id, consent_type=ConsentType.ANALYTICS, version="1.0", accepted=False
    )
    assert world.factory.store.users[user_id].analytics_opt_out is True
    await export_user(world.ctx, user_id)
    assert sink.events == []
    await record_consent(
        world.ctx, user_id, consent_type=ConsentType.ANALYTICS, version="1.0", accepted=True
    )
    assert world.factory.store.users[user_id].analytics_opt_out is False


async def test_faint_and_return_events_share_one_id() -> None:
    world, sink = _world()
    user_id = await make_user(world)
    sink.events.clear()
    world.next_day(3)  # two missed days -> fainted
    await get_pet(world.ctx, user_id)
    await get_pet(world.ctx, user_id)  # already seen: no duplicate events
    await _manual(world, user_id)
    assert sink.names() == FAINT_AND_RETURN
    assert len({anon for anon, _, _ in sink.events}) == 1


async def test_faint_first_seen_on_a_log_still_emits() -> None:
    world, sink = _world()
    user_id = await make_user(world)
    sink.events.clear()
    world.next_day(5)
    await _manual(world, user_id)
    assert sink.names() == FAINT_AND_RETURN


async def test_analytics_failure_never_breaks_the_request() -> None:
    class Broken:
        async def track(
            self, anonymous_id: str, event: str, properties: dict[str, str | int | bool]
        ) -> None:
            raise RuntimeError("down")

    world = make_world()
    world.ctx = replace(world.ctx, analytics=Broken())
    user_id = await make_user(world)
    assert (await get_pet(world.ctx, user_id)).lives == 2


async def test_support_hint_is_off_by_default_and_on_when_configured() -> None:
    world, _ = _world()
    user_id = await make_user(world)
    world.next_day(3)
    assert (await get_pet(world.ctx, user_id)).support_hint is False
    world.ctx = replace(world.ctx, rules=PetRulesConfig(risk_pattern_days=3))
    assert (await get_pet(world.ctx, user_id)).support_hint is True
    await _manual(world, user_id)
    assert (await get_pet(world.ctx, user_id)).support_hint is False


async def test_support_hint_never_costs_lives_or_points() -> None:
    world, _ = _world()
    user_id = await make_user(world)
    world.next_day(2)
    plain = await get_pet(world.ctx, user_id)
    world.ctx = replace(world.ctx, rules=PetRulesConfig(risk_pattern_days=1))
    hinted = await get_pet(world.ctx, user_id)
    assert hinted.support_hint is True
    assert (hinted.lives, hinted.points, hinted.streak_days) == (
        plain.lives,
        plain.points,
        plain.streak_days,
    )


async def test_revoking_meal_consent_blocks_meals_and_offers_follow_ups() -> None:
    world, _ = _world()
    user_id = await make_user(world)
    await _manual(world, user_id)
    result = await record_consent(
        world.ctx, user_id, consent_type=ConsentType.MEAL_DATA, version="1.0", accepted=False
    )
    assert result.suggested_actions == ("export", "delete_meals", "delete_account")
    with pytest.raises(MealConsentRequired):
        await log_meal(world.ctx, user_id, PHOTO)
    with pytest.raises(MealConsentRequired):
        await _manual(world, user_id)
    with pytest.raises(MealConsentRequired):
        await list_meals(world.ctx, user_id, meal_range=MealRange.TODAY, cursor=None)
    # Export and account deletion keep working.
    assert len((await export_user(world.ctx, user_id)).meals) == 1
    await request_deletion(world.ctx, user_id)
    again = await record_consent(
        world.ctx, user_id, consent_type=ConsentType.MEAL_DATA, version="1.0", accepted=True
    )
    assert again.suggested_actions == ()


async def test_delete_all_meals_keeps_account_pet_points_and_streak() -> None:
    world, _ = _world()
    user_id = await make_user(world)
    await _manual(world, user_id)
    await _manual(world, user_id, "leite")
    await record_consent(
        world.ctx, user_id, consent_type=ConsentType.MEAL_DATA, version="1.0", accepted=False
    )
    assert await delete_all_meals(world.ctx, user_id) == 2  # allowed without consent
    assert await delete_all_meals(world.ctx, user_id) == 0
    assert (await export_user(world.ctx, user_id)).meals == []
    pet = await get_pet(world.ctx, user_id)
    assert (pet.points, pet.streak_days, pet.lives) == (20, 1, 2)


async def test_notification_sent_event_only_when_delivered() -> None:
    from app.providers.fake_misc import RecordingPush
    from app.services.notices import run_notice_cycle
    from app.services.push_tokens import register_push_token

    world, sink = _world()
    user_id = await make_user(world)
    await register_push_token(world.ctx, user_id, token="ExponentPushToken[a]", platform="ios")
    sink.events.clear()
    dead = RecordingPush(invalid_tokens={"ExponentPushToken[a]"})
    await run_notice_cycle(world.ctx, dead)
    assert sink.events == []  # the only device was invalid: nothing was delivered
    world.next_day()
    await register_push_token(world.ctx, user_id, token="ExponentPushToken[b]", platform="ios")
    await run_notice_cycle(world.ctx, RecordingPush())
    assert [(n, p) for _, n, p in sink.events] == [("notification_sent", {"kind": "sleepy"})]
