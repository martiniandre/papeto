"""Fake Google identity for tests and local runs.

It owns a locally generated RSA key and serves its public half as an in-memory JWKS, so tokens it
issues go through the real `GoogleIdTokenVerifier` (same signature, issuer, audience, expiry and
email checks). Nothing leaves the process.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime, timedelta

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from app.ports.auth import AuthProviderUnavailableError
from app.ports.clock import Clock
from app.providers.google_id_token import (
    ALGORITHM,
    GoogleIdTokenVerifier,
    JwksDocument,
)

FAKE_CLIENT_ID = "fake-client.apps.googleusercontent.com"
FAKE_ISSUER = "https://accounts.google.com"


def new_rsa_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


class FakeGoogleIdentity:
    def __init__(
        self,
        *,
        kid: str = "fake-key-1",
        max_age_seconds: int = 3600,
        private_key: rsa.RSAPrivateKey | None = None,
    ) -> None:
        self._private = private_key or new_rsa_key()
        self.kid = kid
        self.max_age_seconds = max_age_seconds
        self.available = True  # set False to simulate a JWKS outage
        self.fetches = 0

    def jwks(self) -> dict[str, object]:
        public = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(self._private.public_key()))
        public.update({"kid": self.kid, "alg": ALGORITHM, "use": "sig"})
        return {"keys": [public]}

    async def fetch_jwks(self) -> JwksDocument:
        self.fetches += 1
        if not self.available:
            raise AuthProviderUnavailableError("fake JWKS outage")
        return JwksDocument(keys=self.jwks(), max_age_seconds=self.max_age_seconds)

    def verifier(
        self, clock: Clock, client_ids: Iterable[str] = (FAKE_CLIENT_ID,)
    ) -> GoogleIdTokenVerifier:
        return GoogleIdTokenVerifier(client_ids=client_ids, clock=clock, fetch_jwks=self.fetch_jwks)

    def issue(
        self,
        *,
        subject: str,
        email: str,
        now: datetime,
        email_verified: bool | str = True,
        audience: str = FAKE_CLIENT_ID,
        issuer: str = FAKE_ISSUER,
        ttl: timedelta = timedelta(hours=1),
        name: str | None = None,
        kid: str | None = None,
    ) -> str:
        claims: dict[str, object] = {
            "iss": issuer,
            "aud": audience,
            "sub": subject,
            "email": email,
            "email_verified": email_verified,
            "iat": int(now.timestamp()),
            "exp": int((now + ttl).timestamp()),
        }
        if name is not None:
            claims["name"] = name
        return jwt.encode(
            claims, self._private, algorithm=ALGORITHM, headers={"kid": kid or self.kid}
        )
