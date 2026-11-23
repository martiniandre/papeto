"""Points rules: +10 per logged meal (at most 3 scored meals per local day) and +5 per wake-up.

Points are append-only and always positive. Correcting or deleting a meal never changes points, and
losing lives or fainting never removes them, so there is deliberately no function that subtracts.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.config import DEFAULT_RULES, PetRulesConfig


class PointsReason(StrEnum):
    MEAL_LOGGED = "meal_logged"
    WAKE_UP = "wake_up"


@dataclass(frozen=True, slots=True)
class PointsAward:
    """One `points_event` row to append. `amount` is always > 0."""

    reason: PointsReason
    amount: int

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise ValueError("points awards are always positive")


def meal_points(scored_meals_today: int, config: PetRulesConfig = DEFAULT_RULES) -> int:
    """Points for a new log, given how many meals already scored points on this local day."""
    if scored_meals_today < 0:
        raise ValueError("scored_meals_today must not be negative")
    if scored_meals_today >= config.max_scored_meals_per_day:
        return 0
    return config.points_per_meal


def points_for_log(
    scored_meals_today: int, woke_up: bool, config: PetRulesConfig = DEFAULT_RULES
) -> tuple[PointsAward, ...]:
    """Awards to append for a new log. Zero-point outcomes produce no row."""
    awards: list[PointsAward] = []
    meal = meal_points(scored_meals_today, config)
    if meal > 0:
        awards.append(PointsAward(PointsReason.MEAL_LOGGED, meal))
    if woke_up:
        awards.append(PointsAward(PointsReason.WAKE_UP, config.wake_up_points))
    return tuple(awards)
