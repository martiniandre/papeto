"""Contract tests: one suite per port, run against every adapter that exists today.

Ports that only have a Protocol stub (PaymentProvider, StorageProvider) have no adapter yet; their
suite is added with the first adapter.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest

from app.ports import (
    AnalyticsProvider,
    AuthProvider,
    Clock,
    EmailProvider,
    ErrorReporter,
    FoodVisionProvider,
    IdGenerator,
    InvalidTokenError,
    NotFoodError,
    PhotoNotReadableError,
    PushProvider,
    TokenKind,
    VisionUnavailableError,
)
from app.providers.fake_clock import FakeClock, SequentialIdGenerator
from app.providers.fake_misc import NoopAnalytics, NoopErrorReporter, RecordingEmail, RecordingPush
from app.providers.fake_vision import FakeFoodVision
from app.providers.local_auth import LocalAuthProvider
from app.providers.system_clock import SystemClock, UuidGenerator

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

VISIONS: list[Callable[[], FoodVisionProvider]] = [FakeFoodVision]


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
        secret="test-secret-with-more-than-32-characters", clock=clock, ids=SequentialIdGenerator()
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


# --- Push, Email, Analytics, ErrorReporter (fakes only) --------------------------------------


async def test_push_and_email_fakes_record_messages() -> None:
    push: PushProvider = RecordingPush()
    email: EmailProvider = RecordingEmail()
    await push.send("token", "title", "body")
    await email.send("a@example.com", "subject", "body")
    assert isinstance(push, RecordingPush)
    assert push.sent == [("token", "title", "body")]
    assert isinstance(email, RecordingEmail)
    assert email.sent == [("a@example.com", "subject", "body")]


def test_analytics_and_error_reporter_fakes_do_not_raise() -> None:
    analytics: AnalyticsProvider = NoopAnalytics()
    reporter: ErrorReporter = NoopErrorReporter()
    analytics.track("anon-id", "meal_logged", {"count": 1})
    reporter.capture(RuntimeError("boom"))
