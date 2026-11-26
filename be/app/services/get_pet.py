"""Read and edit the pet. Reads settle missed days lazily (no cron)."""

from __future__ import annotations

import re
from dataclasses import replace
from uuid import UUID

from app.domain import read_events
from app.ports.repositories import PetRecord, UnitOfWork, UserRecord
from app.services.common import build_pet_view, parse_timezone, require_user, settled_state
from app.services.context import ServiceContext
from app.services.errors import PetNotFound, ValidationFailed
from app.services.views import PetView

MAX_NAME_LENGTH = 20
_COLOR = re.compile(r"^[a-z0-9_-]{1,20}$")


async def load_pet(uow: UnitOfWork, user_id: UUID) -> PetRecord:
    pet = await uow.pets.get(user_id, for_update=True)
    if pet is None:
        raise PetNotFound
    return pet


async def settle_and_save(
    ctx: ServiceContext, uow: UnitOfWork, user: UserRecord, pet: PetRecord
) -> tuple[PetRecord, PetView]:
    """Settle missed days, compute events from the last seen lives and persist the result."""
    now = ctx.clock.now()
    zone = parse_timezone(user.timezone)
    today = ctx.clock.today(zone)
    state = await settled_state(uow, user.id, pet, zone, today)
    events = read_events(pet.last_seen_lives, state.lives)
    saved = replace(pet, state=state, last_seen_lives=state.lives)
    await uow.pets.save(saved)
    view = await build_pet_view(uow, saved, state, today, now, events, ctx.rules)
    return saved, view


async def get_pet(ctx: ServiceContext, user_id: UUID) -> PetView:
    async with ctx.uow_factory() as uow:
        user = await require_user(uow, user_id)
        pet = await load_pet(uow, user_id)
        _, view = await settle_and_save(ctx, uow, user, pet)
        await uow.commit()
        return view


async def update_pet(
    ctx: ServiceContext, user_id: UUID, *, name: str | None, color: str | None
) -> PetView:
    if name is not None:
        name = name.strip()
        if not 1 <= len(name) <= MAX_NAME_LENGTH:
            raise ValidationFailed(f"Pet name must have 1 to {MAX_NAME_LENGTH} characters.")
    if color is not None and not _COLOR.match(color):
        raise ValidationFailed("Pet color is not valid.")
    async with ctx.uow_factory() as uow:
        user = await require_user(uow, user_id)
        pet = await load_pet(uow, user_id)
        pet = replace(pet, name=name or pet.name, color=color or pet.color)
        _, view = await settle_and_save(ctx, uow, user, pet)
        await uow.commit()
        return view
