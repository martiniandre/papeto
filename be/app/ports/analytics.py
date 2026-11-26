"""AnalyticsProvider port. Random analytics id only; the caller applies the user's opt-out."""

from __future__ import annotations

from typing import Protocol


class AnalyticsProvider(Protocol):
    async def track(
        self, anonymous_id: str, event: str, properties: dict[str, str | int | bool]
    ) -> None:
        """Record a product event. No names, emails, meal content or free text. Never raises."""
        ...
