"""Photo checks and resize before any provider call (RNF-22).

Order: empty or too large -> decode header -> allowed format -> pixel cap -> apply EXIF orientation
-> shrink to `MAX_SIDE` on the long side -> re-encode as a fresh JPEG with no metadata (no EXIF,
GPS, ICC or XMP). Anything Pillow cannot decode is `PhotoNotReadableError`.
"""

from __future__ import annotations

import io
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError

from app.ports.vision import PhotoNotReadableError, PhotoTooLargeError

MAX_SIDE = 1024
JPEG_QUALITY = 85
MAX_PIXELS = 50_000_000  # well above any phone camera; blocks decompression bombs
# HEIC/HEIF needs a plugin Pillow does not ship; such uploads answer PHOTO_NOT_READABLE for now.
ALLOWED_FORMATS = frozenset({"JPEG", "PNG", "WEBP", "MPO"})  # MPO: multi-picture JPEG from phones


def prepare_image(data: bytes, *, max_bytes: int, max_side: int = MAX_SIDE) -> bytes:
    """A JPEG of at most `max_side` px on the long side, stripped of every metadata block."""
    if not data:
        raise PhotoNotReadableError
    if len(data) > max_bytes:
        raise PhotoTooLargeError
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as source:
                if source.format not in ALLOWED_FORMATS:
                    raise PhotoNotReadableError
                if source.width * source.height > MAX_PIXELS:
                    raise PhotoNotReadableError
                image = ImageOps.exif_transpose(source)  # keep the orientation the user saw
                image.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)  # never upscales
                rgb = _flatten(image)
    except PhotoNotReadableError:
        raise
    except (
        UnidentifiedImageError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        OSError,
        ValueError,
        SyntaxError,  # raised by some Pillow decoders on corrupt headers
    ) as exc:
        raise PhotoNotReadableError from exc
    clean = Image.new("RGB", rgb.size)  # fresh image: carries no `info` metadata at all
    clean.paste(rgb)
    out = io.BytesIO()
    clean.save(out, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return out.getvalue()


def _flatten(image: Image.Image) -> Image.Image:
    """RGB on a white background (transparent PNG/WebP areas would otherwise turn black)."""
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return image.convert("RGB")
