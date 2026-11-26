"""StorageProvider port (stub). Never used for meal photos: they are not stored (ADR 007)."""

from __future__ import annotations

from typing import Protocol


class StorageProvider(Protocol):
    async def put(self, key: str, data: bytes, content_type: str) -> str: ...

    async def delete(self, key: str) -> None: ...
