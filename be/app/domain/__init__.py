"""Pure game rules for the pet (docs/domain/pet-rules.md). No framework, DB or provider imports.

Public API re-exported here so services import from `app.domain` only.
"""

from app.domain.config import DEFAULT_RULES, PetRulesConfig
from app.domain.events import ProductEvent
from app.domain.food_groups import FOOD_GROUPS, known_food_groups
from app.domain.limits import Plan, can_analyze_photo, daily_photo_limit, remaining_photos
from app.domain.local_days import (
    PauseWindow,
    is_paused_on,
    local_day,
    local_day_start,
    pause_window_from_instants,
)
from app.domain.mood import Mood, compute_mood, is_paused
from app.domain.notifications import (
    DEFAULT_PREFS,
    MAX_NOTICES_PER_DAY,
    NOTICE_COPY,
    NoticeCopy,
    NoticeKind,
    NotificationPrefs,
    decide_notice,
    in_quiet_hours,
    pick_copy,
)
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
from app.domain.risk import needs_support_hint
from app.domain.tips import TIP_COPY, missing_food_groups, pick_tip

__all__ = [
    "DEFAULT_PREFS",
    "DEFAULT_RULES",
    "FOOD_GROUPS",
    "MAX_NOTICES_PER_DAY",
    "NOTICE_COPY",
    "TIP_COPY",
    "LogOutcome",
    "Mood",
    "NoticeCopy",
    "NoticeKind",
    "NotificationPrefs",
    "PauseWindow",
    "PetEvent",
    "PetRulesConfig",
    "PetState",
    "Plan",
    "PointsAward",
    "PointsReason",
    "ProductEvent",
    "can_analyze_photo",
    "compute_mood",
    "daily_photo_limit",
    "decide_notice",
    "in_quiet_hours",
    "is_paused",
    "is_paused_on",
    "known_food_groups",
    "local_day",
    "local_day_start",
    "meal_points",
    "missing_food_groups",
    "needs_support_hint",
    "new_pet",
    "pause_window_from_instants",
    "pick_copy",
    "pick_tip",
    "points_for_log",
    "read_events",
    "register_log",
    "remaining_photos",
    "settle",
]
