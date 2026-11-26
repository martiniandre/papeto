"""log_meal and the vision layer: provider metadata on the meal, Premium-only pet tip, sizes."""

from __future__ import annotations

from dataclasses import replace

import pytest

from app.domain import TIP_COPY
from app.ports import MealType
from app.providers.fake_vision import FakeFoodVision
from app.services.errors import PhotoTooLarge
from app.services.log_meal import log_manual_meal, log_meal
from app.vision import VisionPipeline
from tests.support.builders import PHOTO, make_premium, make_user, make_world


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


async def test_manual_meal_has_no_vision_metadata_and_no_tip() -> None:
    world = make_world()
    user_id = await make_user(world)
    await make_premium(world, user_id)
    result = await log_manual_meal(world.ctx, user_id, items=["arroz"], meal_type=MealType.LUNCH)
    assert result.meal.vision_provider is None
    assert result.pet_tip is None


async def test_pet_tip_is_premium_only() -> None:
    world = make_world()
    free_user = await make_user(world, email="free@example.com")
    premium_user = await make_user(world, email="premium@example.com")
    await make_premium(world, premium_user)
    assert (await log_meal(world.ctx, free_user, PHOTO)).pet_tip is None
    tip = (await log_meal(world.ctx, premium_user, PHOTO)).pet_tip
    assert tip in TIP_COPY.values()


async def test_pipeline_size_check_maps_to_photo_too_large() -> None:
    world = make_world()
    ctx = replace(world.ctx, vision=VisionPipeline(FakeFoodVision(), max_upload_bytes=10))
    user_id = await make_user(world)
    with pytest.raises(PhotoTooLarge):
        await log_meal(ctx, user_id, PHOTO)
    assert world.factory.store.usage == {}
