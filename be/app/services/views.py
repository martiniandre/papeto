"""Plain results returned by use cases (the API turns them into response schemas)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.domain import Mood, PetEvent, Plan, ProductEvent
from app.ports.repositories import ConsentRecord, ConsentType, MealRecord, UserRecord


@dataclass(frozen=True, slots=True)
class PetView:
    name: str | None
    color: str
    lives: int
    max_lives: int
    streak_days: int
    points: int
    mood: Mood
    events: tuple[PetEvent, ...] = ()
    support_hint: bool = False  # RF-98: show the kind message and the CVV 188 path


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
    pet_tip: str | None = None  # Premium only ("Seus hábitos"); approved phrase, never AI text
    # RF-70 events decided inside the transaction, emitted after it commits.
    pending_events: tuple[tuple[ProductEvent, dict[str, str | int | bool]], ...] = ()


@dataclass(frozen=True, slots=True)
class ConsentResult:
    record: ConsentRecord
    # Follow-ups the app should offer (only when `meal_data` was revoked).
    suggested_actions: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MealPage:
    items: list[MealRecord] = field(default_factory=list)
    next_cursor: str | None = None
