"""Evaluate the configured vision provider on a local folder of dish photos.

    uv run python -m app.tools.vision_eval <folder> [--language pt-BR] [--json]

Each photo (`.jpg`, `.jpeg`, `.png`, `.webp`) needs a JSON file with the same stem next to it:

    {"meal_type": "lunch",
     "food_groups": ["grains", "legumes", "vegetables"],
     "items": ["arroz", ["feijão", "feijão preto"], "salada"]}

An entry in `items` may be a list of accepted names. An expected item counts as found when a
returned item contains it (case and accents ignored). Photos run through the same pipeline as
`POST /v1/meals` (resize, retry, validation) with the provider picked by `VISION_PROVIDER`.
Photos are only read from disk; nothing is written, uploaded elsewhere or logged.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path

from pydantic import SecretStr

from app.config import Settings
from app.container import build_vision
from app.logging import configure_logging
from app.ports import FoodVisionProvider, VisionResult

PHOTO_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp")


@dataclass(frozen=True)
class Expected:
    meal_type: str
    food_groups: frozenset[str]
    items: tuple[tuple[str, ...], ...]  # each entry: accepted names for one item


@dataclass
class DishScore:
    name: str
    error: str | None = None
    meal_type_ok: bool = False
    groups_exact: bool = False
    groups_tp: int = 0
    groups_fp: int = 0
    groups_fn: int = 0
    items_found: int = 0
    items_expected: int = 0
    seconds: float = 0.0
    returned_items: list[str] = field(default_factory=list)


@dataclass
class Summary:
    provider: str
    model_version: str
    prompt_version: str | None
    dishes: int
    errors: int
    meal_type_accuracy: float
    food_groups_exact_accuracy: float
    food_groups_precision: float
    food_groups_recall: float
    item_recall: float
    mean_seconds: float


def _norm(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return " ".join("".join(c for c in decomposed if not unicodedata.combining(c)).split())


def load_expected(path: Path) -> Expected:
    data = json.loads(path.read_text(encoding="utf-8"))
    items = tuple(
        tuple(entry) if isinstance(entry, list) else (entry,) for entry in data.get("items", [])
    )
    return Expected(
        meal_type=str(data["meal_type"]),
        food_groups=frozenset(str(g).lower() for g in data.get("food_groups", [])),
        items=items,
    )


def score_dish(name: str, expected: Expected, result: VisionResult) -> DishScore:
    got_groups = {g.lower() for g in result.food_groups}
    returned = [_norm(item) for item in result.items]
    found = sum(
        1
        for names in expected.items
        if any(_norm(alias) in candidate for alias in names for candidate in returned)
    )
    return DishScore(
        name=name,
        meal_type_ok=result.meal_type.value == expected.meal_type,
        groups_exact=got_groups == expected.food_groups,
        groups_tp=len(got_groups & expected.food_groups),
        groups_fp=len(got_groups - expected.food_groups),
        groups_fn=len(expected.food_groups - got_groups),
        items_found=found,
        items_expected=len(expected.items),
        returned_items=list(result.items),
    )


def _ratio(num: int, den: int) -> float:
    return round(num / den, 3) if den else 0.0


def summarize(vision: FoodVisionProvider, scores: list[DishScore]) -> Summary:
    ok = [s for s in scores if s.error is None]
    tp = sum(s.groups_tp for s in ok)
    return Summary(
        provider=vision.provider_name,
        model_version=vision.model_version,
        prompt_version=vision.prompt_version,
        dishes=len(scores),
        errors=len(scores) - len(ok),
        # Failed dishes count as misses, so errors lower every accuracy.
        meal_type_accuracy=_ratio(sum(s.meal_type_ok for s in ok), len(scores)),
        food_groups_exact_accuracy=_ratio(sum(s.groups_exact for s in ok), len(scores)),
        food_groups_precision=_ratio(tp, tp + sum(s.groups_fp for s in ok)),
        food_groups_recall=_ratio(tp, tp + sum(s.groups_fn for s in ok)),
        item_recall=_ratio(sum(s.items_found for s in ok), sum(s.items_expected for s in scores)),
        mean_seconds=round(sum(s.seconds for s in scores) / len(scores), 2) if scores else 0.0,
    )


def find_dishes(folder: Path) -> list[tuple[Path, Path]]:
    pairs = []
    for photo in sorted(folder.iterdir()):
        if photo.suffix.lower() in PHOTO_SUFFIXES:
            expected = photo.with_suffix(".json")
            if expected.exists():
                pairs.append((photo, expected))
    return pairs


async def evaluate(
    vision: FoodVisionProvider, folder: Path, language: str = "pt-BR"
) -> tuple[Summary, list[DishScore]]:
    scores: list[DishScore] = []
    for photo, expected_path in find_dishes(folder):
        expected = load_expected(expected_path)
        started = time.perf_counter()
        try:
            result = await vision.analyze(photo.read_bytes(), language)
        except Exception as exc:  # report and keep going: one bad dish must not stop the run
            score = DishScore(name=photo.name, error=type(exc).__name__)
            score.items_expected = len(expected.items)
        else:
            score = score_dish(photo.name, expected, result)
        score.seconds = round(time.perf_counter() - started, 2)
        scores.append(score)
    return summarize(vision, scores), scores


def _print_report(summary: Summary, scores: list[DishScore]) -> None:
    for s in scores:
        if s.error:
            print(f"  {s.name}: ERROR {s.error} ({s.seconds}s)")
            continue
        print(
            f"  {s.name}: meal_type {'ok' if s.meal_type_ok else 'miss'}, "
            f"groups {'exact' if s.groups_exact else 'diff'}, "
            f"items {s.items_found}/{s.items_expected} ({s.seconds}s) "
            f"-> {', '.join(s.returned_items)}"
        )
    print()
    print(
        f"provider={summary.provider} model={summary.model_version} "
        f"prompt={summary.prompt_version} dishes={summary.dishes} errors={summary.errors}"
    )
    print(f"meal_type accuracy        {summary.meal_type_accuracy:.1%}")
    print(f"food_groups exact match   {summary.food_groups_exact_accuracy:.1%}")
    print(f"food_groups precision     {summary.food_groups_precision:.1%}")
    print(f"food_groups recall        {summary.food_groups_recall:.1%}")
    print(f"item recall               {summary.item_recall:.1%}")
    print(f"mean seconds per photo    {summary.mean_seconds}")


async def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.tools.vision_eval")
    parser.add_argument("folder", type=Path)
    parser.add_argument("--language", default="pt-BR")
    parser.add_argument("--json", action="store_true", help="print a JSON report instead")
    args = parser.parse_args(argv)
    if not args.folder.is_dir():
        parser.error(f"{args.folder} is not a folder")
    configure_logging("WARNING")
    # The API's JWT secret is irrelevant here; everything else comes from the environment.
    settings = Settings(jwt_secret=SecretStr("vision-eval-does-not-sign-tokens"))
    vision = build_vision(settings)
    try:
        summary, scores = await evaluate(vision, args.folder, args.language)
    finally:
        close = getattr(vision.inner, "aclose", None)
        if close is not None:
            await close()
    if not scores:
        print("No photo with a matching .json file found.", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps({"summary": asdict(summary), "dishes": [asdict(s) for s in scores]}))
    else:
        _print_report(summary, scores)
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(_main(sys.argv[1:])))


if __name__ == "__main__":
    main()
