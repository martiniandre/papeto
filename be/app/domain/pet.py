"""Pet lives and streak: lazy settlement of missed days and the transition applied on a new log.

`settle` replaces any cron job: call it on every read and every write with the user's local
"today". It is pure and idempotent. `register_log` applies pet-rules.md "On a new log".
Dates are always passed in; this module never reads the clock.
"""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from enum import StrEnum

from app.domain.config import DEFAULT_RULES, PetRulesConfig
from app.domain.local_days import PauseWindow, is_paused_on
from app.domain.points import PointsAward, points_for_log

_ONE_DAY = timedelta(days=1)


class PetEvent(StrEnum):
    """One-shot events returned to the app so it can play animations."""

    WAKE_UP = "wake_up"
    LIFE_LOST = "life_lost"
    CELEBRATE = "celebrate"


@dataclass(frozen=True, slots=True)
class PetState:
    """Stored pet game state. Mood is never stored; see `app.domain.mood`.

    `settled_on` is the last local date for which missed days were applied.
    `rest_until` is the aware instant a pause ends (None when never paused).
    """

    lives: int
    streak_days: int
    last_log_day: date | None
    settled_on: date
    rest_until: datetime | None = None

    def __post_init__(self) -> None:
        if self.lives < 0:
            raise ValueError("lives must not be negative")
        if self.streak_days < 0:
            raise ValueError("streak_days must not be negative")
        if self.rest_until is not None and self.rest_until.utcoffset() is None:
            raise ValueError("rest_until must be timezone-aware")


@dataclass(frozen=True, slots=True)
class LogOutcome:
    """Result of `register_log`: new state, events to return and points rows to append."""

    pet: PetState
    events: tuple[PetEvent, ...]
    points: tuple[PointsAward, ...]


def new_pet(today_local: date, config: PetRulesConfig = DEFAULT_RULES) -> PetState:
    """A freshly created pet. The creation day is the first day that can be missed."""
    return PetState(
        lives=config.starting_lives,
        streak_days=0,
        last_log_day=None,
        settled_on=today_local - _ONE_DAY,
    )


def settle(
    pet: PetState,
    logged_days: Collection[date],
    pause_windows: Collection[PauseWindow],
    today_local: date,
) -> PetState:
    """Apply missed days from `settled_on + 1` to `today_local - 1` (inclusive).

    A day with a log or covered by a pause costs nothing. Every other day costs one life (floored
    at 0) and resets the streak. `pet.last_log_day` always counts as a logged day. Settling never
    moves `settled_on` backwards, so calling it again with the same or an earlier date is a no-op.
    """
    target = today_local - _ONE_DAY
    if target <= pet.settled_on:
        return pet

    lives = pet.lives
    streak_days = pet.streak_days
    day = pet.settled_on + _ONE_DAY
    while day <= target:
        if lives == 0 and streak_days == 0:
            break  # Nothing left to lose; the remaining days cannot change the state.
        missed = (
            day not in logged_days
            and day != pet.last_log_day
            and not is_paused_on(day, pause_windows)
        )
        if missed:
            lives = max(0, lives - 1)
            streak_days = 0
        day += _ONE_DAY

    return replace(pet, lives=lives, streak_days=streak_days, settled_on=target)


def _streak_continues(
    last_log_day: date | None, log_day: date, pause_windows: Collection[PauseWindow]
) -> bool:
    if last_log_day is None or last_log_day >= log_day:
        return False
    day = last_log_day + _ONE_DAY
    while day < log_day:
        if not is_paused_on(day, pause_windows):
            return False
        day += _ONE_DAY
    return True


def register_log(
    pet: PetState,
    logged_days: Collection[date],
    pause_windows: Collection[PauseWindow],
    log_day: date,
    scored_meals_today: int,
    config: PetRulesConfig = DEFAULT_RULES,
) -> LogOutcome:
    """Apply a successful meal log on local day `log_day`.

    `scored_meals_today` is how many meals already earned meal points on `log_day` before this one.
    Only successful analyses are logs; failed ones must not reach this function.
    """
    settled = settle(pet, logged_days, pause_windows, log_day)
    lives = settled.lives
    streak_days = settled.streak_days
    last_log_day = settled.last_log_day
    events: list[PetEvent] = []

    woke_up = lives == 0
    if woke_up:
        lives = config.lives_after_wake_up
        events.append(PetEvent.WAKE_UP)

    if last_log_day is None or last_log_day < log_day:
        if _streak_continues(last_log_day, log_day, pause_windows):
            streak_days += 1
        else:
            streak_days = 1
        if streak_days % config.streak_days_per_life == 0 and lives < config.max_lives:
            lives += 1
            events.append(PetEvent.CELEBRATE)
        last_log_day = log_day
    # A log on a day before `last_log_day` (timezone moved backwards) keeps the later day.

    new_state = replace(settled, lives=lives, streak_days=streak_days, last_log_day=last_log_day)
    return LogOutcome(
        pet=new_state,
        events=tuple(events),
        points=points_for_log(scored_meals_today, woke_up, config),
    )


def read_events(last_seen_lives: int | None, current_lives: int) -> tuple[PetEvent, ...]:
    """Events for a read: `life_lost` when lives dropped since the client's last seen value."""
    if last_seen_lives is not None and current_lives < last_seen_lives:
        return (PetEvent.LIFE_LOST,)
    return ()
