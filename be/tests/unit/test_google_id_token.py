"""Google ID token verification: locally generated RSA keys, a fake JWKS and the fake Clock."""

from __future__ import annotations

from datetime import timedelta

import httpx
import pytest

from app.ports.auth import (
    AuthProviderUnavailableError,
    SocialEmailNotVerifiedError,
    SocialTokenInvalidError,
)
from app.providers.fake_clock import FakeClock
from app.providers.fake_google import FAKE_CLIENT_ID, FakeGoogleIdentity
from app.providers.google_id_token import (
    GoogleIdTokenVerifier,
    HttpJwksFetcher,
    JwksDocument,
    parse_max_age,
)
from tests.support.builders import START, fake_google

SUB = "109876543210"
EMAIL = "Ana@Example.com"


def _setup() -> tuple[FakeGoogleIdentity, FakeClock, GoogleIdTokenVerifier]:
    google = fake_google()
    clock = FakeClock(START)
    return google, clock, google.verifier(clock)


async def test_good_token_returns_identity() -> None:
    google, clock, verifier = _setup()
    token = google.issue(subject=SUB, email=EMAIL, now=clock.now(), name=" Ana ")
    identity = await verifier.verify(token)
    assert identity.subject == SUB
    assert identity.email == EMAIL
    assert identity.name == "Ana"


async def test_issuer_without_scheme_is_accepted() -> None:
    google, clock, verifier = _setup()
    token = google.issue(subject=SUB, email=EMAIL, now=clock.now(), issuer="accounts.google.com")
    assert (await verifier.verify(token)).subject == SUB


async def test_email_verified_as_string_true_is_accepted() -> None:
    google, clock, verifier = _setup()
    token = google.issue(subject=SUB, email=EMAIL, now=clock.now(), email_verified="true")
    assert (await verifier.verify(token)).subject == SUB


async def test_any_configured_client_id_is_accepted() -> None:
    google = fake_google()
    clock = FakeClock(START)
    verifier = google.verifier(clock, client_ids=["web-id", "android-id", "ios-id"])
    token = google.issue(subject=SUB, email=EMAIL, now=clock.now(), audience="ios-id")
    assert (await verifier.verify(token)).subject == SUB


async def test_wrong_audience_is_rejected() -> None:
    google, clock, verifier = _setup()
    token = google.issue(subject=SUB, email=EMAIL, now=clock.now(), audience="someone-else")
    with pytest.raises(SocialTokenInvalidError):
        await verifier.verify(token)


async def test_no_configured_client_id_rejects_everything() -> None:
    google = fake_google()
    clock = FakeClock(START)
    verifier = google.verifier(clock, client_ids=[])
    token = google.issue(subject=SUB, email=EMAIL, now=clock.now())
    with pytest.raises(SocialTokenInvalidError):
        await verifier.verify(token)
    assert google.fetches == 0


async def test_wrong_issuer_is_rejected() -> None:
    google, clock, verifier = _setup()
    token = google.issue(subject=SUB, email=EMAIL, now=clock.now(), issuer="https://evil.example")
    with pytest.raises(SocialTokenInvalidError):
        await verifier.verify(token)


async def test_expired_token_is_rejected_by_the_clock() -> None:
    google, clock, verifier = _setup()
    token = google.issue(subject=SUB, email=EMAIL, now=clock.now(), ttl=timedelta(minutes=10))
    clock.advance(timedelta(minutes=10))  # exp == now counts as expired
    with pytest.raises(SocialTokenInvalidError):
        await verifier.verify(token)


async def test_token_valid_until_the_last_second() -> None:
    google, clock, verifier = _setup()
    token = google.issue(subject=SUB, email=EMAIL, now=clock.now(), ttl=timedelta(minutes=10))
    clock.advance(timedelta(minutes=10) - timedelta(seconds=1))
    assert (await verifier.verify(token)).subject == SUB


async def test_unverified_email_is_rejected() -> None:
    google, clock, verifier = _setup()
    token = google.issue(subject=SUB, email=EMAIL, now=clock.now(), email_verified=False)
    with pytest.raises(SocialEmailNotVerifiedError):
        await verifier.verify(token)


async def test_token_signed_by_another_key_is_rejected() -> None:
    _, clock, verifier = _setup()
    impostor = FakeGoogleIdentity()  # same kid, different private key
    token = impostor.issue(subject=SUB, email=EMAIL, now=clock.now())
    with pytest.raises(SocialTokenInvalidError):
        await verifier.verify(token)


