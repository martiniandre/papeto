"""Vision pipeline: resize and metadata stripping, retry on timeout, error mapping, validation."""

from __future__ import annotations

import asyncio
import io
from collections.abc import Callable

import pytest
from PIL import Image

from app.ports.vision import (
    MealType,
    NotFoodError,
    PhotoNotReadableError,
    PhotoTooLargeError,
    VisionResult,
    VisionTimeoutError,
    VisionUnavailableError,
)
from app.providers.fake_vision import FakeFoodVision
from app.vision import VisionPipeline, clean_result, has_forbidden_terms, prepare_image

MAX_BYTES = 8 * 1024 * 1024
GPS_IFD = 0x8825
ORIENTATION = 0x0112


def make_photo(
    size: tuple[int, int] = (3000, 2000),
    fmt: str = "JPEG",
    mode: str = "RGB",
    *,
    with_gps: bool = False,
    orientation: int | None = None,
) -> bytes:
    image = Image.new(mode, size, (200, 120, 40, 255)[: len(mode)])
    exif = Image.Exif()
    if with_gps:
        exif[0x010F] = "PhoneMaker"  # Make
        exif.get_ifd(GPS_IFD).update({1: "S", 2: (23.0, 33.0, 1.0), 3: "W", 4: (46.0, 38.0, 1.0)})
    if orientation is not None:
        exif[ORIENTATION] = orientation
    out = io.BytesIO()
    if fmt == "JPEG":
        image.save(out, format=fmt, exif=exif.tobytes())
    else:
        image.save(out, format=fmt)
    return out.getvalue()


def _open(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data))


def result(**overrides: object) -> VisionResult:
    base: dict[str, object] = {
        "description": "Arroz, feijão e salada.",
        "items": ["arroz", "feijão", "salada"],
        "meal_type": MealType.LUNCH,
        "food_groups": ["grains", "legumes", "vegetables"],
        "item_count": 3,
        "colors": ["white", "brown", "green"],
        "confidence": 0.9,
        "plate_share": {"grains": 0.4, "legumes": 0.3, "vegetables": 0.3},
    }
    base.update(overrides)
    return VisionResult.model_validate(base)


# --- resize ---------------------------------------------------------------------------------


def test_resize_caps_long_side_and_outputs_jpeg() -> None:
    out = _open(prepare_image(make_photo((4032, 3024)), max_bytes=MAX_BYTES))
    assert out.format == "JPEG"
    assert out.size == (1024, 768)


def test_resize_keeps_small_photos_and_portrait_ratio() -> None:
    assert _open(prepare_image(make_photo((640, 480)), max_bytes=MAX_BYTES)).size == (640, 480)
    assert _open(prepare_image(make_photo((1500, 3000)), max_bytes=MAX_BYTES)).size == (512, 1024)


def test_resize_strips_exif_and_gps() -> None:
    source = make_photo(with_gps=True)
    assert _open(source).getexif().get_ifd(GPS_IFD)  # the fixture really carries GPS
    out = _open(prepare_image(source, max_bytes=MAX_BYTES))
    assert len(out.getexif()) == 0
    assert "exif" not in out.info
    assert "icc_profile" not in out.info


def test_resize_applies_orientation_before_dropping_it() -> None:
    rotated = make_photo((2000, 1000), orientation=6)  # 90 degrees: the user saw a portrait
    assert _open(prepare_image(rotated, max_bytes=MAX_BYTES)).size == (512, 1024)


@pytest.mark.parametrize(("fmt", "mode"), [("PNG", "RGBA"), ("WEBP", "RGB"), ("PNG", "L")])
def test_resize_accepts_png_and_webp_as_rgb_jpeg(fmt: str, mode: str) -> None:
    out = _open(prepare_image(make_photo((1200, 900), fmt, mode), max_bytes=MAX_BYTES))
    assert (out.format, out.mode, out.size) == ("JPEG", "RGB", (1024, 768))


@pytest.mark.parametrize("data", [b"", b"jpeg-bytes", b"\xff\xd8\xff\xe0broken", b"GIF89a"])
def test_unreadable_bytes_are_photo_not_readable(data: bytes) -> None:
    with pytest.raises(PhotoNotReadableError):
        prepare_image(data, max_bytes=MAX_BYTES)


def test_disallowed_format_is_photo_not_readable() -> None:
    with pytest.raises(PhotoNotReadableError):
        prepare_image(make_photo((50, 50), "GIF", "P"), max_bytes=MAX_BYTES)


def test_size_is_checked_before_decoding() -> None:
    with pytest.raises(PhotoTooLargeError):
        prepare_image(b"x" * 101, max_bytes=100)


# --- retry and error mapping ----------------------------------------------------------------


