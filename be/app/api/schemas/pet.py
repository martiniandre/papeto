"""Pet schemas."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt

from app.domain import Attribute, Mood, PetEvent
from app.services.views import PetView


class LevelProgressOut(BaseModel):
    points: int
    current_level_at: int
    next_level_at: int


class AttributesOut(BaseModel):
    strength: int
    speed: int
    skill: int
    endurance: int
    intelligence: int


class PetBase(BaseModel):
    name: str | None  # null until the user names the pet
    color: str
    lives: int
    max_lives: int
    streak_days: int
    points: int
    mood: Mood
    level: int
    level_progress: LevelProgressOut
    attributes: AttributesOut
    unspent_attribute_points: int

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
            "level": view.level,
            "level_progress": {
                "points": view.level_progress.points,
                "current_level_at": view.level_progress.current_level_at,
                "next_level_at": view.level_progress.next_level_at,
            },
            "attributes": view.attributes.as_dict(),
            "unspent_attribute_points": view.unspent_attribute_points,
        }


class PetResponse(PetBase):
    """GET /pet: the pet plus one-shot events."""

    events: list[PetEvent]
    # RF-98: true when the risk pattern is on and met. Show a kind message and the CVV 188 path.
    # Always false while the threshold is not decided (disabled).
    support_hint: bool

    @classmethod
    def from_view(cls, view: PetView) -> PetResponse:
        return cls.model_validate(
            {
                **cls.base_fields(view),
                "events": list(view.events),
                "support_hint": view.support_hint,
            }
        )


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


class AttributeAllocation(BaseModel):
    """POST /pet/attributes. Unknown attributes and non-positive amounts are a 422."""

    model_config = ConfigDict(extra="forbid")

    allocations: dict[Attribute, Annotated[StrictInt, Field(gt=0)]] = Field(min_length=1)
