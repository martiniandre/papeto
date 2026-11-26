"""Container selection, settings and logging hygiene."""

from __future__ import annotations

import pytest

from app.config import AppEnv, Settings
from app.container import ConfigurationError, build_container
from app.logging import configure_logging
from app.providers.fake_vision import FakeFoodVision
from app.vision import VisionPipeline
from tests.api_cases import PASSWORD, signup
from tests.support.api_env import build_env
from tests.support.builders import JWT_SECRET
from tests.support.memory import MemoryUowFactory
from tests.unit.test_vision_pipeline import make_photo


def _settings(**overrides: object) -> Settings:
    return Settings.model_validate({"jwt_secret": JWT_SECRET, **overrides})


async def test_container_picks_fake_vision_from_settings() -> None:
    container = build_container(_settings(vision_provider="fake"))
    assert isinstance(container.ctx.vision, VisionPipeline)
    assert isinstance(container.ctx.vision.inner, FakeFoodVision)
    await container.shutdown()


def test_container_refuses_fake_vision_in_production_and_unknown_providers() -> None:
    with pytest.raises(ConfigurationError):
        build_container(_settings(app_env=AppEnv.PRODUCTION))
    with pytest.raises(ConfigurationError):
        build_container(_settings(vision_provider="someday"))


def test_settings_require_a_jwt_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(ValueError, match="jwt_secret"):
        Settings.model_validate({})


async def test_logs_contain_no_email_password_token_or_meal_text(
    capsys: pytest.CaptureFixture[str],
) -> None:
    env = build_env(MemoryUowFactory())
    configure_logging("INFO")  # build_env quiets logging; turn the access log back on
    headers = await signup(env, "private.person@example.com")
    meal = await env.client.post(
        "/v1/meals", files={"photo": ("m.jpg", b"jpeg-bytes", "image/jpeg")}, headers=headers
    )
    description = meal.json()["meal"]["description"]
    await env.client.aclose()
    out = capsys.readouterr().out
    assert '"event": "request"' in out
    assert "private.person" not in out
    assert PASSWORD not in out
    assert headers["Authorization"].split()[1] not in out
    assert description not in out


async def test_post_meal_runs_through_the_vision_pipeline() -> None:
    env = build_env(
        MemoryUowFactory(),
        vision=VisionPipeline(FakeFoodVision(), max_upload_bytes=1024 * 1024),
    )
    headers = await signup(env, "pipeline@example.com")
    photo = make_photo((2000, 1500), with_gps=True)
    ok = await env.client.post(
        "/v1/meals", files={"photo": ("m.jpg", photo, "image/jpeg")}, headers=headers
    )
    assert ok.status_code == 201
    unreadable = await env.client.post(
        "/v1/meals", files={"photo": ("m.jpg", b"jpeg-bytes", "image/jpeg")}, headers=headers
    )
    assert unreadable.json()["error"]["code"] == "PHOTO_NOT_READABLE"
    await env.client.aclose()
