"""Mood precedence, points rules and the daily AI photo limit."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest

from app.domain import (
    Mood,
    PetRulesConfig,
    PetState,
    Plan,
    PointsAward,
    PointsReason,
    can_analyze_photo,
    compute_mood,
    daily_photo_limit,
    meal_points,
    points_for_log,
    remaining_photos,
    settle,
)
from tests.unit.fakes import SAO_PAULO, UTC, FakeClock, FakeUser, at

TODAY = date(2026, 3, 10)
NOW = datetime(2026, 3, 10, 15, 0, tzinfo=UTC)


def _pet(lives: int, logged_today: bool, rest_until: datetime | None = None) -> PetState:
    return PetState(
        lives=lives,
        streak_days=1 if logged_today else 0,
        last_log_day=TODAY if logged_today else TODAY - timedelta(days=1),
        settled_on=TODAY - timedelta(days=1),
        rest_until=rest_until,
    )


@pytest.mark.parametrize(
    ("lives", "logged_today", "rest_until", "expected"),
    [
        (0, False, NOW + timedelta(hours=1), Mood.PAUSED),
        (3, True, NOW + timedelta(days=2), Mood.PAUSED),
        (0, False, None, Mood.FAINTED),
        (0, False, NOW, Mood.FAINTED),  # rest_until == now is no longer in the future
        (1, True, None, Mood.HAPPY),
        (4, True, NOW - timedelta(days=1), Mood.HAPPY),
        (1, False, None, Mood.SLEEPY),
        (2, False, None, Mood.TIRED),
        (4, False, None, Mood.TIRED),
    ],
)
def test_mood_precedence(
    lives: int, logged_today: bool, rest_until: datetime | None, expected: Mood
) -> None:
    assert compute_mood(_pet(lives, logged_today, rest_until), TODAY, NOW) is expected


def test_mood_requires_aware_now() -> None:
    with pytest.raises(ValueError, match="aware"):
        compute_mood(_pet(2, False), TODAY, datetime(2026, 3, 10, 15, 0))  # noqa: DTZ001


def test_mood_values_match_api_contract() -> None:
    assert {m.value for m in Mood} == {"paused", "fainted", "happy", "sleepy", "tired"}


def test_meal_points_cap_at_three_scored_meals_per_day() -> None:
    assert [meal_points(n) for n in range(5)] == [10, 10, 10, 0, 0]


def test_points_for_log_never_emits_zero_or_negative_rows() -> None:
    assert points_for_log(3, woke_up=False) == ()
    assert points_for_log(3, woke_up=True) == (PointsAward(PointsReason.WAKE_UP, 5),)
    assert points_for_log(0, woke_up=True) == (
        PointsAward(PointsReason.MEAL_LOGGED, 10),
        PointsAward(PointsReason.WAKE_UP, 5),
    )


def test_points_awards_are_always_positive() -> None:
    with pytest.raises(ValueError, match="positive"):
        PointsAward(PointsReason.MEAL_LOGGED, 0)
    with pytest.raises(ValueError, match="negative"):
        meal_points(-1)


def test_four_logs_in_a_day_score_thirty_points_and_reset_next_day() -> None:
    user = FakeUser(FakeClock(at(SAO_PAULO, 2026, 3, 2)), SAO_PAULO)
    for _ in range(4):
        user.log()
    assert user.total_points() == 30
    user.next_day()
    user.log()
    assert user.total_points() == 40


def test_points_tunable_through_config() -> None:
    config = PetRulesConfig(points_per_meal=7, max_scored_meals_per_day=1)
    assert meal_points(0, config) == 7
    assert meal_points(1, config) == 0


def test_free_plan_allows_two_photos_per_day() -> None:
    assert daily_photo_limit(Plan.FREE) == 2
    assert [can_analyze_photo(Plan.FREE, n) for n in range(4)] == [True, True, False, False]
    assert remaining_photos(Plan.FREE, 0) == 2
    assert remaining_photos(Plan.FREE, 5) == 0


def test_premium_limit_falls_back_to_free_until_decided() -> None:
    assert daily_photo_limit(Plan.PREMIUM) == 2
    config = PetRulesConfig(premium_daily_photo_limit=10)
    assert daily_photo_limit(Plan.PREMIUM, config) == 10
    assert daily_photo_limit(Plan.FREE, config) == 2


def test_limit_rejects_negative_counts() -> None:
    with pytest.raises(ValueError, match="negative"):
        remaining_photos(Plan.FREE, -1)


def test_hitting_daily_limit_never_changes_lives() -> None:
    user = FakeUser(FakeClock(at(SAO_PAULO, 2026, 3, 2, 9)), SAO_PAULO)
    analyses = 0
    for _ in range(2):
        assert can_analyze_photo(Plan.FREE, analyses)
        user.log()
        analyses += 1
    before = user.read()
    for _ in range(5):  # blocked attempts: rejected before any pet change
        assert not can_analyze_photo(Plan.FREE, analyses)
        assert settle(user.pet, user.logged_days, user.pause_windows, user.today()) == before
    assert user.read() == before
    assert user.mood() is Mood.HAPPY
    # The day already has a log, so the next day costs nothing either.
    user.next_day()
    assert user.read().lives == before.lives


def test_limit_reached_on_first_photos_does_not_cost_a_life_if_logged() -> None:
    user = FakeUser(FakeClock(at(SAO_PAULO, 2026, 3, 2, 9)), SAO_PAULO)
    user.log()
    user.next_day()
    user.log()
    user.log()
    assert not can_analyze_photo(Plan.FREE, 2)
    user.next_day()
    assert user.read().lives == 2
