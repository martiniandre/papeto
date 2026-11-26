"""Test doubles for domain tests: a fake Clock and a small in-memory user that drives the rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.domain import (
    DEFAULT_RULES,
    LogOutcome,
    Mood,
    PauseWindow,
    PetEvent,
    PetRulesConfig,
    PetState,
    PointsAward,
    compute_mood,
    local_day,
    new_pet,
    register_log,
    settle,
)

UTC = ZoneInfo("UTC")
SAO_PAULO = ZoneInfo("America/Sao_Paulo")
NEW_YORK = ZoneInfo("America/New_York")


class FakeClock:
    """Deterministic clock. Holds an aware UTC instant that tests move forward explicitly."""

    def __init__(self, now: datetime) -> None:
        if now.utcoffset() is None:
            raise ValueError("FakeClock needs an aware datetime")
        self._now = now.astimezone(UTC)

    def now(self) -> datetime:
        return self._now

    def today(self, timezone: ZoneInfo) -> date:
        return local_day(self._now, timezone)

    def set(self, now: datetime) -> None:
        if now.utcoffset() is None:
            raise ValueError("FakeClock needs an aware datetime")
        self._now = now.astimezone(UTC)

    def advance(self, delta: timedelta) -> None:
        self._now += delta


def at(
    timezone: ZoneInfo, year: int, month: int, day: int, hour: int = 12, minute: int = 0
) -> datetime:
    """Aware local wall-clock instant."""
    return datetime(year, month, day, hour, minute, tzinfo=timezone)


@dataclass
class FakeUser:
    """In-memory stand-in for the service layer: keeps pet, logs, pauses and points rows."""

    clock: FakeClock
    timezone: ZoneInfo
    config: PetRulesConfig = DEFAULT_RULES
    pet: PetState = field(init=False)
    logged_days: set[date] = field(default_factory=set)
    pause_windows: list[PauseWindow] = field(default_factory=list)
    points: list[PointsAward] = field(default_factory=list)
    scored_meals: dict[date, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.pet = new_pet(self.today(), self.config)

    def today(self) -> date:
        return self.clock.today(self.timezone)

    def read(self) -> PetState:
        self.pet = settle(self.pet, self.logged_days, self.pause_windows, self.today())
        return self.pet

    def mood(self) -> Mood:
        return compute_mood(self.read(), self.today(), self.clock.now())

    def log(self) -> LogOutcome:
        day = self.today()
        scored = self.scored_meals.get(day, 0)
        outcome = register_log(
            self.pet, self.logged_days, self.pause_windows, day, scored, self.config
        )
        self.pet = outcome.pet
        self.logged_days.add(day)
        self.points.extend(outcome.points)
        if any(award.reason == "meal_logged" for award in outcome.points):
            self.scored_meals[day] = scored + 1
        return outcome

    def total_points(self) -> int:
        return sum(award.amount for award in self.points)

    def next_day(self, days: int = 1) -> None:
        self.clock.advance(timedelta(days=days))

    def log_daily(self, days: int) -> list[tuple[PetEvent, ...]]:
        """Log once today, then once on each of the following `days - 1` days."""
        events: list[tuple[PetEvent, ...]] = []
        for index in range(days):
            if index:
                self.next_day()
            events.append(self.log().events)
        return events