@pytest.mark.parametrize("token", ["", "garbage", "a.b.c"])
async def test_malformed_tokens_are_rejected(token: str) -> None:
    _, _, verifier = _setup()
    with pytest.raises(SocialTokenInvalidError):
        await verifier.verify(token)


async def test_jwks_failure_without_cached_keys_is_unavailable() -> None:
    google, clock, verifier = _setup()
    google.available = False
    token = google.issue(subject=SUB, email=EMAIL, now=clock.now())
    with pytest.raises(AuthProviderUnavailableError):
        await verifier.verify(token)


async def test_jwks_failure_after_expiry_keeps_the_last_good_keys() -> None:
    google, clock, verifier = _setup()
    await verifier.verify(google.issue(subject=SUB, email=EMAIL, now=clock.now()))
    clock.advance(timedelta(seconds=google.max_age_seconds + 1))
    google.available = False
    token = google.issue(subject=SUB, email=EMAIL, now=clock.now())
    assert (await verifier.verify(token)).subject == SUB


async def test_keys_are_cached_for_max_age() -> None:
    google, clock, verifier = _setup()
    google.max_age_seconds = 600
    await verifier.verify(google.issue(subject=SUB, email=EMAIL, now=clock.now()))
    clock.advance(timedelta(seconds=599))
    await verifier.verify(google.issue(subject=SUB, email=EMAIL, now=clock.now()))
    assert google.fetches == 1
    clock.advance(timedelta(seconds=1))
    await verifier.verify(google.issue(subject=SUB, email=EMAIL, now=clock.now()))
    assert google.fetches == 2


async def test_unknown_kid_refetches_at_most_once_a_minute() -> None:
    google, clock, verifier = _setup()
    await verifier.verify(google.issue(subject=SUB, email=EMAIL, now=clock.now()))
    rotated = google.issue(subject=SUB, email=EMAIL, now=clock.now(), kid="rotated")
    with pytest.raises(SocialTokenInvalidError):
        await verifier.verify(rotated)
    assert google.fetches == 1  # fetched less than a minute ago
    clock.advance(timedelta(seconds=60))
    with pytest.raises(SocialTokenInvalidError):
        await verifier.verify(rotated)
    assert google.fetches == 2


@pytest.mark.parametrize(
    ("header", "seconds"),
    [
        ("public, max-age=19800, must-revalidate, no-transform", 19800),
        ("max-age=60", 60),
        ("no-cache", 0),
        ("no-store, max-age=60", 0),
        (None, 0),
    ],
)
def test_parse_max_age(header: str | None, seconds: int) -> None:
    assert parse_max_age(header) == seconds


async def test_http_fetcher_reads_keys_and_cache_control() -> None:
    google = fake_google()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL("https://keys.example/certs")
        return httpx.Response(200, json=google.jwks(), headers={"Cache-Control": "max-age=120"})

    fetch = HttpJwksFetcher(
        url="https://keys.example/certs",
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    document = await fetch()
    await fetch.aclose()
    assert document.max_age_seconds == 120
    assert document.keys["keys"][0]["kid"] == google.kid


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(500),
        httpx.Response(200, content=b"not json"),
        httpx.Response(200, json={"no": "keys"}),
    ],
)
async def test_http_fetcher_failures_are_unavailable(response: httpx.Response) -> None:
    fetch = HttpJwksFetcher(
        client=httpx.AsyncClient(transport=httpx.MockTransport(lambda _: response))
    )
    with pytest.raises(AuthProviderUnavailableError):
        await fetch()


async def test_http_fetcher_network_error_is_unavailable() -> None:
    def boom(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down", request=request)

    fetch = HttpJwksFetcher(client=httpx.AsyncClient(transport=httpx.MockTransport(boom)))
    with pytest.raises(AuthProviderUnavailableError):
        await fetch()


async def test_unreadable_key_set_is_unavailable() -> None:
    clock = FakeClock(START)

    async def bad_keys() -> JwksDocument:
        return JwksDocument(keys={"keys": [{"kty": "nope"}]}, max_age_seconds=60)

    verifier = GoogleIdTokenVerifier(client_ids=[FAKE_CLIENT_ID], clock=clock, fetch_jwks=bad_keys)
    token = fake_google().issue(subject=SUB, email=EMAIL, now=clock.now())
    with pytest.raises(AuthProviderUnavailableError):
        await verifier.verify(token)
