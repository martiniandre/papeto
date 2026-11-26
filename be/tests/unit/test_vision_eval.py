"""Vision evaluation harness: scoring and a full run over a temporary folder with the fake."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest
from PIL import Image

from app.ports.vision import MealType, VisionResult
from app.providers.fake_vision import FakeFoodVision
from app.tools.vision_eval import Expected, _main, evaluate, load_expected, score_dish
from app.vision import VisionPipeline

RESULT = VisionResult(
    description="Arroz, feijão preto e salada.",
    items=["Arroz branco", "Feijão preto", "salada"],
    meal_type=MealType.LUNCH,
    food_groups=["grains", "legumes", "vegetables"],
    item_count=3,
    colors=["white"],
    confidence=0.9,
    plate_share={},
)


def test_score_dish_matches_items_ignoring_case_and_accents() -> None:
    expected = Expected(
        meal_type="lunch",
        food_groups=frozenset({"grains", "legumes", "protein"}),
        items=(("arroz",), ("feijao",), ("ovo", "omelete")),
    )
    score = score_dish("d.jpg", expected, RESULT)
    assert score.meal_type_ok
    assert not score.groups_exact
    assert (score.groups_tp, score.groups_fp, score.groups_fn) == (2, 1, 1)
    assert (score.items_found, score.items_expected) == (2, 3)


def test_load_expected_accepts_aliases(tmp_path: Path) -> None:
    path = tmp_path / "a.json"
    path.write_text(json.dumps({"meal_type": "snack", "items": ["maçã", ["pão", "torrada"]]}))
    expected = load_expected(path)
    assert expected.items == (("maçã",), ("pão", "torrada"))
    assert expected.food_groups == frozenset()


def _dish(
    folder: Path, name: str, expected: dict[str, object], *, photo: bytes | None = None
) -> None:
    if photo is None:
        out = io.BytesIO()
        Image.new("RGB", (64, 48), (10, len(name) * 20, 30)).save(out, format="JPEG")
        photo = out.getvalue()
    (folder / f"{name}.jpg").write_bytes(photo)
    (folder / f"{name}.json").write_text(json.dumps(expected), encoding="utf-8")


async def test_evaluate_runs_the_pipeline_and_counts_errors(tmp_path: Path) -> None:
    _dish(tmp_path, "one", {"meal_type": "lunch", "food_groups": ["grains"], "items": ["rice"]})
    _dish(tmp_path, "two", {"meal_type": "dinner", "items": ["x"]}, photo=b"broken")
    (tmp_path / "lonely.jpg").write_bytes(b"no json next to it")
    vision = VisionPipeline(FakeFoodVision(), max_upload_bytes=1024 * 1024)
    summary, scores = await evaluate(vision, tmp_path)
    assert [s.name for s in scores] == ["one.jpg", "two.jpg"]
    assert scores[1].error == "PhotoNotReadableError"
    assert summary.dishes == 2
    assert summary.errors == 1
    assert summary.provider == "fake"
    assert 0.0 <= summary.item_recall <= 0.5


async def test_cli_prints_a_report(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VISION_PROVIDER", "fake")
    monkeypatch.setenv("APP_ENV", "local")
    _dish(tmp_path, "one", {"meal_type": "lunch", "food_groups": ["grains"], "items": ["rice"]})
    assert await _main([str(tmp_path), "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["summary"]["dishes"] == 1
    assert report["summary"]["provider"] == "fake"


async def test_cli_fails_on_an_empty_folder(tmp_path: Path) -> None:
    assert await _main([str(tmp_path)]) == 1
