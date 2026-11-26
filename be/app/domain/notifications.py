"""Notice rules (RF-40 to RF-42): when the pet may nudge the user. Pure; never changes lives.

The worker only *reads* the mood computed by `app.domain.mood` and asks `decide_notice` whether a
push should go out. Rules, in order:

1. Only `tired` and `sleepy` moods notify. `happy`, `paused` and `fainted` never do.
2. The user can switch each notice off (`meal_reminder` for tired, `sleepy_notice` for sleepy).
3. Nothing is sent during quiet hours (local time; the window may cross midnight).
4. At most one `tired` and one `sleepy` notice per episode. An episode is the stretch since the
   last log (`last_log_day`), so a new log starts a fresh episode.
5. At most `MAX_NOTICES_PER_DAY` notices per local day.

Copy is a fixed list written here (pt-BR). It never mentions body, weight, calories or right/wrong
food, never guilts, and says "registrar" instead of "comer"/"alimentar".
"""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from datetime import date, datetime, time
from enum import StrEnum

from app.domain.mood import Mood

MAX_NOTICES_PER_DAY = 2


class NoticeKind(StrEnum):
    TIRED = "tired"
    SLEEPY = "sleepy"


@dataclass(frozen=True, slots=True)
class NotificationPrefs:
    meal_reminder: bool = True
    sleepy_notice: bool = True
    weekly_summary: bool = True
    quiet_hours_start: time = time(22, 0)
    quiet_hours_end: time = time(8, 0)

    def __post_init__(self) -> None:
        if self.quiet_hours_start.tzinfo is not None or self.quiet_hours_end.tzinfo is not None:
            raise ValueError("quiet hours are local wall-clock times and must be naive")


DEFAULT_PREFS = NotificationPrefs()

_MOOD_TO_KIND = {Mood.TIRED: NoticeKind.TIRED, Mood.SLEEPY: NoticeKind.SLEEPY}


def in_quiet_hours(local_time: time, start: time, end: time) -> bool:
    """True when `local_time` is inside `[start, end)`. `start == end` means no quiet hours."""
    if start == end:
        return False
    if start < end:
        return start <= local_time < end
    return local_time >= start or local_time < end  # crosses midnight, e.g. 22:00 to 08:00


def _enabled(kind: NoticeKind, prefs: NotificationPrefs) -> bool:
    return prefs.meal_reminder if kind is NoticeKind.TIRED else prefs.sleepy_notice


def decide_notice(
    *,
    mood: Mood,
    prefs: NotificationPrefs,
    local_now: datetime,
    sent_today: int,
    sent_in_episode: Collection[NoticeKind],
) -> NoticeKind | None:
    """The notice to send now, or None. `local_now` must be the user's local wall-clock time."""
    kind = _MOOD_TO_KIND.get(mood)
    if kind is None:
        return None
    if not _enabled(kind, prefs):
        return None
    if in_quiet_hours(local_now.time(), prefs.quiet_hours_start, prefs.quiet_hours_end):
        return None
    if sent_today >= MAX_NOTICES_PER_DAY:
        return None
    if kind in sent_in_episode:
        return None
    return kind


@dataclass(frozen=True, slots=True)
class NoticeCopy:
    title: str
    body: str


# Fixed approved phrases. Add variants here; never build copy from user data or free text.
NOTICE_COPY: dict[NoticeKind, tuple[NoticeCopy, ...]] = {
    NoticeKind.TIRED: (
        NoticeCopy(
            "Seu pet está esperando", "Que tal registrar uma refeição hoje? Ele vai gostar."
        ),
        NoticeCopy(
            "Um momento para você", "Quando puder, registre sua próxima refeição com uma foto."
        ),
        NoticeCopy(
            "Oi, tudo bem?", "Seu pet está com soninho e adoraria ver o seu registro de hoje."
        ),
    ),
    NoticeKind.SLEEPY: (
        NoticeCopy("Seu pet está sonolento", "Um registro hoje faz ele acordar mais animado."),
        NoticeCopy(
            "Estamos com saudade", "Registre uma refeição quando puder. Sem pressa, ele espera."
        ),
        NoticeCopy("Que tal voltar?", "Um registro rapidinho e seu pet já fica mais feliz."),
    ),
}


def pick_copy(kind: NoticeKind, episode_day: date) -> NoticeCopy:
    """Deterministic choice (no randomness), so the same episode always reads the same."""
    options = NOTICE_COPY[kind]
    return options[episode_day.toordinal() % len(options)]
