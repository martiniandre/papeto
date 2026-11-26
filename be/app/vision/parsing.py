"""Turn a model's text answer (the JSON asked for in `prompt.py`) into a `VisionResult`.

Shared by every real adapter, so they only have to move bytes over HTTP. `status` maps to port
errors; anything that is not the expected JSON is `VisionUnavailableError`. Small overruns (long
description, too many items, unknown meal type) are trimmed instead of failing the whole log.
"""

from __future__ import annotations

import json
import re

from pydantic import ValidationError

from app.ports.vision import (
    MealType,
    NotFoodError,
    PhotoNotReadableError,
    VisionResult,
    VisionUnavailableError,
)

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)
_LIMITS = {"items": 30, "food_groups": 10, "colors": 10, "new_foods": 30}
_DESCRIPTION_MAX = 500
_KEYS = (
    "description",
    "items",
    "meal_type",
    "food_groups",
    "item_count",
    "colors",
    "confidence",
    "plate_share",
)


def parse_answer(text: str) -> VisionResult:
    try:
        data = json.loads(_FENCE.sub("", text.strip()))
    except json.JSONDecodeError as exc:
        raise VisionUnavailableError from exc
    if not isinstance(data, dict):
        raise VisionUnavailableError
    status = data.get("status", "ok")
    if status == "not_food":
        raise NotFoodError
    if status == "unreadable":
        raise PhotoNotReadableError
    if status != "ok":
        raise VisionUnavailableError
    # Unknown keys (for example "calories") are dropped here and never reach the meal.
    payload: dict[str, object] = {key: data.get(key) for key in _KEYS}
    description = payload["description"]
    if isinstance(description, str):
        payload["description"] = description[:_DESCRIPTION_MAX]
    for key, limit in _LIMITS.items():
        values = payload.get(key)
        if isinstance(values, list):
            payload[key] = values[:limit]
    if payload["meal_type"] not in {m.value for m in MealType}:
        payload["meal_type"] = MealType.SNACK.value
    items = payload["items"]
    if isinstance(items, list):
        payload["item_count"] = len(items)
    try:
        return VisionResult.model_validate(payload)
    except ValidationError as exc:
        raise VisionUnavailableError from exc
