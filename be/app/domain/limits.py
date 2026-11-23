"""Daily AI photo limit per plan.

The count passed in must only include successful analyses on the user's local day: a failed
analysis (unreadable photo, provider error, not food) never consumes the limit. Limits never touch
the pet, so hitting one can never cost a life.
"""

from __future__ import annotations

from enum import StrEnum

from app.domain.config import DEFAULT_RULES, PetRulesConfig


class Plan(StrEnum):
    FREE = "free"
    PREMIUM = "premium"


def daily_photo_limit(plan: Plan, config: PetRulesConfig = DEFAULT_RULES) -> int:
    """AI photos allowed per local day. Premium falls back to Free until its value is decided."""
    if plan is Plan.PREMIUM and config.premium_daily_photo_limit is not None:
        return config.premium_daily_photo_limit
    return config.free_daily_photo_limit


def remaining_photos(
    plan: Plan, successful_analyses_today: int, config: PetRulesConfig = DEFAULT_RULES
) -> int:
    if successful_analyses_today < 0:
        raise ValueError("successful_analyses_today must not be negative")
    return max(0, daily_photo_limit(plan, config) - successful_analyses_today)


def can_analyze_photo(
    plan: Plan, successful_analyses_today: int, config: PetRulesConfig = DEFAULT_RULES
) -> bool:
    """False means the API answers 429 DAILY_LIMIT_REACHED."""
    return remaining_photos(plan, successful_analyses_today, config) > 0
