"""Provider-neutral vision pipeline: check, resize, call `FoodVisionProvider`, retry, validate.

Any adapter in `app/providers` plugs in behind `VisionPipeline`; nothing here knows a vendor.
Meal photos only live in memory during one call: they are never stored or logged.
"""

from app.vision.image import ALLOWED_FORMATS, MAX_SIDE, prepare_image
from app.vision.pipeline import VisionPipeline
from app.vision.result import clean_result, has_forbidden_terms

__all__ = [
    "ALLOWED_FORMATS",
    "MAX_SIDE",
    "VisionPipeline",
    "clean_result",
    "has_forbidden_terms",
    "prepare_image",
]
