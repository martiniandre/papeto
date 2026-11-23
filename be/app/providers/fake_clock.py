"""Fake Clock and IdGenerator: deterministic, for tests and local runs."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo


class FakeClock:
    def __init__(self, now: datetime) -> None:
        if now.utcoffset() is None:
            raise ValueError("FakeClock needs an aware datetime")
        self._now = now.astimezone(UTC)

    def now(self) -> datetime:
        return self._now

    def today(self, timezone: ZoneInfo) -> date:
        return self._now.astimezone(timezone).date()

    def set(self, now: datetime) -> None:
        if now.utcoffset() is None:
            raise ValueError("FakeClock needs an aware datetime")
        self._now = now.astimezone(UTC)

    def advance(self, delta: timedelta) -> None:
        self._now += delta


class SequentialIdGenerator:
    """Ids 00000000-0000-0000-0000-000000000001, ...0002, and so on."""

    def __init__(self, start: int = 1) -> None:
        self._next = start

    def new_id(self) -> UUID:
        value = UUID(int=self._next)
        self._next += 1
        return value