class ScriptedVision:
    """Plays a script of outcomes, one per call: an exception to raise or a result to return."""

    provider_name = "scripted"
    model_version = "scripted-1"
    prompt_version: str | None = "v-test"

    def __init__(self, *outcomes: BaseException | VisionResult | Callable[[], object]) -> None:
        self.outcomes = list(outcomes)
        self.calls: list[bytes] = []

    async def analyze(self, image: bytes, language: str) -> VisionResult:
        self.calls.append(image)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        if isinstance(outcome, VisionResult):
            return outcome
        await asyncio.sleep(1)  # a callable means "hang"
        raise AssertionError("the pipeline timeout should have fired")


def pipeline(inner: ScriptedVision | FakeFoodVision, timeout: float = 5.0) -> VisionPipeline:
    return VisionPipeline(inner, max_upload_bytes=MAX_BYTES, timeout_seconds=timeout)


async def test_provider_receives_only_the_resized_jpeg() -> None:
    inner = ScriptedVision(result())
    await pipeline(inner).analyze(make_photo((4000, 3000), with_gps=True), "pt-BR")
    sent = _open(inner.calls[0])
    assert sent.size == (1024, 768)
    assert len(sent.getexif()) == 0


async def test_retries_once_on_adapter_timeout() -> None:
    inner = ScriptedVision(VisionTimeoutError(), result())
    out = await pipeline(inner).analyze(make_photo(), "pt-BR")
    assert out.items == ["arroz", "feijão", "salada"]
    assert len(inner.calls) == 2


async def test_retries_once_when_the_pipeline_timeout_fires() -> None:
    inner = ScriptedVision(lambda: None, result())
    await pipeline(inner, timeout=0.05).analyze(make_photo(), "pt-BR")
    assert len(inner.calls) == 2


async def test_two_timeouts_give_vision_unavailable() -> None:
    inner = ScriptedVision(VisionTimeoutError(), lambda: None)
    with pytest.raises(VisionTimeoutError) as caught:
        await pipeline(inner, timeout=0.05).analyze(make_photo(), "pt-BR")
    assert isinstance(caught.value, VisionUnavailableError)  # API answers VISION_UNAVAILABLE
    assert len(inner.calls) == 2


@pytest.mark.parametrize(
    "error", [NotFoodError(), PhotoNotReadableError(), VisionUnavailableError()]
)
async def test_port_errors_pass_through_without_retry(error: Exception) -> None:
    inner = ScriptedVision(error, result())
    with pytest.raises(type(error)):
        await pipeline(inner).analyze(make_photo(), "pt-BR")
    assert len(inner.calls) == 1


async def test_unexpected_adapter_errors_become_vision_unavailable() -> None:
    inner = ScriptedVision(KeyError("choices"))
    with pytest.raises(VisionUnavailableError):
        await pipeline(inner).analyze(make_photo(), "pt-BR")


async def test_unreadable_photo_never_reaches_the_provider() -> None:
    inner = ScriptedVision(result())
    with pytest.raises(PhotoNotReadableError):
        await pipeline(inner).analyze(b"not an image", "pt-BR")
    assert inner.calls == []


async def test_pipeline_exposes_adapter_identity() -> None:
    vision = pipeline(ScriptedVision())
    assert (vision.provider_name, vision.model_version, vision.prompt_version) == (
        "scripted",
        "scripted-1",
        "v-test",
    )


# --- validation and cleanup -----------------------------------------------------------------


def test_clean_result_keeps_only_the_food_group_vocabulary() -> None:
    out = clean_result(
        result(
            food_groups=["Grains", "sweets", "grains", "fruits"],
            plate_share={"grains": 0.5, "sweets": 0.3, "fruits": 0.2},
        )
    )
    assert out.food_groups == ["grains", "fruits"]
    assert out.plate_share == {"grains": 0.5, "fruits": 0.2}


def test_clean_result_normalizes_plate_share_above_one() -> None:
    out = clean_result(result(plate_share={"grains": 1.0, "legumes": 1.0, "vegetables": 0.0}))
    assert sum(out.plate_share.values()) == pytest.approx(1.0)


def test_clean_result_drops_forbidden_text_and_recounts_items() -> None:
    out = clean_result(
        result(
            description="Prato saudável com 450 kcal.",
            items=["arroz", "  arroz ", "150 g de frango", "salada", ""],
            item_count=9,
            new_foods=["x"],
        )
    )
    assert out.description == ""
    assert out.items == ["arroz", "salada"]
    assert out.item_count == 2
    assert out.new_foods == []


@pytest.mark.parametrize(
    "text",
    ["450 kcal", "Calorias: 300", "rich in carbs", "200g", "healthy bowl", "comida saudável"],
)
def test_forbidden_terms_are_detected(text: str) -> None:
    assert has_forbidden_terms(text)


@pytest.mark.parametrize("text", ["Arroz, feijão e salada verde.", "Pão de queijo e café"])
def test_plain_descriptions_are_allowed(text: str) -> None:
    assert not has_forbidden_terms(text)


def test_clean_result_rejects_invalid_answers() -> None:
    bad = result().model_copy(update={"confidence": 3.0})  # model_copy skips validation
    with pytest.raises(VisionUnavailableError):
        clean_result(bad)
