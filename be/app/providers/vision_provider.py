"""Candidate real FoodVisionProvider: an OpenAI-compatible `chat/completions` call over plain httpx.

The product owner has NOT chosen a vision provider. This adapter exists so that choice is one
setting (or, for a vendor with another wire format, one new `vision_<name>.py` file with the same
four members). It is off by default: `VISION_PROVIDER=fake`. To try it, set
`VISION_PROVIDER=openai_compatible`, `VISION_API_KEY`, `VISION_MODEL` and `VISION_BASE_URL`; the
container refuses to start without them. Adding a vendor also means updating the Privacy Policy.

What leaves the server: the versioned prompt, the language tag and the already resized,
metadata-free JPEG (the pipeline does that before calling here). Never a name, e-mail or user id.
Nothing about the request or the answer is logged; errors map to port errors only.
"""

from __future__ import annotations

import base64

import httpx

from app.ports.vision import VisionResult, VisionTimeoutError, VisionUnavailableError
from app.vision.parsing import parse_answer
from app.vision.prompt import PROMPT_VERSION, build_prompt

PROVIDER_NAME = "openai_compatible"
MAX_ANSWER_TOKENS = 800
USER_TEXT = "Describe this meal photo as instructed."


class OpenAICompatibleVision:
    provider_name = PROVIDER_NAME
    prompt_version: str | None = PROMPT_VERSION

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str,
        timeout_seconds: float = 5.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not api_key or not model or not base_url:
            raise ValueError("api_key, model and base_url are required")
        self.model_version = model
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/") + "/",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout_seconds,
            transport=transport,
        )

    async def analyze(self, image: bytes, language: str) -> VisionResult:
        try:
            response = await self._client.post("chat/completions", json=self._body(image, language))
        except httpx.TimeoutException as exc:
            raise VisionTimeoutError from exc
        except httpx.HTTPError as exc:
            raise VisionUnavailableError from exc
        if response.status_code in (408, 504):
            raise VisionTimeoutError
        if response.status_code != 200:
            raise VisionUnavailableError  # 4xx/5xx, including 401 bad key and 429 rate limit
        try:
            content = response.json()["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise VisionUnavailableError from exc
        if not isinstance(content, str):
            raise VisionUnavailableError
        return parse_answer(content)

    async def aclose(self) -> None:
        await self._client.aclose()

    def _body(self, image: bytes, language: str) -> dict[str, object]:
        data_url = "data:image/jpeg;base64," + base64.b64encode(image).decode("ascii")
        return {
            "model": self.model_version,
            "temperature": 0,
            "max_tokens": MAX_ANSWER_TOKENS,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": build_prompt(language)},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": USER_TEXT},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
        }
