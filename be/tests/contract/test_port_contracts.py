"""Contract tests: one suite per port, run against every adapter that exists today.

Ports that only have a Protocol stub (PaymentProvider, StorageProvider) have no adapter yet; their
suite is added with the first adapter.
"""

from __future__ import annotations

import base64
import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import httpx
import pytest
from argon2 import PasswordHasher

from app.ports import (
    AnalyticsProvider,
    AuthProvider,
    AuthProviderUnavailableError,
    Clock,
    EmailProvider,
    ErrorReporter,
    FoodVisionProvider,
    IdGenerator,
    InvalidTokenError,
    NotFoodError,
    PhotoNotReadableError,
    PushOutcome,
    PushProvider,
    PushUnavailableError,
    SocialEmailNotVerifiedError,
    SocialTokenInvalidError,
    TokenKind,
    VisionUnavailableError,
)
from app.providers.expo_push import ExpoPushProvider
from app.providers.fake_clock import FakeClock, SequentialIdGenerator
from app.providers.fake_google import FAKE_CLIENT_ID, FakeGoogleIdentity
from app.providers.fake_misc import NoopAnalytics, NoopErrorReporter, RecordingEmail, RecordingPush
from app.providers.fake_vision import FakeFoodVision
from app.providers.google_id_token import GoogleIdTokenVerifier, HttpJwksFetcher
from app.providers.local_auth import LocalAuthProvider
from app.providers.system_clock import SystemClock, UuidGenerator
from app.providers.vision_provider import OpenAICompatibleVision
from tests.support.builders import fake_google

START = datetime(2026, 3, 10, 12, 0, tzinfo=UTC)
SAO_PAULO = ZoneInfo("America/Sao_Paulo")
FORBIDDEN_FIELDS = {"calories", "kcal", "macros", "grams", "weight", "score", "health"}


# --- Clock -----------------------------------------------------------------------------------

CLOCKS: list[Callable[[], Clock]] = [lambda: FakeClock(START), SystemClock]


@pytest.mark.parametrize("make", CLOCKS)
def test_clock_now_is_aware_utc(make: Callable[[], Clock]) -> None:
    now = make().now()
    assert now.utcoffset() == timedelta(0)


@pytest.mark.parametrize("make", CLOCKS)
def test_clock_today_matches_now_in_timezone(make: Callable[[], Clock]) -> None:
    clock = make()
    assert clock.today(SAO_PAULO) == clock.now().astimezone(SAO_PAULO).date()


def test_fake_clock_local_day_differs_from_utc_day() -> None:
    clock = FakeClock(datetime(2026, 3, 10, 2, 30, tzinfo=UTC))
    assert clock.today(SAO_PAULO).day == 9
    clock.advance(timedelta(hours=1))
    assert clock.today(SAO_PAULO).day == 10


# --- IdGenerator -----------------------------------------------------------------------------

ID_GENERATORS: list[Callable[[], IdGenerator]] = [SequentialIdGenerator, UuidGenerator]


@pytest.mark.parametrize("make", ID_GENERATORS)
def test_ids_are_unique_uuids(make: Callable[[], IdGenerator]) -> None:
    ids = make()
    values = [ids.new_id() for _ in range(50)]
    assert all(isinstance(value, UUID) for value in values)
    assert len(set(values)) == 50


# --- FoodVisionProvider ----------------------------------------------------------------------


def _mock_vision_answer(request: httpx.Request) -> httpx.Response:
    """A stand-in vision server: answers from the image bytes the adapter sent."""
    body = json.loads(request.content)
    url = body["messages"][1]["content"][1]["image_url"]["url"]
    image = base64.b64decode(url.split(",", 1)[1])
    if image.startswith(b"UNAVAILABLE"):
        return httpx.Response(503, json={"error": "overloaded"})
    status = "unreadable" if not image else "not_food" if image.startswith(b"NOTFOOD") else "ok"
    answer = {
        "status": status,
        "description": "Arroz, feijão e salada verde.",
        "items": ["arroz", "feijão", "salada"],
        "meal_type": "lunch",
        "food_groups": ["grains", "legumes", "vegetables"],
        "item_count": 3,
        "colors": ["white", "brown", "green"],
        "confidence": 0.9,
        "plate_share": {"grains": 0.4, "legumes": 0.3, "vegetables": 0.3},
    }
    content = json.dumps(answer, ensure_ascii=False)
    return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})


def _http_vision() -> FoodVisionProvider:
    return OpenAICompatibleVision(
        api_key="test-key",
        model="test-model",
        base_url="https://vision.invalid/v1",
        transport=httpx.MockTransport(_mock_vision_answer),
    )


VISIONS: list[Callable[[], FoodVisionProvider]] = [FakeFoodVision, _http_vision]


@pytest.mark.parametrize("make", VISIONS)
def test_vision_says_who_answers(make: Callable[[], FoodVisionProvider]) -> None:
    vision = make()
    assert vision.provider_name
    assert vision.model_version
    assert vision.prompt_version is None or vision.prompt_version.startswith("meal-v")


