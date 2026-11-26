"""Decide and send pet notices (RF-40 to RF-42). Reads the mood; never changes lives.

`run_notice_cycle` is called by the ARQ cron task every few minutes. For each user it settles the
pet *in memory only* (nothing is saved), computes the mood and asks the domain whether a notice is
due. The decision is recorded first (unique per user, kind and episode), then pushed to the user's
devices, so a crash or a second worker can never cause a duplicate.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

import structlog

from app.domain import NoticeKind, compute_mood, decide_notice, pick_copy
from app.ports import PushOutcome, PushProvider, PushUnavailableError
from app.ports.repositories import ConsentType, NoticeRecord, UserRecord
from app.services.common import parse_timezone, settled_state
from app.services.context import ServiceContext
from app.services.errors import InvalidTimezone

log = structlog.get_logger()

PAGE_SIZE = 200
# A pet that never had a log is in one single episode until its first log.
NEVER_LOGGED_EPISODE = date.min


@dataclass(frozen=True, slots=True)
class NoticeReport:
    users_checked: int = 0
    notices_sent: int = 0
    failures: int = 0


async def run_notice_cycle(ctx: ServiceContext, push: PushProvider) -> NoticeReport:
    checked = sent = failures = 0
    after: UUID | None = None
    while True:
        async with ctx.uow_factory() as uow:
            page = await uow.users.list_notifiable_page(after=after, limit=PAGE_SIZE)
        if not page:
            break
        after = page[-1].id
        for user in page:
            checked += 1
            try:
                if await notify_user(ctx, push, user):
                    sent += 1
            except Exception as exc:  # one broken user must not stop the cycle
                failures += 1
                ctx.error_reporter.capture(exc)
    log.info("notice_cycle", users_checked=checked, notices_sent=sent, failures=failures)
    return NoticeReport(users_checked=checked, notices_sent=sent, failures=failures)


async def notify_user(
    ctx: ServiceContext, push: PushProvider, user: UserRecord
) -> NoticeKind | None:
    """The notice sent to this user now, or None."""
    try:
        timezone = parse_timezone(user.timezone)
    except InvalidTimezone:
        return None
    now = ctx.clock.now()
    today = ctx.clock.today(timezone)
    async with ctx.uow_factory() as uow:
        pet = await uow.pets.get(user.id)
        if pet is None:
            return None
        consent = (await uow.consents.latest_by_type(user.id)).get(ConsentType.MEAL_DATA)
        if consent is None or not consent.accepted:
            return None  # meal reminders only make sense for people who log meals
        tokens = await uow.push_tokens.list_for_user(user.id)
        if not tokens:
            return None
        state = await settled_state(uow, user.id, pet, timezone, today)  # in memory, not saved
        episode_day = state.last_log_day or NEVER_LOGGED_EPISODE
        kind = decide_notice(
            mood=compute_mood(state, today, now),
            prefs=user.notifications,
            local_now=now.astimezone(timezone),
            sent_today=await uow.notices.count_on_day(user.id, today),
            sent_in_episode=await uow.notices.kinds_in_episode(user.id, episode_day),
        )
        if kind is None:
            return None
        recorded = await uow.notices.add_if_new(
            NoticeRecord(
                id=ctx.ids.new_id(),
                user_id=user.id,
                kind=kind,
                episode_day=episode_day,
                local_day=today,
                sent_at=now,
            )
        )
        if not recorded:
            return None
        await uow.commit()

    copy = pick_copy(kind, episode_day)
    stale: list[str] = []
    for token in tokens:
        try:
            outcome = await push.send(token.token, copy.title, copy.body)
        except PushUnavailableError:
            log.warning("push_unavailable", kind=kind.value)
            continue
        if outcome is PushOutcome.INVALID_TOKEN:
            stale.append(token.token)
    if stale:
        async with ctx.uow_factory() as uow:
            for token_value in stale:
                await uow.push_tokens.delete(user.id, token_value)
            await uow.commit()
    return kind
