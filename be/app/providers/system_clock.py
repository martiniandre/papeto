"""Real Clock and IdGenerator adapters."""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)  # noqa: TID251 - the only place allowed to read the system time

    def today(self, timezone: ZoneInfo) -> date:
        return self.now().astimezone(timezone).date()


class UuidGenerator:
    def new_id(self) -> UUID:
        return uuid4()
