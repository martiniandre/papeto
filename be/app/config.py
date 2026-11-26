"""Typed settings. Every environment variable the backend reads is declared here.

Secrets come only from the environment. There is deliberately no `.env` loading in code; export the
variables (see `.env.example`) or let your process manager do it.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(StrEnum):
    LOCAL = "local"
    TEST = "test"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore", case_sensitive=False)

    app_env: AppEnv = AppEnv.LOCAL
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://papeto:papeto@localhost:5432/papeto"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: SecretStr
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 30

    # Adapter selection: "fake" works offline; real adapters are not implemented yet.
    vision_provider: str = "fake"
    payment_provider: str = "fake"
    push_provider: str = "fake"  # "fake" or "expo"
    vision_api_key: SecretStr | None = None
    stripe_secret_key: SecretStr | None = None
    stripe_webhook_secret: SecretStr | None = None
    sentry_dsn: SecretStr | None = None
    posthog_api_key: SecretStr | None = None
    expo_access_token: SecretStr | None = None

    max_upload_bytes: int = 8 * 1024 * 1024
    deletion_grace_days: int = 30
    default_timezone: str = "America/Sao_Paulo"
