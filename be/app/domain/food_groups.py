"""Fixed food group vocabulary (docs/api.md). Groups describe the plate; they never rank it.

The vision prompt asks only for these tokens and the pipeline drops anything else, so the rest of
the app (pet tip, Premium "Seus hábitos" view) can rely on this closed set.
"""

from __future__ import annotations

from collections.abc import Iterable

FOOD_GROUPS: tuple[str, ...] = ("grains", "legumes", "protein", "vegetables", "fruits", "dairy")


def known_food_groups(groups: Iterable[str]) -> list[str]:
    """Lowercased, deduplicated groups from the fixed vocabulary, in first-seen order."""
    seen: list[str] = []
    for group in groups:
        token = group.strip().lower()
        if token in FOOD_GROUPS and token not in seen:
            seen.append(token)
    return seen
