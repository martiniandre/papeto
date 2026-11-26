"""Register, login and refresh."""

from __future__ import annotations

from dataclasses import replace

from app.domain import new_pet
from app.ports import InvalidTokenError, TokenKind
from app.ports.repositories import DuplicateEmailError, PetRecord, UserRecord
from app.services.common import parse_timezone
from app.services.context import ServiceContext
from app.services.errors import (
    AdultConfirmationRequired,
    EmailAlreadyRegistered,
    InvalidCredentials,
    InvalidToken,
)
from app.services.views import TokenPair

DEFAULT_PET_COLOR = "default"


def normalize_email(email: str) -> str:
    return email.strip().lower()


def _issue(ctx: ServiceContext, user: UserRecord) -> TokenPair:
    return TokenPair(
        access_token=ctx.auth.create_token(user.id, TokenKind.ACCESS),
        refresh_token=ctx.auth.create_token(user.id, TokenKind.REFRESH),
        expires_in=ctx.auth.access_ttl_seconds,
    )


async def register(
    ctx: ServiceContext,
    *,
    email: str,
    password: str,
    name: str,
    timezone: str | None,
    adult_confirmed: bool,
) -> TokenPair:
    if not adult_confirmed:
        raise AdultConfirmationRequired
    zone_name = timezone or ctx.default_timezone
    zone = parse_timezone(zone_name)
    now = ctx.clock.now()
    user = UserRecord(
        id=ctx.ids.new_id(),
        email=normalize_email(email),
        password_hash=ctx.auth.hash_password(password),
        name=name.strip(),
        timezone=zone_name,
        analytics_opt_out=False,
        adult_confirmed_at=now,
        created_at=now,
    )
    state = new_pet(ctx.clock.today(zone), ctx.rules)
    pet = PetRecord(
        id=ctx.ids.new_id(),
        user_id=user.id,
        name=None,  # the user names the pet on screen 43
        color=DEFAULT_PET_COLOR,
        state=state,
        last_seen_lives=state.lives,
        created_at=now,
    )
    async with ctx.uow_factory() as uow:
        if await uow.users.get_by_email(user.email) is not None:
            raise EmailAlreadyRegistered
        try:
            await uow.users.add(user)
        except DuplicateEmailError as exc:
            raise EmailAlreadyRegistered from exc
        await uow.pets.add(pet)
        await uow.commit()
    return _issue(ctx, user)


async def login(ctx: ServiceContext, *, email: str, password: str) -> TokenPair:
    async with ctx.uow_factory() as uow:
        user = await uow.users.get_by_email(normalize_email(email))
        if user is None or user.password_hash is None:
            ctx.auth.hash_password(password)  # spend similar time whether or not the email exists
            raise InvalidCredentials
        if not ctx.auth.verify_password(password, user.password_hash):
            raise InvalidCredentials
        if user.deletion_requested_at is not None:
            # Signing in during the 30-day window cancels the pending deletion.
            user = replace(user, deletion_requested_at=None)
            await uow.users.save(user)
            await uow.commit()
    return _issue(ctx, user)


async def refresh(ctx: ServiceContext, *, refresh_token: str) -> TokenPair:
    try:
        user_id = ctx.auth.decode_token(refresh_token, TokenKind.REFRESH)
    except InvalidTokenError as exc:
        raise InvalidToken from exc
    async with ctx.uow_factory() as uow:
        user = await uow.users.get(user_id)
    if user is None:
        raise InvalidToken
    return _issue(ctx, user)
