"""Tunable game values from docs/domain/pet-rules.md, kept in one immutable config object.

Every other domain module reads its numbers from `PetRulesConfig`; nothing is hard-coded elsewhere.
Use `DEFAULT_RULES` unless a test or an experiment needs different values.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PetRulesConfig:
    """Game rule values. Values marked tunable in pet-rules.md live here."""

    starting_lives: int = 2
    max_lives: int = 4
    streak_days_per_life: int = 7
    lives_after_wake_up: int = 1
    points_per_meal: int = 10
    max_scored_meals_per_day: int = 3
    wake_up_points: int = 5
    # Levels: experience is the points total; one level per this many points.
    points_per_level: int = 100
    free_daily_photo_limit: int = 2
    # Not decided yet (pet-rules.md: "ask before implementing"). While None, Premium uses the
    # Free limit so no unapproved number reaches production.
    premium_daily_photo_limit: int | None = None
    # RF-98 risk pattern: consecutive local days without a log before `support_hint` is raised.
    # Threshold not decided by the product owner. While None the rule is disabled.
    risk_pattern_days: int | None = None

    def __post_init__(self) -> None:
        if self.max_lives < 1:
            raise ValueError("max_lives must be at least 1")
        if not 0 < self.starting_lives <= self.max_lives:
            raise ValueError("starting_lives must be between 1 and max_lives")
        if not 0 < self.lives_after_wake_up <= self.max_lives:
            raise ValueError("lives_after_wake_up must be between 1 and max_lives")
        if self.streak_days_per_life < 1:
            raise ValueError("streak_days_per_life must be at least 1")
        if self.points_per_meal <= 0 or self.wake_up_points <= 0:
            raise ValueError("points are always positive")
        if self.points_per_level < 1:
            raise ValueError("points_per_level must be at least 1")
        if self.max_scored_meals_per_day < 0:
            raise ValueError("max_scored_meals_per_day must not be negative")
        if self.free_daily_photo_limit < 0:
            raise ValueError("free_daily_photo_limit must not be negative")
        if self.premium_daily_photo_limit is not None and self.premium_daily_photo_limit < 0:
            raise ValueError("premium_daily_photo_limit must not be negative")
        if self.risk_pattern_days is not None and self.risk_pattern_days < 1:
            raise ValueError("risk_pattern_days must be at least 1")


DEFAULT_RULES = PetRulesConfig()
