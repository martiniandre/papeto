"""Register, login (email or Google) and refresh."""

from __future__ import annotations

from dataclasses import dataclass, replace

from app.domain import ProductEvent, new_pet
from app.ports import (
    AuthProviderUnavailableError,
    GoogleIdentity,
    InvalidTokenError,
    SocialEmailNotVerifiedError,
    SocialTokenInvalidError,
    TokenKind,
)
from app.ports.repositories import AuthMethod, DuplicateEmailError, PetRecord, UserRecord
from app.services.analytics import track
from app.services.common import parse_timezone
from app.services.context import ServiceContext
from app.services.errors import (
    AdultConfirmationRequired,
    AuthProviderUnavailable,
    EmailAlreadyRegistered,
    GoogleEmailNotVerified,
    GoogleTokenInvalid,
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


def _new_pet(ctx: ServiceContext, user: UserRecord) -> PetRecord:
    state = new_pet(ctx.clock.today(parse_timezone(user.timezone)), ctx.rules)
    return PetRecord(
        id=ctx.ids.new_id(),
        user_id=user.id,
        name=None,  # the user names the pet on screen 43
        color=DEFAULT_PET_COLOR,
        state=state,
        last_seen_lives=state.lives,
        created_at=user.created_at,
        last_seen_level=1,
    )


def _cancel_pending_deletion(user: UserRecord) -> UserRecord:
    # Signing in during the 30-day window cancels the pending deletion.
    return replace(user, deletion_requested_at=None)


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
    parse_timezone(zone_name)
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
    pet = _new_pet(ctx, user)
    async with ctx.uow_factory() as uow:
        if await uow.users.get_by_email(user.email) is not None:
            raise EmailAlreadyRegistered
        try:
            await uow.users.add(user)
        except DuplicateEmailError as exc:
            raise EmailAlreadyRegistered from exc
        await uow.pets.add(pet)
        await uow.commit()
    await track(ctx, user, ProductEvent.SIGNUP_COMPLETED)
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
            user = _cancel_pending_deletion(user)
            await uow.users.save(user)
            await uow.commit()
    return _issue(ctx, user)


@dataclass(frozen=True, slots=True)
class GoogleSignIn:
    tokens: TokenPair
    is_new_user: bool


async def _verified_google_identity(ctx: ServiceContext, id_token: str) -> GoogleIdentity:
    try:
        return await ctx.auth.verify_google_id_token(id_token)
    except SocialTokenInvalidError as exc:
        raise GoogleTokenInvalid from exc
    except SocialEmailNotVerifiedError as exc:
        raise GoogleEmailNotVerified from exc
    except AuthProviderUnavailableError as exc:
        raise AuthProviderUnavailable from exc


async def google_sign_in(
    ctx: ServiceContext, *, id_token: str, timezone: str | None
) -> GoogleSignIn:
    """Sign in or sign up with a verified Google ID token (ADR 013).

    1. A user already linked to this Google subject signs in.
    2. Otherwise a user with the same (Google-verified) email gets the subject linked and signs in.
    3. Otherwise a new account is created with no password and no adult confirmation yet: pet
       and meal endpoints answer 403 ADULT_CONFIRMATION_REQUIRED until `PATCH /me`.
    Signing in cancels a pending deletion, same as the email login.
    """
    identity = await _verified_google_identity(ctx, id_token)
    zone_name = timezone or ctx.default_timezone
    parse_timezone(zone_name)
    email = normalize_email(identity.email)
    for attempt in range(2):  # a parallel first sign-in may win the unique email/subject race
        try:
            return await _google_sign_in_once(ctx, identity, email, zone_name)
        except DuplicateEmailError:
            if attempt:
                raise
    raise AssertionError("unreachable")


async def _google_sign_in_once(
    ctx: ServiceContext, identity: GoogleIdentity, email: str, zone_name: str
) -> GoogleSignIn:
    async with ctx.uow_factory() as uow:
        user = await uow.users.get_by_google_subject(identity.subject)
        if user is None:
            # Safe to trust: the verifier only returns emails Google marked as verified.
            user = await uow.users.get_by_email(email)
        if user is not None:
            changed = user
            if changed.google_subject != identity.subject:
                changed = replace(changed, google_subject=identity.subject)
            if changed.deletion_requested_at is not None:
                changed = _cancel_pending_deletion(changed)
            if changed != user:
                await uow.users.save(changed)
                await uow.commit()
            return GoogleSignIn(tokens=_issue(ctx, changed), is_new_user=False)

        now = ctx.clock.now()
        user = UserRecord(
            id=ctx.ids.new_id(),
            email=email,
            password_hash=None,
            name=(identity.name or "")[:100],
            timezone=zone_name,
            analytics_opt_out=False,
            adult_confirmed_at=None,
            created_at=now,
            auth_provider=AuthMethod.GOOGLE,
            google_subject=identity.subject,
        )
        await uow.users.add(user)
        await uow.pets.add(_new_pet(ctx, user))
        await uow.commit()
    await track(ctx, user, ProductEvent.SIGNUP_COMPLETED)
    return GoogleSignIn(tokens=_issue(ctx, user), is_new_user=True)


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
