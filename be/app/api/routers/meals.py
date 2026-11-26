"""Meal routes. The photo is read into memory, analyzed and dropped: never stored or logged."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, UploadFile

from app.api.deps import Ctx, UserId, get_max_upload_bytes
from app.api.errors import ApiError, ErrorCode
from app.api.schemas.meals import (
    LogMealResponse,
    ManualMealRequest,
    MealListResponse,
    MealOut,
    MealPatch,
)
from app.services import meals as meal_service
from app.services.log_meal import log_manual_meal, log_meal
from app.services.meals import MealRange

router = APIRouter(prefix="/meals", tags=["meals"])

ALLOWED_CONTENT_TYPES = frozenset(
    {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
)
_READ_CHUNK = 256 * 1024


async def _read_photo(photo: UploadFile, max_bytes: int) -> bytes:
    if (photo.content_type or "").lower() not in ALLOWED_CONTENT_TYPES:
        raise ApiError(ErrorCode.PHOTO_NOT_READABLE, "Send a JPEG, PNG, WebP or HEIC photo.")
    data = bytearray()
    while chunk := await photo.read(_READ_CHUNK):
        data.extend(chunk)
        if len(data) > max_bytes:
            raise ApiError(ErrorCode.PHOTO_TOO_LARGE, "The photo is too large.")
    return bytes(data)


@router.post("", status_code=201)
async def create_meal(
    photo: UploadFile,
    ctx: Ctx,
    user_id: UserId,
    max_bytes: Annotated[int, Depends(get_max_upload_bytes)],
) -> LogMealResponse:
    image = await _read_photo(photo, max_bytes)
    return LogMealResponse.from_result(await log_meal(ctx, user_id, image))


@router.post("/manual", status_code=201)
async def create_manual_meal(body: ManualMealRequest, ctx: Ctx, user_id: UserId) -> LogMealResponse:
    """RF-95: log a meal by hand when the photo could not be read. No AI, no photo limit."""
    result = await log_manual_meal(ctx, user_id, items=body.items, meal_type=body.meal_type)
    return LogMealResponse.from_result(result)


@router.get("")
async def list_meals(
    ctx: Ctx,
    user_id: UserId,
    meal_range: Annotated[MealRange, Query(alias="range")] = MealRange.TODAY,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=meal_service.MAX_PAGE_SIZE)] = (
        meal_service.DEFAULT_PAGE_SIZE
    ),
) -> MealListResponse:
    page = await meal_service.list_meals(
        ctx, user_id, meal_range=meal_range, cursor=cursor, limit=limit
    )
    return MealListResponse.from_page(page)


@router.get("/{meal_id}")
async def read_meal(meal_id: UUID, ctx: Ctx, user_id: UserId) -> MealOut:
    return MealOut.from_record(await meal_service.get_meal(ctx, user_id, meal_id))


@router.patch("/{meal_id}")
async def patch_meal(meal_id: UUID, body: MealPatch, ctx: Ctx, user_id: UserId) -> MealOut:
    meal = await meal_service.update_meal(
        ctx, user_id, meal_id, items=body.items, meal_type=body.meal_type
    )
    return MealOut.from_record(meal)


@router.delete("/{meal_id}", status_code=204)
async def remove_meal(meal_id: UUID, ctx: Ctx, user_id: UserId) -> Response:
    await meal_service.delete_meal(ctx, user_id, meal_id)
    return Response(status_code=204)
