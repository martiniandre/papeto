"""Local-day helpers: map UTC instants to the user's local calendar day and pause windows to days.

All instants must be timezone-aware. Day boundaries are local midnight in the user's IANA timezone,
so DST transitions (23- or 25-hour days) are handled by `zoneinfo`.
"""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


def _require_aware(instant: datetime, name: str) -> None:
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


def local_day(instant: datetime, timezone: ZoneInfo) -> date:
    """Return the calendar day of `instant` in `timezone`."""
    _require_aware(instant, "instant")
    return instant.astimezone(timezone).date()


def local_day_start(day: date, timezone: ZoneInfo) -> datetime:
    """Return the aware instant of local midnight that starts `day` in `timezone`."""
    return datetime.combine(day, time.min, tzinfo=timezone)


@dataclass(frozen=True, slots=True)
class PauseWindow:
    """Local days covered by a pause, both ends inclusive."""

    first_day: date
    last_day: date

    def __post_init__(self) -> None:
        if self.last_day < self.first_day:
            raise ValueError("last_day must not be before first_day")

    def covers(self, day: date) -> bool:
        return self.first_day <= day <= self.last_day


def pause_window_from_instants(
    started_at: datetime, rest_until: datetime, timezone: ZoneInfo
) -> PauseWindow | None:
    """Convert a pause `[started_at, rest_until)` into the local days it touches.

    A local day counts as paused if any part of it overlaps the pause. Returns None for an empty
    pause (`rest_until <= started_at`).
    """
    _require_aware(started_at, "started_at")
    _require_aware(rest_until, "rest_until")
    if rest_until <= started_at:
        return None
    first_day = local_day(started_at, timezone)
    last_day = local_day(rest_until, timezone)
    if local_day_start(last_day, timezone) >= rest_until:
        # The pause ends exactly at local midnight: that day is not touched.
        last_day -= timedelta(days=1)
    return PauseWindow(first_day=first_day, last_day=last_day)


def is_paused_on(day: date, pause_windows: Collection[PauseWindow]) -> bool:
    """True if any pause window covers `day`."""
    return any(window.covers(day) for window in pause_windows)
