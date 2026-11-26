"""RF-98 risk pattern: many days in a row without logs (mechanism only, disabled by default).

The threshold is `PetRulesConfig.risk_pattern_days` and is NOT decided by the product owner, so it
defaults to None (disabled). When enabled the API returns `support_hint: true` and the app shows a
kind message with the CVV 188 path. It is never a punishment: no life, point or streak changes.
"""

from __future__ import annotations

from collections.abc import Collection
from datetime import date, timedelta

from app.domain.config import DEFAULT_RULES, PetRulesConfig
from app.domain.local_days import PauseWindow, is_paused_on


def needs_support_hint(
    logged_days: Collection[date],
    pause_windows: Collection[PauseWindow],
    today_local: date,
    first_day: date,
    config: PetRulesConfig = DEFAULT_RULES,
) -> bool:
    """True when the last N completed local days (before today) had no log and no pause.

    `first_day` is the local day the pet was created; days before it never count. A log today
    clears the hint. Disabled (always False) while `config.risk_pattern_days` is None.
    """
    threshold = config.risk_pattern_days
    if threshold is None or today_local in logged_days:
        return False
    for offset in range(1, threshold + 1):
        day = today_local - timedelta(days=offset)
        if day < first_day or day in logged_days or is_paused_on(day, pause_windows):
            return False
    return True
