"""AuthProvider port: password hashing and access/refresh tokens (social login comes later)."""

from __future__ import annotations

from enum import StrEnum
from typing import Protocol
from uuid import UUID


class TokenKind(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


class InvalidTokenError(Exception):
    """Token is malformed, expired, has a bad signature or is of the wrong kind."""


class AuthProvider(Protocol):
    @property
    def access_ttl_seconds(self) -> int: ...

    def hash_password(self, password: str) -> str: ...

    def verify_password(self, password: str, password_hash: str) -> bool: ...

    def create_token(self, user_id: UUID, kind: TokenKind) -> str: ...

    def decode_token(self, token: str, kind: TokenKind) -> UUID:
        """Return the user id. Raises InvalidTokenError."""
        ...
