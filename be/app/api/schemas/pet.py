"""Pet schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain import Mood, PetEvent
from app.services.views import PetView


class PetBase(BaseModel):
    name: str | None  # null until the user names the pet
    color: str
    lives: int
    max_lives: int
    streak_days: int
    points: int
    mood: Mood

    @classmethod
    def base_fields(cls, view: PetView) -> dict[str, object]:
        return {
            "name": view.name,
            "color": view.color,
            "lives": view.lives,
            "max_lives": view.max_lives,
            "streak_days": view.streak_days,
            "points": view.points,
            "mood": view.mood,
        }


class PetResponse(PetBase):
    """GET /pet: the pet plus one-shot events."""

    events: list[PetEvent]

    @classmethod
    def from_view(cls, view: PetView) -> PetResponse:
        return cls.model_validate({**cls.base_fields(view), "events": list(view.events)})


class PetSummary(PetBase):
    """Pet inside POST /meals (events are returned next to it)."""

    @classmethod
    def from_view(cls, view: PetView) -> PetSummary:
        return cls.model_validate(cls.base_fields(view))


class PetPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=20)
    color: str | None = Field(default=None, min_length=1, max_length=20)


class PauseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    days: Literal[1, 3, 7]
