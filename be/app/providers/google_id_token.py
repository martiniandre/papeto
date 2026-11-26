"""Google ID token verification with PyJWT and httpx (no Google SDK).

The device signs in with Google and sends the ID token; the server checks it here:

- RS256 signature against Google's JWKS (`GOOGLE_JWKS_URL`), cached for the response's
  `Cache-Control: max-age` (measured with the Clock port);
- `iss` is `accounts.google.com` or `https://accounts.google.com`;
- `aud` is one of the configured client ids (web, Android, iOS);
- `exp` has not passed (Clock port, no leeway);
- `email_verified` is true.

Neither the token nor the email is ever logged.
"""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import httpx
import jwt

from app.ports.auth import (
    AuthProviderUnavailableError,
    GoogleIdentity,
    SocialEmailNotVerifiedError,
    SocialTokenInvalidError,
)
from app.ports.clock import Clock

GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = frozenset({"accounts.google.com", "https://accounts.google.com"})
ALGORITHM = "RS256"
# An unknown `kid` forces a refetch (Google rotates keys), but at most this often.
MIN_REFETCH_INTERVAL = timedelta(seconds=60)

_MAX_AGE = re.compile(r"(?:^|[,\s])max-age\s*=\s*(\d+)", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class JwksDocument:
    keys: Mapping[str, Any]  # the JSON Web Key Set as returned by the provider
    max_age_seconds: int


JwksFetcher = Callable[[], Awaitable[JwksDocument]]


def parse_max_age(cache_control: str | None) -> int:
    """Seconds from `Cache-Control: max-age=N`; 0 (do not cache) when absent or `no-store`."""
    if not cache_control or "no-store" in cache_control.lower():
        return 0
    match = _MAX_AGE.search(cache_control)
    return int(match.group(1)) if match else 0


class HttpJwksFetcher:
    """Downloads the JWKS. Any network, status or JSON problem is AuthProviderUnavailableError."""

    def __init__(
        self,
        *,
        url: str = GOOGLE_JWKS_URL,
        client: httpx.AsyncClient | None = None,
        timeout_seconds: float = 5.0,
    ) -> None:
        self._url = url
        self._client = client or httpx.AsyncClient(timeout=timeout_seconds)

    async def __call__(self) -> JwksDocument:
        try:
            response = await self._client.get(self._url)
            response.raise_for_status()
            body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise AuthProviderUnavailableError("could not fetch the signing keys") from exc
        if not isinstance(body, dict) or not isinstance(body.get("keys"), list):
            raise AuthProviderUnavailableError("signing keys have an unexpected shape")
        return JwksDocument(
            keys=body, max_age_seconds=parse_max_age(response.headers.get("cache-control"))
        )

    async def aclose(self) -> None:
        await self._client.aclose()


class GoogleIdTokenVerifier:
    def __init__(
        self,
        *,
        client_ids: Iterable[str],
        clock: Clock,
        fetch_jwks: JwksFetcher,
    ) -> None:
        self._client_ids = tuple(cid for cid in client_ids if cid)
        self._clock = clock
        self._fetch = fetch_jwks
        self._keys: dict[str, jwt.PyJWK] = {}
        self._expires_at: datetime | None = None
        self._fetched_at: datetime | None = None

    async def verify(self, id_token: str) -> GoogleIdentity:
        if not self._client_ids:
            raise SocialTokenInvalidError("no Google client id is configured")
        try:
            header = jwt.get_unverified_header(id_token)
        except jwt.PyJWTError as exc:
            raise SocialTokenInvalidError("malformed token") from exc
        kid = header.get("kid")
        if header.get("alg") != ALGORITHM or not isinstance(kid, str):
            raise SocialTokenInvalidError("unexpected token header")
        key = await self._key(kid)
        try:
            claims = jwt.decode(
                id_token,
                key.key,
                algorithms=[ALGORITHM],
                audience=list(self._client_ids),
                options={
                    # Time claims are checked against the Clock port below, not the system clock.
                    "verify_exp": False,
                    "verify_iat": False,
                    "verify_nbf": False,
                    "require": ["iss", "aud", "exp", "sub"],
                },
            )
        except jwt.PyJWTError as exc:
            raise SocialTokenInvalidError("signature or audience check failed") from exc
        return self._identity(claims)

    def _identity(self, claims: Mapping[str, Any]) -> GoogleIdentity:
        if claims.get("iss") not in GOOGLE_ISSUERS:
            raise SocialTokenInvalidError("unexpected issuer")
        exp = claims.get("exp")
        if not isinstance(exp, int | float) or isinstance(exp, bool):
            raise SocialTokenInvalidError("bad expiry")
        if exp <= self._clock.now().timestamp():
            raise SocialTokenInvalidError("token expired")
        subject = claims.get("sub")
        email = claims.get("email")
        if not isinstance(subject, str) or not subject:
            raise SocialTokenInvalidError("missing subject")
        if not isinstance(email, str) or "@" not in email:
            raise SocialTokenInvalidError("missing email")
        if claims.get("email_verified") not in (True, "true"):
            raise SocialEmailNotVerifiedError("email not verified by Google")
        name = claims.get("name")
        return GoogleIdentity(
            subject=subject,
            email=email,
            name=name.strip() or None if isinstance(name, str) else None,
        )

    async def _key(self, kid: str) -> jwt.PyJWK:
        now = self._clock.now()
        fresh = self._expires_at is not None and now < self._expires_at
        if not fresh:
            await self._refresh(now)
        elif kid not in self._keys and self._may_refetch(now):
            await self._refresh(now)  # possible key rotation
        key = self._keys.get(kid)
        if key is None:
            raise SocialTokenInvalidError("unknown signing key")
        return key

    def _may_refetch(self, now: datetime) -> bool:
        return self._fetched_at is None or now - self._fetched_at >= MIN_REFETCH_INTERVAL

    async def _refresh(self, now: datetime) -> None:
        try:
            document = await self._fetch()
        except AuthProviderUnavailableError:
            if self._keys:
                return  # keep using the last good keys until the provider answers again
            raise
        try:
            key_set = jwt.PyJWKSet.from_dict(dict(document.keys))
        except jwt.PyJWTError as exc:
            if self._keys:
                return
            raise AuthProviderUnavailableError("signing keys could not be read") from exc
        self._keys = {k.key_id: k for k in key_set.keys if k.key_id}
        self._fetched_at = now
        self._expires_at = now + timedelta(seconds=document.max_age_seconds)
