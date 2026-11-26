"""FoodVisionProvider port and the vision result model (docs/api.md).

The result never carries calories, macros, grams, scores or health labels.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field


class MealType(StrEnum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class VisionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str = Field(max_length=500)
    items: list[str] = Field(max_length=30)
    meal_type: MealType
    food_groups: list[str] = Field(max_length=10)
    item_count: int = Field(ge=0, le=50)
    colors: list[str] = Field(max_length=10)
    confidence: float = Field(ge=0.0, le=1.0)
    plate_share: dict[str, float]
    new_foods: list[str] = Field(default_factory=list, max_length=30)


class PhotoNotReadableError(Exception):
    """The photo could not be read. Does not consume the daily limit."""


class NotFoodError(Exception):
    """The photo is not food. Does not consume the daily limit."""


class PhotoTooLargeError(Exception):
    """The upload is above the size limit. Checked before any provider call."""


class VisionUnavailableError(Exception):
    """Provider error or timeout. Does not consume the daily limit."""


class VisionTimeoutError(VisionUnavailableError):
    """The provider did not answer in time. The pipeline retries once before giving up."""


class FoodVisionProvider(Protocol):
    """Adapters also say who answered, so each meal records its provider, model and prompt."""

    @property
    def provider_name(self) -> str: ...

    @property
    def model_version(self) -> str: ...

    @property
    def prompt_version(self) -> str | None: ...

    async def analyze(self, image: bytes, language: str) -> VisionResult:
        """Describe the plate. The image is never stored or logged.

        Raises PhotoNotReadableError, NotFoodError or VisionUnavailableError.
        """
        ...
