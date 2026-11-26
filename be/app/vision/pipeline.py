"""`VisionPipeline`: the provider-neutral wrapper the container puts around every adapter.

1. Type and size check, resize to 1024 px JPEG, metadata stripped (`prepare_image`).
2. Call the adapter with a per-attempt timeout; retry once, on timeout only.
3. Map anything unexpected to `VisionUnavailableError`; pass the adapter's
   `PhotoNotReadableError` / `NotFoodError` / `VisionUnavailableError` through unchanged.
4. Validate and tidy the answer (`clean_result`).

The caller (`log_meal`) turns port errors into PHOTO_NOT_READABLE, PHOTO_TOO_LARGE, NOT_FOOD and
VISION_UNAVAILABLE before writing anything, so a failure never consumes the daily limit. Logs carry
only the provider name, the attempt and the outcome: never image bytes or meal text.
"""

from __future__ import annotations

import asyncio

import structlog

from app.ports.vision import (
    FoodVisionProvider,
    NotFoodError,
    PhotoNotReadableError,
    VisionResult,
    VisionTimeoutError,
    VisionUnavailableError,
)
from app.vision.image import MAX_SIDE, prepare_image
from app.vision.result import clean_result

log = structlog.get_logger("app.vision")

DEFAULT_TIMEOUT_SECONDS = 5.0  # two attempts stay within the 10 s budget of RNF-22
MAX_ATTEMPTS = 2  # first call + one retry on timeout


class VisionPipeline:
    def __init__(
        self,
        inner: FoodVisionProvider,
        *,
        max_upload_bytes: int,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_side: int = MAX_SIDE,
    ) -> None:
        self.inner = inner
        self._max_bytes = max_upload_bytes
        self._timeout = timeout_seconds
        self._max_side = max_side

    @property
    def provider_name(self) -> str:
        return self.inner.provider_name

    @property
    def model_version(self) -> str:
        return self.inner.model_version

    @property
    def prompt_version(self) -> str | None:
        return self.inner.prompt_version

    async def analyze(self, image: bytes, language: str) -> VisionResult:
        prepared = prepare_image(image, max_bytes=self._max_bytes, max_side=self._max_side)
        result = await self._call_with_retry(prepared, language)
        return clean_result(result)

    async def _call_with_retry(self, prepared: bytes, language: str) -> VisionResult:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                async with asyncio.timeout(self._timeout):
                    result = await self.inner.analyze(prepared, language)
            except (TimeoutError, VisionTimeoutError) as exc:
                log.warning("vision_timeout", provider=self.provider_name, attempt=attempt)
                if attempt == MAX_ATTEMPTS:
                    raise VisionTimeoutError from exc
                continue
            except (PhotoNotReadableError, NotFoodError, VisionUnavailableError) as exc:
                log.info(
                    "vision_rejected",
                    provider=self.provider_name,
                    attempt=attempt,
                    reason=type(exc).__name__,
                )
                raise
            except Exception as exc:  # adapter bug or unexpected transport error
                log.warning(
                    "vision_failed",
                    provider=self.provider_name,
                    attempt=attempt,
                    reason=type(exc).__name__,
                )
                raise VisionUnavailableError from exc
            log.info("vision_analyzed", provider=self.provider_name, attempts=attempt)
            return result
        raise VisionUnavailableError  # not reached: every attempt returns or raises
