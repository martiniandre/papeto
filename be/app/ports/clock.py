"""Clock port. Domain and services never read the system time directly."""

from __future__ import annotations

from datetime import date, datetime
from typing import Protocol
from zoneinfo import ZoneInfo


class Clock(Protocol):
    def now(self) -> datetime:
        """Current instant, timezone-aware, in UTC."""
        ...

    def today(self, timezone: ZoneInfo) -> date:
        """Current local calendar day in `timezone`."""
        ...
