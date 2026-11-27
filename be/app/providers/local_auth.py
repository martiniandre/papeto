"""AuthProvider adapter: Argon2 password hashes, HS256 JWTs (PyJWT) and Google ID token checks."""

from __future__ import annotations

from datetime import timedelta
from typing import Protocol
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.ports.auth import GoogleIdentity, InvalidTokenError, SocialTokenInvalidError, TokenKind
from app.ports.clock import Clock
from app.ports.ids import IdGenerator


class GoogleTokenVerifier(Protocol):
    async def verify(self, id_token: str) -> GoogleIdentity: ...


class LocalAuthProvider:
    def __init__(
        self,
        *,
        secret: str,
        clock: Clock,
        ids: IdGenerator,
        access_minutes: int = 15,
        refresh_days: int = 30,
        algorithm: str = "HS256",
        hasher: PasswordHasher | None = None,
        google: GoogleTokenVerifier | None = None,
    ) -> None:
        if len(secret) < 16:
            raise ValueError("JWT secret is too short")
        self._secret = secret
        self._clock = clock
        self._ids = ids
        self._access = timedelta(minutes=access_minutes)
        self._refresh = timedelta(days=refresh_days)
        self._algorithm = algorithm
        self._hasher = hasher or PasswordHasher()
        self._google = google

    @property
    def access_ttl_seconds(self) -> int:
        return int(self._access.total_seconds())

    def hash_password(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify_password(self, password: str, password_hash: str) -> bool:
        try:
            return self._hasher.verify(password_hash, password)
        except (VerificationError, InvalidHashError):
            return False

    def create_token(self, user_id: UUID, kind: TokenKind) -> str:
        now = self._clock.now()
        ttl = self._access if kind is TokenKind.ACCESS else self._refresh
        payload = {
            "sub": str(user_id),
            "typ": kind.value,
            "jti": str(self._ids.new_id()),
            "iat": int(now.timestamp()),
            "exp": int((now + ttl).timestamp()),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def decode_token(self, token: str, kind: TokenKind) -> UUID:
        try:
            # Expiry is checked against the Clock port, not the system clock.
            claims = jwt.decode(
                token,
                self._secret,
                algorithms=[self._algorithm],
                options={
                    "verify_exp": False,
                    "verify_iat": False,
                    "require": ["sub", "typ", "exp"],
                },
            )
            if claims["typ"] != kind.value:
                raise InvalidTokenError("wrong token kind")
            if int(claims["exp"]) <= int(self._clock.now().timestamp()):
                raise InvalidTokenError("token expired")
            return UUID(str(claims["sub"]))
        except (jwt.PyJWTError, ValueError, KeyError) as exc:
            raise InvalidTokenError("invalid token") from exc

    async def verify_google_id_token(self, id_token: str) -> GoogleIdentity:
        if self._google is None:
            raise SocialTokenInvalidError("Google sign-in is not configured")
        return await self._google.verify(id_token)
