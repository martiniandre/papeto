"""AnalyticsProvider port (stub). Must respect the user's analytics opt-out; random id only."""

from __future__ import annotations

from typing import Protocol


class AnalyticsProvider(Protocol):
    def track(self, anonymous_id: str, event: str, properties: dict[str, str | int | bool]) -> None:
        """Record a product event. No names, emails or meal content."""
        ...
