"""IdGenerator port."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID


class IdGenerator(Protocol):
    def new_id(self) -> UUID:
        """A new unique identifier."""
        ...
