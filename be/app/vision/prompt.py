"""The one versioned vision prompt. Every real adapter sends exactly this text.

Bump `PROMPT_VERSION` on any change to the wording or the JSON shape: each meal stores the version
it was analyzed with (`meal_logs.prompt_version`), and the evaluation harness reports it.

Instructions are in English; the model writes `description` and `items` in the user's language.
The prompt asks only for the fields of `VisionResult` (docs/api.md) plus a `status`, and forbids
calories, macros, grams, scores and healthy/unhealthy labels. It never includes the user's name,
e-mail or any other personal data: only the language tag.
"""

from __future__ import annotations

from app.domain import FOOD_GROUPS
from app.ports.vision import MealType

PROMPT_VERSION = "meal-v1"

COLORS: tuple[str, ...] = (
    "red",
    "orange",
    "yellow",
    "green",
    "blue",
    "purple",
    "pink",
    "brown",
    "beige",
    "white",
    "black",
)

LANGUAGE_NAMES = {"pt-BR": "Brazilian Portuguese", "en": "English"}

_TEMPLATE = """\
You describe photos of meals for a meal-logging app. You describe the plate; you never judge it.

Answer with one JSON object and nothing else, with exactly these keys:
- "status": "ok" if the photo shows food or drink, "not_food" if it clearly shows no food or \
drink, "unreadable" if it is too dark, blurry or cropped to tell.
- "description": one short, neutral sentence describing what is on the plate, written in \
{language}. At most 200 characters.
- "items": list of the foods and drinks you can see, each a short common name in {language} \
(for example "arroz", "feijão", "ovo frito"). At most 30.
- "meal_type": one of {meal_types}. Use the kind of food; if unclear, use "{default_meal}".
- "food_groups": the groups present, only from this list: {food_groups}. Do not invent groups.
- "item_count": the number of entries in "items".
- "colors": the main colors of the plate, only from this list: {colors}.
- "confidence": a number from 0 to 1, how sure you are about the items.
- "plate_share": an object mapping each group in "food_groups" to the fraction of the plate it \
covers (numbers from 0 to 1 that add up to about 1).

When "status" is not "ok", still return every key, with empty lists, an empty description, \
"item_count" 0, "confidence" 0 and an empty "plate_share".

Never include, in any field: calories, kilojoules, macronutrients, carbohydrates, fat or protein \
amounts, grams, portion weights, any score, rating or grade, and never words like healthy, \
unhealthy, good, bad, junk, clean, light or diet. Do not give advice. Do not mention the body, \
weight or health. Do not guess who the person is.
"""


def build_prompt(language: str) -> str:
    """The instructions for one analysis. `language` is a tag such as "pt-BR"."""
    return _TEMPLATE.format(
        language=LANGUAGE_NAMES.get(language, LANGUAGE_NAMES["pt-BR"]),
        meal_types=", ".join(f'"{m.value}"' for m in MealType),
        default_meal=MealType.SNACK.value,
        food_groups=", ".join(f'"{g}"' for g in FOOD_GROUPS),
        colors=", ".join(f'"{c}"' for c in COLORS),
    )
