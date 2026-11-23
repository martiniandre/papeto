"""ErrorReporter port (stub). Must never receive emails, tokens, photos or meal descriptions."""

from __future__ import annotations

from typing import Protocol


class ErrorReporter(Protocol):
    def capture(self, error: BaseException) -> None: ...
