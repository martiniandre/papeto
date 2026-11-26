"""Pet tip: approved pt-BR phrases, chosen deterministically from the missing food groups."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.domain import FOOD_GROUPS, TIP_COPY, missing_food_groups, pick_tip
from app.vision import has_forbidden_terms

DAY = date(2026, 3, 10)
NEGATIVE_WORDS = ("evite", "não coma", "corte", "menos", "proib", "nunca", "comer", "aliment")


def test_every_food_group_has_exactly_one_approved_tip() -> None:
    assert set(TIP_COPY) == set(FOOD_GROUPS)


@pytest.mark.parametrize("tip", list(TIP_COPY.values()))
def test_tips_only_add_and_never_judge(tip: str) -> None:
    assert tip.startswith("Que tal")
    assert tip.endswith("?")
    assert not has_forbidden_terms(tip)
    for word in NEGATIVE_WORDS:
        assert word not in tip.lower()


def test_missing_groups_follow_the_vocabulary_order() -> None:
    assert missing_food_groups(["grains", "legumes", "protein", "vegetables"]) == [
        "fruits",
        "dairy",
    ]
    assert missing_food_groups(["Sweets"]) == list(FOOD_GROUPS)


def test_tip_comes_from_a_missing_group() -> None:
    present = ["grains", "legumes", "protein", "vegetables", "dairy"]
    assert pick_tip(present, DAY) == TIP_COPY["fruits"]


def test_tip_is_deterministic_and_rotates_by_day() -> None:
    present = ["grains", "legumes", "protein", "vegetables"]
    assert pick_tip(present, DAY) == pick_tip(present, DAY)
    tips = {pick_tip(present, DAY + timedelta(days=n)) for n in range(4)}
    assert tips == {TIP_COPY["fruits"], TIP_COPY["dairy"]}


def test_no_tip_when_nothing_is_missing_or_groups_are_unknown() -> None:
    assert pick_tip(list(FOOD_GROUPS), DAY) is None
    assert pick_tip([], DAY) is None  # manual meals carry no groups
    assert pick_tip(["sweets"], DAY) is None
