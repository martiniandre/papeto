"""Local-day boundaries in America/Sao_Paulo (no DST) and America/New_York (DST)."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.domain import (
    Mood,
    PauseWindow,
    local_day,
    local_day_start,
    pause_window_from_instants,
)
from tests.unit.fakes import NEW_YORK, SAO_PAULO, UTC, FakeClock, FakeUser, at


@pytest.mark.parametrize(
    ("instant_utc", "expected"),
    [
        # Sao Paulo is UTC-3 all year.
        (datetime(2026, 3, 11, 2, 59, tzinfo=UTC), date(2026, 3, 10)),  # 23:59 local
        (datetime(2026, 3, 11, 3, 1, tzinfo=UTC), date(2026, 3, 11)),  # 00:01 local
        (
            datetime(2026, 3, 11, 3, 0, tzinfo=UTC),
            date(2026, 3, 11),
        ),  # midnight belongs to the new day
    ],
)
def test_sao_paulo_local_day(instant_utc: datetime, expected: date) -> None:
    assert local_day(instant_utc, SAO_PAULO) == expected


@pytest.mark.parametrize(
    ("instant_utc", "expected"),
    [
        # Before spring forward (EST, UTC-5): 2026-03-07 23:59 local.
        (datetime(2026, 3, 8, 4, 59, tzinfo=UTC), date(2026, 3, 7)),
        (datetime(2026, 3, 8, 5, 1, tzinfo=UTC), date(2026, 3, 8)),
        # 2026-03-08 is a 23 h day; it ends at 04:00 UTC on 03-09 (EDT, UTC-4).
        (datetime(2026, 3, 9, 3, 59, tzinfo=UTC), date(2026, 3, 8)),
        (datetime(2026, 3, 9, 4, 1, tzinfo=UTC), date(2026, 3, 9)),
        # 2026-11-01 is a 25 h day: starts 04:00 UTC (EDT), ends 05:00 UTC on 11-02 (EST).
        (datetime(2026, 11, 1, 3, 59, tzinfo=UTC), date(2026, 10, 31)),
        (datetime(2026, 11, 1, 4, 1, tzinfo=UTC), date(2026, 11, 1)),
        (datetime(2026, 11, 2, 4, 59, tzinfo=UTC), date(2026, 11, 1)),  # 23:59 EST
        (datetime(2026, 11, 2, 5, 1, tzinfo=UTC), date(2026, 11, 2)),  # 00:01 EST
    ],
)
def test_new_york_local_day_across_dst(instant_utc: datetime, expected: date) -> None:
    assert local_day(instant_utc, NEW_YORK) == expected


def test_local_day_requires_aware_instant() -> None:
    with pytest.raises(ValueError, match="aware"):
        local_day(datetime(2026, 3, 10, 12, 0), SAO_PAULO)  # noqa: DTZ001


def test_local_day_start_accounts_for_dst() -> None:
    assert local_day_start(date(2026, 3, 9), NEW_YORK).astimezone(UTC) == datetime(
        2026, 3, 9, 4, 0, tzinfo=UTC
    )
    assert local_day_start(date(2026, 11, 2), NEW_YORK).astimezone(UTC) == datetime(
        2026, 11, 2, 5, 0, tzinfo=UTC
    )


@pytest.mark.parametrize(
    ("timezone", "day"),
    [
        (SAO_PAULO, date(2026, 3, 10)),
        (NEW_YORK, date(2026, 3, 7)),  # 23:59 EST, then 00:01 on the 23 h day
        (NEW_YORK, date(2026, 10, 31)),  # 23:59 EDT, then 00:01 on the 25 h day
        (NEW_YORK, date(2026, 11, 1)),  # 23:59 EST on the 25 h day
    ],
)
def test_log_at_2359_and_0001_are_consecutive_days(timezone: ZoneInfo, day: date) -> None:
    tz = timezone
    clock = FakeClock(at(tz, day.year, day.month, day.day, 8))
    user = FakeUser(clock, tz)

    clock.set(at(tz, day.year, day.month, day.day, 23, 59))
    first = user.log()
    assert first.pet.last_log_day == day

    clock.advance(timedelta(minutes=2))  # 00:01 local on the next day
    assert user.today() == day + timedelta(days=1)
    second = user.log()

    assert second.pet.last_log_day == day + timedelta(days=1)
    assert second.pet.streak_days == 2
    assert second.pet.lives == 2
    assert user.mood() is Mood.HAPPY


@pytest.mark.parametrize("zone", [SAO_PAULO, NEW_YORK])
def test_log_at_0001_after_missing_whole_day_costs_a_life(zone: ZoneInfo) -> None:
    clock = FakeClock(at(zone, 2026, 3, 7, 23, 59))
    user = FakeUser(clock, zone)
    user.log()  # 2026-03-07 23:59 local
    clock.set(at(zone, 2026, 3, 9, 0, 1))  # skips 2026-03-08 (DST day in New York)
    outcome = user.log()
    assert outcome.pet.lives == 1
    assert outcome.pet.streak_days == 1


def test_new_york_day_not_over_until_local_midnight_after_spring_forward() -> None:
    clock = FakeClock(at(NEW_YORK, 2026, 3, 7, 12))
    user = FakeUser(clock, NEW_YORK)
    user.log()
    # 23:30 local on 2026-03-08 (the 23 h day): still the same local day, nothing missed yet.
    clock.set(at(NEW_YORK, 2026, 3, 8, 23, 30))
    assert user.today() == date(2026, 3, 8)
    assert user.read().lives == 2
    user.log()
    clock.set(at(NEW_YORK, 2026, 3, 9, 0, 1))
    assert user.read().lives == 2
    assert user.pet.streak_days == 2


def test_same_utc_instant_is_different_local_days_per_timezone() -> None:
    instant = datetime(2026, 11, 1, 3, 30, tzinfo=UTC)
    assert local_day(instant, SAO_PAULO) == date(2026, 11, 1)  # 00:30 in Sao Paulo
    assert local_day(instant, NEW_YORK) == date(2026, 10, 31)  # 23:30 in New York


def test_pause_window_from_instants_in_local_days() -> None:
    start = at(NEW_YORK, 2026, 10, 30, 20)
    window = pause_window_from_instants(start, start + timedelta(days=3), NEW_YORK)
    assert window == PauseWindow(date(2026, 10, 30), date(2026, 11, 2))


def test_pause_ending_at_local_midnight_does_not_cover_next_day() -> None:
    start = at(SAO_PAULO, 2026, 3, 10, 9)
    end = at(SAO_PAULO, 2026, 3, 12, 0, 0)
    assert pause_window_from_instants(start, end, SAO_PAULO) == PauseWindow(
        date(2026, 3, 10), date(2026, 3, 11)
    )


def test_empty_pause_returns_none() -> None:
    start = at(SAO_PAULO, 2026, 3, 10, 9)
    assert pause_window_from_instants(start, start, SAO_PAULO) is None


def test_pause_window_rejects_inverted_days() -> None:
    with pytest.raises(ValueError, match="last_day"):
        PauseWindow(date(2026, 3, 10), date(2026, 3, 9))


def test_paused_mood_and_no_loss_across_dst_in_new_york() -> None:
    clock = FakeClock(at(NEW_YORK, 2026, 10, 30, 10))
    user = FakeUser(clock, NEW_YORK)
    user.log()
    rest_until = at(NEW_YORK, 2026, 11, 3, 0, 0)
    window = pause_window_from_instants(clock.now(), rest_until, NEW_YORK)
    assert window is not None
    user.pause_windows.append(window)
    user.pet = replace(user.pet, rest_until=rest_until)
    clock.set(at(NEW_YORK, 2026, 11, 2, 23, 59))
    assert user.mood() is Mood.PAUSED
    clock.set(at(NEW_YORK, 2026, 11, 3, 0, 1))
    assert user.mood() is Mood.TIRED
    assert user.pet.lives == 2
    assert user.pet.streak_days == 1
