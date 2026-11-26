"""log_meal and the vision layer: provider metadata on the meal and the size check."""

from __future__ import annotations

from dataclasses import replace

import pytest

from app.providers.fake_vision import FakeFoodVision
from app.services.errors import PhotoTooLarge
from app.services.log_meal import log_meal
from app.vision import VisionPipeline
from tests.support.builders import PHOTO, make_user, make_world


async def test_photo_meal_records_provider_model_and_prompt() -> None:
    world = make_world()
    user_id = await make_user(world)
    result = await log_meal(world.ctx, user_id, PHOTO)
    stored = world.factory.store.meals[result.meal.id]
    assert (stored.vision_provider, stored.model_version, stored.prompt_version) == (
        "fake",
        "fake-1",
        None,
    )


async def test_pipeline_size_check_maps_to_photo_too_large() -> None:
    world = make_world()
    ctx = replace(world.ctx, vision=VisionPipeline(FakeFoodVision(), max_upload_bytes=10))
    user_id = await make_user(world)
    with pytest.raises(PhotoTooLarge):
        await log_meal(ctx, user_id, PHOTO)
    assert world.factory.store.usage == {}
