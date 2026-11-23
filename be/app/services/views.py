"""Plain results returned by use cases (the API turns them into response schemas)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.domain import Mood, PetEvent, Plan
from app.ports.repositories import ConsentRecord, ConsentType, MealRecord, UserRecord


@dataclass(frozen=True, slots=True)
class PetView:
    name: str
    color: str
    lives: int
    max_lives: int
    streak_days: int
    points: int
    mood: Mood
    events: tuple[PetEvent, ...] = ()


@dataclass(frozen=True, slots=True)
class TokenPair:
    access_token: str
    refresh_token: str
    expires_in: int


@dataclass(frozen=True, slots=True)
class MeView:
    user: UserRecord
    plan: Plan
    consents: dict[ConsentType, ConsentRecord]
    deletion_scheduled_for: datetime | None


@dataclass(frozen=True, slots=True)
class LogMealResult:
    meal: MealRecord
    pet: PetView
    events: tuple[PetEvent, ...]


@dataclass(frozen=True, slots=True)
class MealPage:
    items: list[MealRecord] = field(default_factory=list)
    next_cursor: str | None = None
