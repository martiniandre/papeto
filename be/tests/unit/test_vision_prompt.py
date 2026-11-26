"""The vision prompt asks only for allowed fields and forbids calories, scores and health labels."""

from __future__ import annotations

import json
import re

import pytest

from app.domain import FOOD_GROUPS
from app.ports.vision import (
    MealType,
    NotFoodError,
    PhotoNotReadableError,
    VisionResult,
    VisionUnavailableError,
)
from app.vision import has_forbidden_terms
from app.vision.parsing import parse_answer
from app.vision.prompt import PROMPT_VERSION, build_prompt

PROMPT = build_prompt("pt-BR")
ASKED, _, FORBIDDING = PROMPT.partition("Never include")
FORBIDDEN_WORDS = ("calorie", "macronutrient", "gram", "score", "healthy", "unhealthy")


def test_prompt_is_versioned() -> None:
    assert re.fullmatch(r"meal-v\d+", PROMPT_VERSION)


def test_prompt_asks_exactly_for_the_vision_result_fields() -> None:
    asked = set(re.findall(r'^- "(\w+)"', ASKED, flags=re.MULTILINE))
    expected = set(VisionResult.model_fields) - {"new_foods"}  # computed by the service
    assert asked == expected | {"status"}


def test_prompt_requests_no_forbidden_concept() -> None:
    assert FORBIDDING, "the prompt must have an explicit 'Never include' paragraph"
    assert not has_forbidden_terms(ASKED)
    for word in FORBIDDEN_WORDS:
        assert word not in ASKED.lower()


@pytest.mark.parametrize("word", FORBIDDEN_WORDS)
def test_prompt_explicitly_forbids(word: str) -> None:
    assert word in FORBIDDING.lower()


def test_prompt_uses_the_fixed_vocabularies_and_user_language() -> None:
    for group in FOOD_GROUPS:
        assert f'"{group}"' in ASKED
    for meal_type in MealType:
        assert f'"{meal_type.value}"' in ASKED
    assert "Brazilian Portuguese" in PROMPT
    assert "English" in build_prompt("en")
    assert "Brazilian Portuguese" in build_prompt("xx-unknown")  # falls back to pt-BR


def test_prompt_carries_no_personal_data_placeholders() -> None:
    assert "{" not in PROMPT
    assert "name" not in ASKED.lower().replace("common name", "")
    assert "mail" not in PROMPT.lower()


# --- parsing --------------------------------------------------------------------------------


def answer(**overrides: object) -> str:
    base: dict[str, object] = {
        "status": "ok",
        "description": "Arroz, feijão e salada.",
        "items": ["arroz", "feijão", "salada"],
        "meal_type": "lunch",
        "food_groups": ["grains", "legumes", "vegetables"],
        "item_count": 3,
        "colors": ["white", "brown", "green"],
        "confidence": 0.9,
        "plate_share": {"grains": 0.4, "legumes": 0.3, "vegetables": 0.3},
    }
    base.update(overrides)
    return json.dumps(base, ensure_ascii=False)


def test_parse_ok_answer_and_drop_unknown_keys() -> None:
    result = parse_answer(answer(calories=650, score=8))
    assert result.items == ["arroz", "feijão", "salada"]
    assert result.meal_type is MealType.LUNCH
    assert "calories" not in result.model_dump()


def test_parse_accepts_code_fences_and_trims_overruns() -> None:
    text = (
        "```json\n" + answer(description="x" * 900, items=["a"] * 40, meal_type="brunch") + "\n```"
    )
    result = parse_answer(text)
    assert len(result.description) == 500
    assert len(result.items) == 30
    assert result.item_count == 30
    assert result.meal_type is MealType.SNACK


@pytest.mark.parametrize(
    ("status", "error"),
    [
        ("not_food", NotFoodError),
        ("unreadable", PhotoNotReadableError),
        ("?", VisionUnavailableError),
    ],
)
def test_parse_status_maps_to_port_errors(status: str, error: type[Exception]) -> None:
    with pytest.raises(error):
        parse_answer(answer(status=status))


@pytest.mark.parametrize("text", ["", "not json", "[1, 2]", answer(confidence=7)])
def test_parse_garbage_is_vision_unavailable(text: str) -> None:
    with pytest.raises(VisionUnavailableError):
        parse_answer(text)
