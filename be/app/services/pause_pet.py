"""Pause and resume the pet (Premium)."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from uuid import UUID

from app.domain import Plan, is_paused
from app.ports.repositories import PauseRecord
from app.services.common import current_plan, require_adult_user
from app.services.context import ServiceContext
from app.services.errors import PetAlreadyPaused, PetNotPaused, PremiumRequired, ValidationFailed
from app.services.get_pet import load_pet, settle_and_save
from app.services.views import PetView

ALLOWED_PAUSE_DAYS = (1, 3, 7)


async def pause_pet(ctx: ServiceContext, user_id: UUID, *, days: int) -> PetView:
    if days not in ALLOWED_PAUSE_DAYS:
        raise ValidationFailed("Pause must be 1, 3 or 7 days.")
    now = ctx.clock.now()
    async with ctx.uow_factory() as uow:
        user = await require_adult_user(uow, user_id)
        if await current_plan(uow, user_id, now) is not Plan.PREMIUM:
            raise PremiumRequired
        pet = await load_pet(uow, user_id)
        # Charge missed days up to today before the pause starts.
        pet, _ = await settle_and_save(ctx, uow, user, pet)
        if is_paused(pet.state, now):
            raise PetAlreadyPaused
        ends_at = now + timedelta(days=days)
        await uow.pauses.add(
            PauseRecord(id=ctx.ids.new_id(), user_id=user_id, started_at=now, ends_at=ends_at)
        )
        pet = replace(pet, state=replace(pet.state, rest_until=ends_at))
        await uow.pets.save(pet)
        _, view = await settle_and_save(ctx, uow, user, pet)
        await uow.commit()
        return view


async def resume_pet(ctx: ServiceContext, user_id: UUID) -> PetView:
    now = ctx.clock.now()
    async with ctx.uow_factory() as uow:
        user = await require_adult_user(uow, user_id)
        pet = await load_pet(uow, user_id)
        if not is_paused(pet.state, now):
            raise PetNotPaused
        await uow.pauses.end_active(user_id, now)
        pet = replace(pet, state=replace(pet.state, rest_until=now))
        await uow.pets.save(pet)
        _, view = await settle_and_save(ctx, uow, user, pet)
        await uow.commit()
        return view
