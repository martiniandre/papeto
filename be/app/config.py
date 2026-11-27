"""Typed settings. Every environment variable the backend reads is declared here.

Secrets come only from the environment. There is deliberately no `.env` loading in code; export the
variables (see `.env.example`) or let your process manager do it.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


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

    # Google sign-in: OAuth client ids accepted as the ID token `aud` (web, Android, iOS).
    # Comma-separated in GOOGLE_CLIENT_IDS. Empty (default) rejects every Google token.
    google_client_ids: Annotated[list[str], NoDecode] = []
    google_jwks_url: str = "https://www.googleapis.com/oauth2/v3/certs"
    google_timeout_seconds: float = 5.0

    # Adapter selection: "fake" works offline; real adapters are not implemented yet.
    vision_provider: str = "fake"
    payment_provider: str = "fake"
    push_provider: str = "fake"  # "fake" or "expo"
    email_provider: str = "fake"
    analytics_provider: str = "noop"  # "noop" (default, disabled), "fake" or "posthog"
    # Vision: "fake" (default) or "openai_compatible" (candidate adapter, provider not chosen yet).
    vision_api_key: SecretStr | None = None
    vision_model: str | None = None
    vision_base_url: str | None = None
    stripe_secret_key: SecretStr | None = None
    stripe_webhook_secret: SecretStr | None = None
    sentry_dsn: SecretStr | None = None
    posthog_api_key: SecretStr | None = None
    expo_access_token: SecretStr | None = None
    posthog_host: str = "https://us.i.posthog.com"
    # Secret mixed into the per-user analytics id. Falls back to a value derived from jwt_secret.
    analytics_id_secret: SecretStr | None = None

    max_upload_bytes: int = 8 * 1024 * 1024
    vision_timeout_seconds: float = 5.0  # per attempt; the pipeline retries once on timeout
    deletion_grace_days: int = 30
    default_timezone: str = "America/Sao_Paulo"

    # Password reset: the e-mailed link is `<password_reset_url>?token=...` (app deep link or web
    # page; not decided yet). Requests above the hourly cap per account are dropped silently.
    password_reset_url: str = "papeto://reset-password"
    password_reset_minutes: int = 60
    password_reset_max_per_hour: int = 3

    @field_validator("google_client_ids", mode="before")
    @classmethod
    def _split_client_ids(cls, value: object) -> object:
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return value
