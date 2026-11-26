"""RF-98 risk pattern: disabled by default; flags N consecutive local days without logs."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from app.domain import DEFAULT_RULES, PauseWindow, PetRulesConfig, needs_support_hint
from tests.unit.fakes import SAO_PAULO, FakeClock, at

CLOCK = FakeClock(at(SAO_PAULO, 2026, 3, 20, 10))
TODAY = CLOCK.today(SAO_PAULO)
CREATED = TODAY - timedelta(days=30)
ENABLED = PetRulesConfig(risk_pattern_days=3)


def _hint(
    logged: set[date],
    config: PetRulesConfig = ENABLED,
    *,
    today: date = TODAY,
    first_day: date = CREATED,
    windows: list[PauseWindow] | None = None,
) -> bool:
    return needs_support_hint(logged, windows or [], today, first_day, config)


def test_disabled_by_default() -> None:
    assert DEFAULT_RULES.risk_pattern_days is None
    assert _hint(set(), DEFAULT_RULES) is False


def test_flags_after_n_missed_days_in_a_row() -> None:
    assert _hint({TODAY - timedelta(days=4)}) is True  # days -1, -2, -3 are empty


def test_one_day_short_is_not_flagged() -> None:
    assert _hint({TODAY - timedelta(days=3)}) is False


def test_a_log_today_clears_it() -> None:
    assert _hint({TODAY}) is False


def test_a_pause_inside_the_window_clears_it() -> None:
    window = PauseWindow(TODAY - timedelta(days=2), TODAY - timedelta(days=2))
    assert _hint(set(), windows=[window]) is False


def test_days_before_the_pet_existed_do_not_count() -> None:
    assert _hint(set(), first_day=TODAY - timedelta(days=2)) is False
    assert _hint(set(), first_day=TODAY - timedelta(days=3)) is True


def test_local_day_follows_the_timezone_not_utc() -> None:
    # 01:00 UTC on the 21st is still the 20th in Sao Paulo (UTC-3): today is the 20th.
    late = FakeClock(datetime(2026, 3, 21, 1, 0, tzinfo=UTC))
    assert late.today(SAO_PAULO) == TODAY
    assert _hint({TODAY - timedelta(days=4)}, today=late.today(SAO_PAULO)) is True


def test_threshold_must_be_positive() -> None:
    with pytest.raises(ValueError, match="risk_pattern_days"):
        PetRulesConfig(risk_pattern_days=0)
