"""Validate and tidy a provider answer before it reaches the meal log.

Runs on every answer, fake or real: re-validates with `VisionResult`, keeps only the fixed food
group vocabulary, keeps `plate_share` consistent with the groups, and drops any text that slipped
in with calories, macros, grams, scores or health labels (the prompt already forbids them).
"""

from __future__ import annotations

import re

from pydantic import ValidationError

from app.domain import known_food_groups
from app.ports.vision import VisionResult, VisionUnavailableError

MAX_ITEM_CHARS = 80

# Stems in English and Portuguese, matched case-insensitively.
_FORBIDDEN = (
    r"calori",
    r"kcal",
    r"\bcal\b",
    r"macro",
    r"\bcarbs?\b",
    r"carboidrat",
    r"\d+\s*(g|gr|grams?|gramas?|mg|kg)\b",
    r"\bgram(a|o|as|os|s)?\b",
    r"\bscore",
    r"pontua[cç]",
    r"\bnota\b",
    r"health",
    r"saud[aá]ve",
    r"insalubr",
    r"junk",
    r"porcaria",
    r"engorda",
    r"fattening",
    r"\bdiet\b",
    r"\bdieta\b",
)
_FORBIDDEN_RE = re.compile("|".join(_FORBIDDEN), re.IGNORECASE)


def has_forbidden_terms(text: str) -> bool:
    return bool(_FORBIDDEN_RE.search(text))


def clean_result(result: VisionResult) -> VisionResult:
    """A validated copy with only allowed content. Raises VisionUnavailableError if invalid."""
    try:
        checked = VisionResult.model_validate(result.model_dump())
    except ValidationError as exc:
        raise VisionUnavailableError from exc
    items = _clean_items(checked.items)
    groups = known_food_groups(checked.food_groups)
    share = {g: min(max(v, 0.0), 1.0) for g, v in checked.plate_share.items() if g in groups}
    total = sum(share.values())
    if total > 1.0:
        share = {g: round(v / total, 4) for g, v in share.items()}
    description = checked.description.strip()
    if has_forbidden_terms(description):
        description = ""  # better no description than a judging one
    return checked.model_copy(
        update={
            "description": description,
            "items": items,
            "item_count": len(items),
            "food_groups": groups,
            "plate_share": share,
            "colors": _unique_lower(checked.colors),
            "new_foods": [],  # computed by the service from the user's own history
        }
    )


def _clean_items(items: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in items:
        item = " ".join(raw.split())[:MAX_ITEM_CHARS]
        key = item.lower()
        if not item or key in seen or has_forbidden_terms(item):
            continue
        seen.add(key)
        cleaned.append(item)
    return cleaned


def _unique_lower(values: list[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        token = value.strip().lower()
        if token and token not in out:
            out.append(token)
    return out
