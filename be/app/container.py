"""Dependency wiring: picks real or fake adapters from settings (the only place that knows all)."""

from __future__ import annotations

import contextlib
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.config import AppEnv, Settings
from app.db.session import SqlUowFactory, create_engine
from app.ports import AnalyticsProvider, EmailProvider, FoodVisionProvider, PushProvider
from app.providers.expo_push import ExpoPushProvider
from app.providers.fake_misc import (
    NoopAnalytics,
    NoopErrorReporter,
    RecordingAnalytics,
    RecordingEmail,
    RecordingPush,
)
from app.providers.fake_vision import FakeFoodVision
from app.providers.local_auth import LocalAuthProvider
from app.providers.posthog_analytics import PostHogAnalytics
from app.providers.system_clock import SystemClock, UuidGenerator
from app.services.context import ServiceContext


@dataclass(frozen=True)
class Container:
    ctx: ServiceContext
    readiness: Callable[[], Awaitable[dict[str, bool]]]
    shutdown: Callable[[], Awaitable[None]]


class ConfigurationError(RuntimeError):
    pass


def _vision(settings: Settings) -> FoodVisionProvider:
    if settings.vision_provider == "fake":
        if settings.app_env is AppEnv.PRODUCTION:
            raise ConfigurationError("The fake vision provider must not run in production.")
        return FakeFoodVision()
    raise ConfigurationError(f"Vision provider {settings.vision_provider!r} is not implemented.")


def build_push(settings: Settings) -> PushProvider:
    if settings.push_provider == "expo":
        token = settings.expo_access_token
        return ExpoPushProvider(access_token=token.get_secret_value() if token else None)
    if settings.push_provider == "fake":
        if settings.app_env is AppEnv.PRODUCTION:
            raise ConfigurationError("The fake push provider must not run in production.")
        return RecordingPush()
    raise ConfigurationError(f"Push provider {settings.push_provider!r} is not implemented.")


def _email(settings: Settings) -> EmailProvider:
    if settings.email_provider == "fake":
        if settings.app_env is AppEnv.PRODUCTION:
            raise ConfigurationError("The fake email provider must not run in production.")
        return RecordingEmail()  # keeps messages in memory; nothing is sent
    raise ConfigurationError(f"Email provider {settings.email_provider!r} is not implemented.")


def build_analytics(settings: Settings) -> AnalyticsProvider:
    """Disabled (noop) by default. PostHog needs its key from the environment."""
    if settings.analytics_provider == "noop":
        return NoopAnalytics()
    if settings.analytics_provider == "fake":
        if settings.app_env is AppEnv.PRODUCTION:
            raise ConfigurationError("The fake analytics provider must not run in production.")
        return RecordingAnalytics()
    if settings.analytics_provider == "posthog":
        key = settings.posthog_api_key
        if key is None:
            raise ConfigurationError("POSTHOG_API_KEY is required for the posthog provider.")
        return PostHogAnalytics(api_key=key.get_secret_value(), host=settings.posthog_host)
    raise ConfigurationError(f"Analytics provider {settings.analytics_provider!r} is not known.")


def _analytics_secret(settings: Settings) -> str:
    if settings.analytics_id_secret is not None:
        return settings.analytics_id_secret.get_secret_value()
    return "analytics:" + settings.jwt_secret.get_secret_value()


def build_container(settings: Settings) -> Container:
    engine: AsyncEngine = create_engine(settings.database_url)
    redis = Redis.from_url(settings.redis_url)
    clock = SystemClock()
    ids = UuidGenerator()
    ctx = ServiceContext(
        uow_factory=SqlUowFactory(engine),
        clock=clock,
        ids=ids,
        vision=_vision(settings),
        auth=LocalAuthProvider(
            secret=settings.jwt_secret.get_secret_value(),
            clock=clock,
            ids=ids,
            access_minutes=settings.access_token_minutes,
            refresh_days=settings.refresh_token_days,
            algorithm=settings.jwt_algorithm,
        ),
        analytics=build_analytics(settings),
        analytics_id_secret=_analytics_secret(settings),
        error_reporter=NoopErrorReporter(),
        email=_email(settings),
        deletion_grace_days=settings.deletion_grace_days,
        default_timezone=settings.default_timezone,
        password_reset_url=settings.password_reset_url,
        password_reset_minutes=settings.password_reset_minutes,
        password_reset_max_per_hour=settings.password_reset_max_per_hour,
    )

    async def readiness() -> dict[str, bool]:
        checks = {"database": False, "redis": False}
        with contextlib.suppress(Exception):  # any failure just means "not ready"
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
            checks["database"] = True
        with contextlib.suppress(Exception):
            checks["redis"] = bool(await redis.ping())
        return checks

    async def shutdown() -> None:
        await redis.aclose()
        await engine.dispose()

    return Container(ctx=ctx, readiness=readiness, shutdown=shutdown)
