"""Notice rules (RF-40 to RF-42): mood, preferences, quiet hours, per-episode and per-day caps."""

from __future__ import annotations

import re
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.domain import (
    DEFAULT_PREFS,
    MAX_NOTICES_PER_DAY,
    NOTICE_COPY,
    Mood,
    NoticeKind,
    NotificationPrefs,
    decide_notice,
    in_quiet_hours,
    pick_copy,
)
from tests.unit.fakes import NEW_YORK, SAO_PAULO, FakeClock

NOON_UTC = datetime(2026, 3, 10, 15, 0, tzinfo=UTC)  # 12:00 in Sao Paulo (UTC-3)


def _decide(
    mood: Mood,
    *,
    now: datetime = NOON_UTC,
    tz: ZoneInfo = SAO_PAULO,
    prefs: NotificationPrefs = DEFAULT_PREFS,
    sent_today: int = 0,
    sent_in_episode: frozenset[NoticeKind] = frozenset(),
) -> NoticeKind | None:
    local_now = FakeClock(now).now().astimezone(tz)
    return decide_notice(
        mood=mood,
        prefs=prefs,
        local_now=local_now,
        sent_today=sent_today,
        sent_in_episode=sent_in_episode,
    )


def test_tired_and_sleepy_notify() -> None:
    assert _decide(Mood.TIRED) is NoticeKind.TIRED
    assert _decide(Mood.SLEEPY) is NoticeKind.SLEEPY


@pytest.mark.parametrize("mood", [Mood.HAPPY, Mood.PAUSED, Mood.FAINTED])
def test_other_moods_never_notify(mood: Mood) -> None:
    assert _decide(mood) is None


def test_each_notice_can_be_switched_off() -> None:
    off_meal = NotificationPrefs(meal_reminder=False)
    off_sleepy = NotificationPrefs(sleepy_notice=False)
    assert _decide(Mood.TIRED, prefs=off_meal) is None
    assert _decide(Mood.SLEEPY, prefs=off_meal) is NoticeKind.SLEEPY
    assert _decide(Mood.SLEEPY, prefs=off_sleepy) is None
    assert _decide(Mood.TIRED, prefs=off_sleepy) is NoticeKind.TIRED


def test_weekly_summary_flag_does_not_affect_meal_notices() -> None:
    assert _decide(Mood.TIRED, prefs=NotificationPrefs(weekly_summary=False)) is NoticeKind.TIRED


def test_one_tired_and_one_sleepy_per_episode() -> None:
    assert _decide(Mood.TIRED, sent_in_episode=frozenset({NoticeKind.TIRED})) is None
    # The tired notice was already sent; becoming sleepy still earns its own notice.
    assert _decide(Mood.SLEEPY, sent_in_episode=frozenset({NoticeKind.TIRED})) is NoticeKind.SLEEPY
    assert _decide(Mood.SLEEPY, sent_in_episode=frozenset(NoticeKind)) is None


def test_at_most_two_notices_per_local_day() -> None:
    assert MAX_NOTICES_PER_DAY == 2
    assert _decide(Mood.TIRED, sent_today=1) is NoticeKind.TIRED
    assert _decide(Mood.TIRED, sent_today=2) is None
    assert _decide(Mood.SLEEPY, sent_today=3) is None


# --- quiet hours -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("local", "expected"),
    [
        (time(21, 59), False),
        (time(22, 0), True),
        (time(23, 59), True),
        (time(0, 0), True),
        (time(7, 59), True),
        (time(8, 0), False),
        (time(12, 0), False),
    ],
)
def test_default_quiet_hours_cross_midnight(local: time, expected: bool) -> None:
    assert in_quiet_hours(local, time(22, 0), time(8, 0)) is expected


def test_quiet_hours_same_day_window_and_empty_window() -> None:
    assert in_quiet_hours(time(13, 0), time(12, 0), time(14, 0))
    assert not in_quiet_hours(time(14, 0), time(12, 0), time(14, 0))
    assert not in_quiet_hours(time(3, 0), time(9, 0), time(9, 0))  # start == end: none


def test_quiet_hours_use_the_users_local_time_not_utc() -> None:
    # 01:30 UTC is 22:30 in Sao Paulo (quiet) but 21:30 the day before in New York (EDT).
    at = datetime(2026, 3, 10, 1, 30, tzinfo=UTC)
    assert _decide(Mood.TIRED, now=at, tz=SAO_PAULO) is None  # 22:30 local
    assert _decide(Mood.TIRED, now=at, tz=NEW_YORK) is NoticeKind.TIRED  # 21:30 local (EDT)


def test_quiet_hours_follow_dst_changes() -> None:
    # New York springs forward on 2026-03-08: 12:30 UTC is 08:30 EDT (allowed), but would have
    # been 07:30 EST (quiet) a day earlier at the same UTC instant.
    after = datetime(2026, 3, 8, 12, 30, tzinfo=UTC)
    before = datetime(2026, 3, 7, 12, 30, tzinfo=UTC)
    assert _decide(Mood.TIRED, now=after, tz=NEW_YORK) is NoticeKind.TIRED
    assert _decide(Mood.TIRED, now=before, tz=NEW_YORK) is None


def test_custom_quiet_hours() -> None:
    prefs = NotificationPrefs(quiet_hours_start=time(12, 0), quiet_hours_end=time(13, 0))
    assert _decide(Mood.TIRED, prefs=prefs) is None  # 12:00 local
    later = NOON_UTC + timedelta(hours=1)
    assert _decide(Mood.TIRED, prefs=prefs, now=later) is NoticeKind.TIRED


def test_quiet_hours_must_be_naive() -> None:
    with pytest.raises(ValueError, match="naive"):
        NotificationPrefs(quiet_hours_start=time(22, 0, tzinfo=UTC))


# --- copy ------------------------------------------------------------------------------------

FORBIDDEN = re.compile(
    r"caloria|kcal|peso|gordur|magr|dieta|corpo|imc|certo|errad|saud[aá]vel|culpa|comer|aliment",
    re.IGNORECASE,
)


def test_copy_is_fixed_kind_and_free_of_forbidden_words() -> None:
    assert set(NOTICE_COPY) == set(NoticeKind)
    for options in NOTICE_COPY.values():
        assert options
        for copy in options:
            assert not FORBIDDEN.search(copy.title + " " + copy.body), copy
            assert len(copy.title) <= 40
            assert len(copy.body) <= 120


def test_pick_copy_is_deterministic_and_covers_every_option() -> None:
    day = date(2026, 3, 10)
    assert pick_copy(NoticeKind.TIRED, day) == pick_copy(NoticeKind.TIRED, day)
    picked = {pick_copy(NoticeKind.SLEEPY, day + timedelta(days=i)) for i in range(10)}
    assert picked == set(NOTICE_COPY[NoticeKind.SLEEPY])
