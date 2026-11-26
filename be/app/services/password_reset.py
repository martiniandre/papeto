"""Forgot and reset password.

`request_password_reset` never tells the caller whether the email exists: the API always answers
202 with the same body. The token is random (256 bits), single use and short-lived; only its
SHA-256 hash is stored, and neither the token nor the email is ever logged.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import replace
from datetime import timedelta
from urllib.parse import urlencode
from uuid import UUID

from app.i18n import translate
from app.ports.repositories import PasswordResetRecord
from app.services.auth import normalize_email
from app.services.context import ServiceContext
from app.services.errors import InvalidResetToken

_RATE_WINDOW = timedelta(hours=1)


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def reset_link(base_url: str, token: str) -> str:
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{urlencode({'token': token})}"


async def request_password_reset(ctx: ServiceContext, *, email: str) -> None:
    """Send a reset link if the account exists and is under the hourly cap. Silent otherwise."""
    now = ctx.clock.now()
    async with ctx.uow_factory() as uow:
        user = await uow.users.get_by_email(normalize_email(email))
        if user is None:
            return
        recent = await uow.password_resets.count_since(user.id, now - _RATE_WINDOW)
        if recent >= ctx.password_reset_max_per_hour:
            return  # rate limited: still 202, nothing sent
        token = secrets.token_urlsafe(32)
        await uow.password_resets.add(
            PasswordResetRecord(
                id=ctx.ids.new_id(),
                user_id=user.id,
                token_hash=hash_reset_token(token),
                created_at=now,
                expires_at=now + timedelta(minutes=ctx.password_reset_minutes),
            )
        )
        await uow.commit()
        to = user.email
    try:
        await ctx.email.send(
            to,
            translate("password_reset.subject"),
            translate(
                "password_reset.body",
                minutes=ctx.password_reset_minutes,
                link=reset_link(ctx.password_reset_url, token),
            ),
        )
    except Exception as exc:  # a send failure must not reveal that the account exists
        ctx.error_reporter.capture(exc)


async def reset_password(ctx: ServiceContext, *, token: str, new_password: str) -> UUID:
    """Set a new password with a valid token. Every open token of the user becomes used."""
    now = ctx.clock.now()
    async with ctx.uow_factory() as uow:
        reset = await uow.password_resets.get_by_hash(hash_reset_token(token))
        if reset is None or reset.used_at is not None or reset.expires_at <= now:
            raise InvalidResetToken
        user = await uow.users.get(reset.user_id)
        if user is None:
            raise InvalidResetToken
        await uow.users.save(replace(user, password_hash=ctx.auth.hash_password(new_password)))
        await uow.password_resets.use_all(user.id, now)
        await uow.commit()
    return user.id
