"""AuthProvider port: password hashing, access/refresh tokens and social ID token checks."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol
from uuid import UUID


class TokenKind(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


class InvalidTokenError(Exception):
    """Token is malformed, expired, has a bad signature or is of the wrong kind."""


class SocialTokenInvalidError(Exception):
    """A social ID token failed verification (signature, issuer, audience, expiry or format)."""


class SocialEmailNotVerifiedError(Exception):
    """The social ID token is valid but the provider has not verified the email."""


class AuthProviderUnavailableError(Exception):
    """The identity provider could not be reached (for example its signing keys)."""


@dataclass(frozen=True, slots=True)
class GoogleIdentity:
    """Claims taken from a verified Google ID token. `email` is always verified by Google."""

    subject: str
    email: str
    name: str | None = None


class AuthProvider(Protocol):
    @property
    def access_ttl_seconds(self) -> int: ...

    def hash_password(self, password: str) -> str: ...

    def verify_password(self, password: str, password_hash: str) -> bool: ...

    def create_token(self, user_id: UUID, kind: TokenKind) -> str: ...

    def decode_token(self, token: str, kind: TokenKind) -> UUID:
        """Return the user id. Raises InvalidTokenError."""
        ...

    async def verify_google_id_token(self, id_token: str) -> GoogleIdentity:
        """Verify a Google ID token from the device.

        Raises SocialTokenInvalidError, SocialEmailNotVerifiedError or
        AuthProviderUnavailableError.
        """
        ...