@pytest.mark.parametrize("make", VISIONS)
async def test_vision_returns_valid_result_without_forbidden_fields(
    make: Callable[[], FoodVisionProvider],
) -> None:
    result = await make().analyze(b"some-jpeg-bytes", "pt-BR")
    assert 0.0 <= result.confidence <= 1.0
    assert result.item_count == len(result.items)
    assert set(result.plate_share) <= set(result.food_groups)
    assert not FORBIDDEN_FIELDS & set(type(result).model_fields)


@pytest.mark.parametrize("make", VISIONS)
async def test_vision_is_deterministic(make: Callable[[], FoodVisionProvider]) -> None:
    vision = make()
    assert await vision.analyze(b"abc", "pt-BR") == await vision.analyze(b"abc", "pt-BR")


@pytest.mark.parametrize("make", VISIONS)
async def test_vision_failures_use_port_errors(make: Callable[[], FoodVisionProvider]) -> None:
    vision = make()
    with pytest.raises(PhotoNotReadableError):
        await vision.analyze(b"", "pt-BR")
    with pytest.raises(NotFoodError):
        await vision.analyze(b"NOTFOOD-bytes", "pt-BR")
    with pytest.raises(VisionUnavailableError):
        await vision.analyze(b"UNAVAILABLE-bytes", "pt-BR")


# --- AuthProvider ----------------------------------------------------------------------------


def _local_auth(clock: Clock) -> AuthProvider:
    return LocalAuthProvider(
        secret="test-secret-with-more-than-32-characters",
        clock=clock,
        ids=SequentialIdGenerator(),
        hasher=PasswordHasher(time_cost=1, memory_cost=8, parallelism=1),
    )


def test_auth_password_roundtrip() -> None:
    auth = _local_auth(FakeClock(START))
    hashed = auth.hash_password("correct horse")
    assert hashed != "correct horse"
    assert auth.verify_password("correct horse", hashed)
    assert not auth.verify_password("wrong", hashed)
    assert not auth.verify_password("anything", "not-a-hash")


def test_auth_token_roundtrip_and_kind_check() -> None:
    auth = _local_auth(FakeClock(START))
    user_id = uuid4()
    access = auth.create_token(user_id, TokenKind.ACCESS)
    refresh = auth.create_token(user_id, TokenKind.REFRESH)
    assert auth.decode_token(access, TokenKind.ACCESS) == user_id
    assert auth.decode_token(refresh, TokenKind.REFRESH) == user_id
    with pytest.raises(InvalidTokenError):
        auth.decode_token(access, TokenKind.REFRESH)
    with pytest.raises(InvalidTokenError):
        auth.decode_token(refresh, TokenKind.ACCESS)


def test_auth_rejects_expired_and_tampered_tokens() -> None:
    clock = FakeClock(START)
    auth = _local_auth(clock)
    token = auth.create_token(uuid4(), TokenKind.ACCESS)
    with pytest.raises(InvalidTokenError):
        auth.decode_token(token + "x", TokenKind.ACCESS)
    with pytest.raises(InvalidTokenError):
        auth.decode_token("garbage", TokenKind.ACCESS)
    clock.advance(timedelta(seconds=auth.access_ttl_seconds + 1))
    with pytest.raises(InvalidTokenError):
        auth.decode_token(token, TokenKind.ACCESS)


def test_auth_rejects_token_signed_with_another_secret() -> None:
    clock = FakeClock(START)
    other = LocalAuthProvider(
        secret="another-secret-with-more-than-32-chars", clock=clock, ids=SequentialIdGenerator()
    )
    token = other.create_token(uuid4(), TokenKind.ACCESS)
    with pytest.raises(InvalidTokenError):
        _local_auth(clock).decode_token(token, TokenKind.ACCESS)


def _google_with_fake_jwks(google: FakeGoogleIdentity, clock: Clock) -> AuthProvider:
    """Fake adapter: the fake identity serves its JWKS in memory."""
    return LocalAuthProvider(
        secret="test-secret-with-more-than-32-characters",
        clock=clock,
        ids=SequentialIdGenerator(),
        google=google.verifier(clock),
    )


