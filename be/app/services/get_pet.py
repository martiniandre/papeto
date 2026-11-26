"""Read and edit the pet. Reads settle missed days lazily (no cron)."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import replace
from uuid import UUID

from app.domain import (
    Attribute,
    NotEnoughAttributePointsError,
    ProductEvent,
    level_events,
    level_for_points,
    read_events,
    spend_attribute_points,
)
from app.ports.repositories import PetRecord, UnitOfWork, UserRecord
from app.services.analytics import life_change_events, track_all
from app.services.common import build_pet_view, parse_timezone, require_user, settled_state
from app.services.context import ServiceContext
from app.services.errors import NotEnoughPoints, PetNotFound, ValidationFailed
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
    """Settle missed days, compute events from the last seen lives and level, persist the result."""
    now = ctx.clock.now()
    zone = parse_timezone(user.timezone)
    today = ctx.clock.today(zone)
    state = await settled_state(uow, user.id, pet, zone, today)
    level = level_for_points(await uow.points.total(user.id), ctx.rules)
    events = read_events(pet.last_seen_lives, state.lives) + level_events(
        pet.last_seen_level, level
    )
    saved = replace(pet, state=state, last_seen_lives=state.lives, last_seen_level=level)
    await uow.pets.save(saved)
    view = await build_pet_view(uow, saved, state, today, now, events, ctx.rules, zone)
    return saved, view


async def get_pet(ctx: ServiceContext, user_id: UUID) -> PetView:
    async with ctx.uow_factory() as uow:
        user = await require_user(uow, user_id)
        pet = await load_pet(uow, user_id)
        _, view = await settle_and_save(ctx, uow, user, pet)
        await uow.commit()
    await track_all(ctx, user, life_change_events(pet.last_seen_lives, view.lives))
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
        was_unnamed = pet.name is None
        last_seen = pet.last_seen_lives
        pet = replace(pet, name=name or pet.name, color=color or pet.color)
        _, view = await settle_and_save(ctx, uow, user, pet)
        await uow.commit()
    events = life_change_events(last_seen, view.lives)
    if was_unnamed and name is not None:
        events.append((ProductEvent.PET_NAMED, {}))
    await track_all(ctx, user, events)
    return view


async def spend_attributes(
    ctx: ServiceContext, user_id: UUID, allocations: Mapping[Attribute, int]
) -> PetView:
    """Spend unspent attribute points, all or nothing, under the pet row lock."""
    async with ctx.uow_factory() as uow:
        user = await require_user(uow, user_id)
        pet = await load_pet(uow, user_id)  # row lock: parallel requests cannot overspend
        last_seen = pet.last_seen_lives
        level = level_for_points(await uow.points.total(user_id), ctx.rules)
        try:
            attributes = spend_attribute_points(pet.attributes, allocations, level)
        except NotEnoughAttributePointsError as exc:
            raise NotEnoughPoints from exc
        except ValueError as exc:
            raise ValidationFailed("Allocations must be positive whole numbers.") from exc
        _, view = await settle_and_save(ctx, uow, user, replace(pet, attributes=attributes))
        await uow.commit()
    await track_all(ctx, user, life_change_events(last_seen, view.lives))
    return view
