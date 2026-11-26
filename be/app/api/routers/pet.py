"""Pet routes."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import Ctx, UserId
from app.api.schemas.pet import AttributeAllocation, PauseRequest, PetPatch, PetResponse
from app.services.get_pet import get_pet, spend_attributes, update_pet
from app.services.pause_pet import pause_pet, resume_pet

router = APIRouter(prefix="/pet", tags=["pet"])


@router.get("")
async def read_pet(ctx: Ctx, user_id: UserId) -> PetResponse:
    return PetResponse.from_view(await get_pet(ctx, user_id))


@router.patch("")
async def patch_pet(body: PetPatch, ctx: Ctx, user_id: UserId) -> PetResponse:
    view = await update_pet(ctx, user_id, name=body.name, color=body.color)
    return PetResponse.from_view(view)


@router.post("/pause")
async def start_pause(body: PauseRequest, ctx: Ctx, user_id: UserId) -> PetResponse:
    return PetResponse.from_view(await pause_pet(ctx, user_id, days=body.days))


@router.delete("/pause")
async def end_pause(ctx: Ctx, user_id: UserId) -> PetResponse:
    return PetResponse.from_view(await resume_pet(ctx, user_id))


@router.post("/attributes")
async def allocate_attributes(body: AttributeAllocation, ctx: Ctx, user_id: UserId) -> PetResponse:
    return PetResponse.from_view(await spend_attributes(ctx, user_id, body.allocations))
