"""Pet tip for the Premium "Seus hábitos" view: one kind phrase from a fixed, approved list.

Rules:
- The tip always *adds* something ("que tal uma fruta no lanche?"). It never cuts, forbids,
  compares or judges, and never mentions body, weight, calories or right/wrong food.
- It is chosen only from the food groups missing on the plate, deterministically: the missing
  groups in `FOOD_GROUPS` order, rotated by the local day so the same plate does not always get
  the same tip. No randomness and never free text from the AI.
- No tip when every group is present, or when the groups are unknown (manual meals carry none).

Copy is a draft (pt-BR): product must review it before launch.
"""

from __future__ import annotations

from collections.abc import Collection
from datetime import date

from app.domain.food_groups import FOOD_GROUPS, known_food_groups

TIP_COPY: dict[str, str] = {
    "grains": "Que tal um arroz, pão ou milho para acompanhar a próxima refeição?",
    "legumes": "Que tal um feijão, lentilha ou grão-de-bico numa próxima refeição?",
    "protein": "Que tal um ovo, peixe, frango ou tofu numa próxima refeição?",
    "vegetables": "Que tal uma verdura ou um legume colorido no próximo prato?",
    "fruits": "Que tal uma fruta no lanche?",
    "dairy": "Que tal um iogurte ou um queijo no lanche?",
}


def missing_food_groups(present: Collection[str]) -> list[str]:
    have = set(known_food_groups(present))
    return [group for group in FOOD_GROUPS if group not in have]


def pick_tip(food_groups: Collection[str], local_day: date) -> str | None:
    """The approved tip for this plate on `local_day`, or None when there is nothing to add."""
    if not known_food_groups(food_groups):
        return None
    missing = missing_food_groups(food_groups)
    if not missing:
        return None
    return TIP_COPY[missing[local_day.toordinal() % len(missing)]]
