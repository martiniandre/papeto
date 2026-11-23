"""Lives, streak, wake-up and celebrate rules from docs/domain/pet-rules.md."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.domain import (
    DEFAULT_RULES,
    Mood,
    PauseWindow,
    PetEvent,
    PetRulesConfig,
    PetState,
    PointsReason,
    new_pet,
    read_events,
    register_log,
    settle,
)
from tests.unit.fakes import SAO_PAULO, FakeClock, FakeUser, at


@pytest.fixture
def user() -> FakeUser:
    return FakeUser(FakeClock(at(SAO_PAULO, 2026, 3, 2)), SAO_PAULO)


def test_new_pet_starts_with_two_lives_and_happy_after_first_log(user: FakeUser) -> None:
    assert user.read().lives == 2
    assert user.pet.streak_days == 0
    assert user.mood() is Mood.TIRED
    user.log()
    assert user.mood() is Mood.HAPPY


def test_creation_day_without_log_is_a_missed_day(user: FakeUser) -> None:
    user.next_day()
    assert user.read().lives == 1


def test_one_missed_day_leaves_one_life_and_sleepy(user: FakeUser) -> None:
    user.log()
    user.next_day(2)  # the day in between had no log
    assert user.read().lives == 1
    assert user.mood() is Mood.SLEEPY
    assert user.pet.streak_days == 0


def test_two_missed_days_faint_the_pet(user: FakeUser) -> None:
    user.log()
    user.next_day(3)
    assert user.read().lives == 0
    assert user.mood() is Mood.FAINTED


def test_lives_never_go_below_zero(user: FakeUser) -> None:
    user.log()
    user.next_day(60)
    assert user.read().lives == 0


def test_today_without_log_is_not_missed_yet(user: FakeUser) -> None:
    user.log()
    user.next_day()
    assert user.read().lives == 2
    assert user.mood() is Mood.TIRED


def test_log_while_fainted_wakes_with_one_life_and_five_points(user: FakeUser) -> None:
    user.log()
    user.next_day(3)
    assert user.read().lives == 0
    points_before = user.total_points()

    outcome = user.log()

    assert outcome.pet.lives == 1
    assert PetEvent.WAKE_UP in outcome.events
    wake = [a for a in outcome.points if a.reason is PointsReason.WAKE_UP]
    assert [a.amount for a in wake] == [5]
    assert user.total_points() == points_before + 5 + 10
    assert user.mood() is Mood.HAPPY


def test_wake_up_bonus_is_given_once_per_wake_up(user: FakeUser) -> None:
    user.log()
    user.next_day(3)
    first = user.log()
    second = user.log()
    assert PetEvent.WAKE_UP in first.events
    assert PetEvent.WAKE_UP not in second.events
    assert all(a.reason is not PointsReason.WAKE_UP for a in second.points)


def test_fainting_never_removes_points(user: FakeUser) -> None:
    user.log_daily(3)
    total = user.total_points()
    user.next_day(10)
    user.read()
    assert user.total_points() == total


def test_seven_consecutive_days_gain_a_life_and_celebrate(user: FakeUser) -> None:
    events = user.log_daily(7)
    assert user.pet.streak_days == 7
    assert user.pet.lives == 3
    assert events[-1] == (PetEvent.CELEBRATE,)
    assert all(PetEvent.CELEBRATE not in e for e in events[:-1])


def test_streak_gains_again_at_every_multiple_of_seven(user: FakeUser) -> None:
    user.log_daily(14)
    assert user.pet.lives == 4
    assert user.pet.streak_days == 14


def test_no_extra_life_at_maximum(user: FakeUser) -> None:
    events = user.log_daily(28)
    assert user.pet.lives == 4
    assert user.pet.streak_days == 28
    assert PetEvent.CELEBRATE not in events[20]
    assert PetEvent.CELEBRATE not in events[27]


def test_lives_never_exceed_maximum_even_after_wake_up() -> None:
    config = PetRulesConfig(starting_lives=1, max_lives=1, lives_after_wake_up=1)
    user = FakeUser(FakeClock(at(SAO_PAULO, 2026, 3, 2)), SAO_PAULO, config)
    user.log_daily(21)
    assert user.pet.lives == 1


def test_several_logs_on_one_day_count_once_for_streak(user: FakeUser) -> None:
    user.log()
    user.log()
    user.log()
    assert user.pet.streak_days == 1
    assert user.pet.lives == 2


def test_missed_day_resets_streak(user: FakeUser) -> None:
    user.log_daily(5)
    user.next_day(2)
    user.log()
    assert user.pet.streak_days == 1


def test_pause_covering_missed_days_keeps_lives_and_streak(user: FakeUser) -> None:
    user.log_daily(5)
    start = user.today() + timedelta(days=1)
    user.pause_windows.append(PauseWindow(start, start + timedelta(days=2)))
    user.next_day(3)  # three paused days without logs
    assert user.read().lives == 2
    assert user.pet.streak_days == 5

    outcome = user.log()
    assert outcome.pet.streak_days == 6
    user.next_day()
    outcome = user.log()
    assert outcome.pet.streak_days == 7
    assert outcome.pet.lives == 3
    assert PetEvent.CELEBRATE in outcome.events


def test_partial_pause_still_costs_the_unpaused_days(user: FakeUser) -> None:
    user.log()
    paused = user.today() + timedelta(days=1)
    user.pause_windows.append(PauseWindow(paused, paused))
    user.next_day(3)  # day+1 paused, day+2 missed
    assert user.read().lives == 1
    assert user.pet.streak_days == 0


def test_settle_is_idempotent(user: FakeUser) -> None:
    user.log_daily(3)
    user.next_day(2)
    today = user.today()
    once = settle(user.pet, user.logged_days, user.pause_windows, today)
    twice = settle(once, user.logged_days, user.pause_windows, today)
    assert once == twice
    assert once.lives == 1
    # An earlier date never undoes or reapplies anything.
    assert settle(once, user.logged_days, user.pause_windows, today - timedelta(days=5)) == once


def test_settle_does_not_mutate_input() -> None:
    pet = new_pet(date(2026, 3, 1))
    snapshot = PetState(pet.lives, pet.streak_days, pet.last_log_day, pet.settled_on)
    settle(pet, set(), [], date(2026, 3, 10))
    assert pet == snapshot


def test_settle_uses_logged_days_set() -> None:
    pet = new_pet(date(2026, 3, 1))
    logged = {date(2026, 3, 1), date(2026, 3, 3)}
    settled = settle(pet, logged, [], date(2026, 3, 4))
    assert settled.lives == 1  # only 2026-03-02 was missed
    assert settled.settled_on == date(2026, 3, 3)


def test_settle_with_many_missed_days_stays_at_zero() -> None:
    pet = new_pet(date(2020, 1, 1))
    settled = settle(pet, set(), [], date(2026, 1, 1))
    assert settled.lives == 0
    assert settled.streak_days == 0
    assert settled.settled_on == date(2025, 12, 31)


def test_read_events_reports_life_lost_only_when_lives_dropped() -> None:
    assert read_events(2, 1) == (PetEvent.LIFE_LOST,)
    assert read_events(1, 0) == (PetEvent.LIFE_LOST,)
    assert read_events(1, 1) == ()
    assert read_events(1, 2) == ()
    assert read_events(None, 0) == ()


def test_log_on_earlier_day_than_last_log_keeps_state() -> None:
    pet = PetState(
        lives=2, streak_days=3, last_log_day=date(2026, 3, 5), settled_on=date(2026, 3, 4)
    )
    outcome = register_log(pet, {date(2026, 3, 5)}, [], date(2026, 3, 4), 0)
    assert outcome.pet.last_log_day == date(2026, 3, 5)
    assert outcome.pet.streak_days == 3
    assert outcome.pet.lives == 2


def test_pet_state_rejects_negative_values() -> None:
    with pytest.raises(ValueError, match="lives"):
        PetState(lives=-1, streak_days=0, last_log_day=None, settled_on=date(2026, 1, 1))
    with pytest.raises(ValueError, match="streak"):
        PetState(lives=1, streak_days=-1, last_log_day=None, settled_on=date(2026, 1, 1))


def test_default_rules_match_pet_rules_doc() -> None:
    assert DEFAULT_RULES.starting_lives == 2
    assert DEFAULT_RULES.max_lives == 4
    assert DEFAULT_RULES.streak_days_per_life == 7
    assert DEFAULT_RULES.lives_after_wake_up == 1
    assert DEFAULT_RULES.points_per_meal == 10
    assert DEFAULT_RULES.max_scored_meals_per_day == 3
    assert DEFAULT_RULES.wake_up_points == 5
    assert DEFAULT_RULES.free_daily_photo_limit == 2


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_lives": 0},
        {"starting_lives": 5},
        {"starting_lives": 0},
        {"lives_after_wake_up": 0},
        {"streak_days_per_life": 0},
        {"points_per_meal": 0},
        {"wake_up_points": -5},
        {"max_scored_meals_per_day": -1},
        {"free_daily_photo_limit": -1},
        {"premium_daily_photo_limit": -1},
    ],
)
def test_config_rejects_invalid_values(kwargs: dict[str, int]) -> None:
    with pytest.raises(ValueError):  # noqa: PT011
        PetRulesConfig(**kwargs)
