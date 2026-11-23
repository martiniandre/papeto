"""Pure game rules for the pet (docs/domain/pet-rules.md). No framework, DB or provider imports.

Public API re-exported here so services import from `app.domain` only.
"""

from app.domain.config import DEFAULT_RULES, PetRulesConfig
from app.domain.limits import Plan, can_analyze_photo, daily_photo_limit, remaining_photos
from app.domain.local_days import (
    PauseWindow,
    is_paused_on,
    local_day,
    local_day_start,
    pause_window_from_instants,
)
from app.domain.mood import Mood, compute_mood, is_paused
from app.domain.pet import (
    LogOutcome,
    PetEvent,
    PetState,
    new_pet,
    read_events,
    register_log,
    settle,
)
from app.domain.points import PointsAward, PointsReason, meal_points, points_for_log

__all__ = [
    "DEFAULT_RULES",
    "LogOutcome",
    "Mood",
    "PauseWindow",
    "PetEvent",
    "PetRulesConfig",
    "PetState",
    "Plan",
    "PointsAward",
    "PointsReason",
    "can_analyze_photo",
    "compute_mood",
    "daily_photo_limit",
    "is_paused",
    "is_paused_on",
    "local_day",
    "local_day_start",
    "meal_points",
    "new_pet",
    "pause_window_from_instants",
    "points_for_log",
    "read_events",
    "register_log",
    "remaining_photos",
    "settle",
]
