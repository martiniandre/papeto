"""Deterministic fake FoodVisionProvider. No network, no calories or grams.

Special payloads trigger failures so tests and local runs can exercise error paths: empty bytes
raise PhotoNotReadableError, a payload starting with NOTFOOD raises NotFoodError and one starting
with UNAVAILABLE raises VisionUnavailableError. Any other payload picks one of a few canned plates
from a hash of the bytes.
"""

from __future__ import annotations

import hashlib

from app.ports.vision import (
    MealType,
    NotFoodError,
    PhotoNotReadableError,
    VisionResult,
    VisionUnavailableError,
)

_PLATES: tuple[VisionResult, ...] = (
    VisionResult(
        description="Rice, beans and a green salad on a white plate.",
        items=["rice", "beans", "salad"],
        meal_type=MealType.LUNCH,
        food_groups=["grains", "legumes", "vegetables"],
        item_count=3,
        colors=["white", "brown", "green"],
        confidence=0.9,
        plate_share={"grains": 0.4, "legumes": 0.3, "vegetables": 0.3},
    ),
    VisionResult(
        description="Bread with cheese and a cup of coffee.",
        items=["bread", "cheese", "coffee"],
        meal_type=MealType.BREAKFAST,
        food_groups=["grains", "dairy"],
        item_count=3,
        colors=["brown", "yellow"],
        confidence=0.85,
        plate_share={"grains": 0.6, "dairy": 0.4},
    ),
    VisionResult(
        description="A banana and a handful of nuts.",
        items=["banana", "nuts"],
        meal_type=MealType.SNACK,
        food_groups=["fruits", "protein"],
        item_count=2,
        colors=["yellow", "brown"],
        confidence=0.8,
        plate_share={"fruits": 0.7, "protein": 0.3},
    ),
)


class FakeFoodVision:
    provider_name = "fake"
    model_version = "fake-1"
    prompt_version: str | None = None  # canned answers, no prompt

    async def analyze(self, image: bytes, language: str) -> VisionResult:
        if not image:
            raise PhotoNotReadableError
        if image.startswith(b"NOTFOOD"):
            raise NotFoodError
        if image.startswith(b"UNAVAILABLE"):
            raise VisionUnavailableError
        index = hashlib.sha256(image).digest()[0] % len(_PLATES)
        return _PLATES[index].model_copy(deep=True)