def _google_with_http_jwks(google: FakeGoogleIdentity, clock: Clock) -> AuthProvider:
    """Real adapter: HTTP JWKS fetcher (mocked transport) behind the same verifier."""

    def handler(_: httpx.Request) -> httpx.Response:
        if not google.available:
            return httpx.Response(503)
        return httpx.Response(200, json=google.jwks(), headers={"Cache-Control": "max-age=300"})

    fetch = HttpJwksFetcher(client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    verifier = GoogleIdTokenVerifier(client_ids=[FAKE_CLIENT_ID], clock=clock, fetch_jwks=fetch)
    return LocalAuthProvider(
        secret="test-secret-with-more-than-32-characters",
        clock=clock,
        ids=SequentialIdGenerator(),
        google=verifier,
    )


GOOGLE_AUTHS: list[Callable[[FakeGoogleIdentity, Clock], AuthProvider]] = [
    _google_with_fake_jwks,
    _google_with_http_jwks,
]


@pytest.mark.parametrize("make", GOOGLE_AUTHS)
async def test_auth_google_accepts_a_valid_token(
    make: Callable[[FakeGoogleIdentity, Clock], AuthProvider],
) -> None:
    google, clock = fake_google(), FakeClock(START)
    auth = make(google, clock)
    token = google.issue(subject="sub-1", email="ana@example.com", now=clock.now())
    identity = await auth.verify_google_id_token(token)
    assert (identity.subject, identity.email) == ("sub-1", "ana@example.com")


@pytest.mark.parametrize("make", GOOGLE_AUTHS)
async def test_auth_google_failures_use_port_errors(
    make: Callable[[FakeGoogleIdentity, Clock], AuthProvider],
) -> None:
    google, clock = fake_google(), FakeClock(START)
    auth = make(google, clock)
    now = clock.now()
    with pytest.raises(SocialTokenInvalidError):
        await auth.verify_google_id_token("garbage")
    google.available = False
    with pytest.raises(AuthProviderUnavailableError):
        await auth.verify_google_id_token(google.issue(subject="s", email="a@b.co", now=now))
    google.available = True
    with pytest.raises(SocialTokenInvalidError):
        await auth.verify_google_id_token(
            google.issue(subject="s", email="a@b.co", now=now, audience="other")
        )
    with pytest.raises(SocialEmailNotVerifiedError):
        await auth.verify_google_id_token(
            google.issue(subject="s", email="a@b.co", now=now, email_verified=False)
        )


async def test_auth_without_google_configured_rejects_google_tokens() -> None:
    google, clock = fake_google(), FakeClock(START)
    with pytest.raises(SocialTokenInvalidError):
        await _local_auth(clock).verify_google_id_token(
            google.issue(subject="s", email="a@b.co", now=clock.now())
        )


# --- PushProvider ----------------------------------------------------------------------------


def _expo_with(handler: Callable[[httpx.Request], httpx.Response]) -> PushProvider:
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return ExpoPushProvider(access_token="secret-access", client=client)


def _expo_ok(request: httpx.Request) -> httpx.Response:
    body = json.loads(request.content)
    assert {"to", "title", "body"} <= set(body)
    if body["to"] == "ExponentPushToken[gone]":
        return httpx.Response(
            200,
            json={
                "data": {
                    "status": "error",
                    "message": "not registered",
                    "details": {"error": "DeviceNotRegistered"},
                }
            },
        )
    return httpx.Response(200, json={"data": {"status": "ok", "id": "ticket"}})


PUSHES: list[Callable[[], PushProvider]] = [
    lambda: RecordingPush(invalid_tokens={"ExponentPushToken[gone]"}),
    lambda: _expo_with(_expo_ok),
]


@pytest.mark.parametrize("make", PUSHES)
async def test_push_delivers_to_valid_token(make: Callable[[], PushProvider]) -> None:
    assert await make().send("ExponentPushToken[abc]", "title", "body") is PushOutcome.DELIVERED


@pytest.mark.parametrize("make", PUSHES)
async def test_push_reports_unregistered_device_as_invalid_token(
    make: Callable[[], PushProvider],
) -> None:
    outcome = await make().send("ExponentPushToken[gone]", "title", "body")
    assert outcome is PushOutcome.INVALID_TOKEN


async def test_fake_push_records_messages_and_can_simulate_outage() -> None:
    push = RecordingPush()
    await push.send("t", "title", "body")
    assert push.sent == [("t", "title", "body")]
    with pytest.raises(PushUnavailableError):
        await RecordingPush(fail=True).send("t", "title", "body")


async def test_expo_sends_bearer_token_and_message_fields() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"data": {"status": "ok"}})

    await _expo_with(handler).send("ExponentPushToken[abc]", "Oi", "Texto")
    assert seen[0].headers["Authorization"] == "Bearer secret-access"
    assert json.loads(seen[0].content) == {
        "to": "ExponentPushToken[abc]",
        "title": "Oi",
        "body": "Texto",
        "sound": "default",
    }


@pytest.mark.parametrize(
    "handler",
    [
        lambda request: httpx.Response(503),
        lambda request: httpx.Response(200, text="not json"),
        lambda request: httpx.Response(200, json={"data": {"status": "error", "details": {}}}),
        lambda request: (_ for _ in ()).throw(httpx.ConnectError("down")),
    ],
)
async def test_expo_failures_raise_push_unavailable(
    handler: Callable[[httpx.Request], httpx.Response],
) -> None:
    with pytest.raises(PushUnavailableError):
        await _expo_with(handler).send("ExponentPushToken[abc]", "t", "b")


async def test_email_fake_records_messages() -> None:
    email: EmailProvider = RecordingEmail()
    await email.send("a@example.com", "subject", "body")
    assert isinstance(email, RecordingEmail)
    assert email.sent == [("a@example.com", "subject", "body")]


async def test_analytics_and_error_reporter_fakes_do_not_raise() -> None:
    analytics: AnalyticsProvider = NoopAnalytics()
    reporter: ErrorReporter = NoopErrorReporter()
    await analytics.track("anon-id", "meal_logged", {"count": 1})
    reporter.capture(RuntimeError("boom"))
