"""Candidate HTTP vision adapter, against a mocked transport (no network, no real key)."""

from __future__ import annotations

import base64
import json

import httpx
import pytest

from app.config import AppEnv, Settings
from app.container import ConfigurationError, build_vision
from app.ports.vision import VisionTimeoutError, VisionUnavailableError
from app.providers.fake_vision import FakeFoodVision
from app.providers.vision_provider import OpenAICompatibleVision
from app.vision.prompt import PROMPT_VERSION, build_prompt
from tests.support.builders import JWT_SECRET

OK_ANSWER = json.dumps(
    {
        "status": "ok",
        "description": "Arroz e feijão.",
        "items": ["arroz", "feijão"],
        "meal_type": "lunch",
        "food_groups": ["grains", "legumes"],
        "item_count": 2,
        "colors": ["white", "brown"],
        "confidence": 0.8,
        "plate_share": {"grains": 0.5, "legumes": 0.5},
    }
)


def adapter(handler: httpx.MockTransport) -> OpenAICompatibleVision:
    return OpenAICompatibleVision(
        api_key="secret-key",
        model="model-x",
        base_url="https://vision.invalid/v1/",
        transport=handler,
    )


def ok(_: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"choices": [{"message": {"content": OK_ANSWER}}]})


async def test_request_shape_carries_only_prompt_language_and_image() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return ok(request)

    vision = adapter(httpx.MockTransport(handler))
    result = await vision.analyze(b"\xff\xd8resized", "pt-BR")
    assert result.items == ["arroz", "feijão"]
    request = seen[0]
    assert request.url == "https://vision.invalid/v1/chat/completions"
    assert request.headers["Authorization"] == "Bearer secret-key"
    body = json.loads(request.content)
    assert body["model"] == "model-x"
    assert body["messages"][0] == {"role": "system", "content": build_prompt("pt-BR")}
    image_url = body["messages"][1]["content"][1]["image_url"]["url"]
    assert image_url == "data:image/jpeg;base64," + base64.b64encode(b"\xff\xd8resized").decode()
    assert set(body) == {"model", "temperature", "max_tokens", "response_format", "messages"}
    assert (vision.provider_name, vision.model_version, vision.prompt_version) == (
        "openai_compatible",
        "model-x",
        PROMPT_VERSION,
    )
    await vision.aclose()


async def test_transport_timeout_is_vision_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    with pytest.raises(VisionTimeoutError):
        await adapter(httpx.MockTransport(handler)).analyze(b"x", "pt-BR")


@pytest.mark.parametrize("status", [408, 504])
async def test_gateway_timeouts_are_vision_timeout(status: int) -> None:
    vision = adapter(httpx.MockTransport(lambda _: httpx.Response(status)))
    with pytest.raises(VisionTimeoutError):
        await vision.analyze(b"x", "pt-BR")


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(401, json={"error": "bad key"}),
        httpx.Response(429),
        httpx.Response(500),
        httpx.Response(200, text="not json"),
        httpx.Response(200, json={"choices": []}),
        httpx.Response(200, json={"choices": [{"message": {"content": None}}]}),
        httpx.Response(200, json={"choices": [{"message": {"content": "no json here"}}]}),
    ],
)
async def test_bad_answers_are_vision_unavailable(response: httpx.Response) -> None:
    vision = adapter(httpx.MockTransport(lambda _: response))
    with pytest.raises(VisionUnavailableError):
        await vision.analyze(b"x", "pt-BR")


async def test_connection_errors_are_vision_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down", request=request)

    with pytest.raises(VisionUnavailableError):
        await adapter(httpx.MockTransport(handler)).analyze(b"x", "pt-BR")


# --- container selection ----------------------------------------------------------------------


def _settings(**overrides: object) -> Settings:
    return Settings.model_validate({"jwt_secret": JWT_SECRET, **overrides})


def test_fake_is_the_default_provider() -> None:
    assert isinstance(build_vision(_settings()).inner, FakeFoodVision)


def test_real_provider_refuses_to_start_without_key_model_or_url() -> None:
    with pytest.raises(ConfigurationError, match="VISION_API_KEY"):
        build_vision(
            _settings(
                vision_provider="openai_compatible",
                vision_model="m",
                vision_base_url="https://vision.invalid/v1",
            )
        )
    with pytest.raises(ConfigurationError, match="VISION_MODEL, VISION_BASE_URL"):
        build_vision(_settings(vision_provider="openai_compatible", vision_api_key="k"))


def test_real_provider_needs_https_in_production() -> None:
    with pytest.raises(ConfigurationError, match="https"):
        build_vision(
            _settings(
                app_env=AppEnv.PRODUCTION,
                vision_provider="openai_compatible",
                vision_api_key="k",
                vision_model="m",
                vision_base_url="http://vision.invalid/v1",
            )
        )


async def test_real_provider_is_built_from_settings_behind_the_pipeline() -> None:
    vision = build_vision(
        _settings(
            vision_provider="openai_compatible",
            vision_api_key="k",
            vision_model="m",
            vision_base_url="https://vision.invalid/v1",
            vision_timeout_seconds=3,
        )
    )
    assert isinstance(vision.inner, OpenAICompatibleVision)
    assert vision.model_version == "m"
    await vision.inner.aclose()
