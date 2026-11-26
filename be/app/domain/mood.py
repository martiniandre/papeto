"""Pet mood, computed on read and never stored.

Order (first match wins): paused > fainted > happy > sleepy > tired. Pass a pet that was already
settled for `today_local`, otherwise missed days are not reflected in the lives.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from app.domain.pet import PetState


class Mood(StrEnum):
    PAUSED = "paused"
    FAINTED = "fainted"
    HAPPY = "happy"
    SLEEPY = "sleepy"
    TIRED = "tired"


def is_paused(pet: PetState, now: datetime) -> bool:
    """True while `rest_until` is in the future."""
    if now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    return pet.rest_until is not None and pet.rest_until > now


def compute_mood(pet: PetState, today_local: date, now: datetime) -> Mood:
    if is_paused(pet, now):
        return Mood.PAUSED
    if pet.lives == 0:
        return Mood.FAINTED
    if pet.last_log_day == today_local:
        return Mood.HAPPY
    if pet.lives == 1:
        return Mood.SLEEPY
    return Mood.TIRED
