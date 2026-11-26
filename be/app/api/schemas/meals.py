"""Meal schemas. No calories, macros, grams, scores or health labels exist in any of them."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.pet import PetSummary
from app.domain import PetEvent
from app.ports import MealType
from app.ports.repositories import MealRecord, MealSource
from app.services.views import LogMealResult, MealPage


class MealOut(BaseModel):
    id: UUID
    logged_at: datetime
    local_day: date
    meal_type: MealType
    description: str
    items: list[str]
    food_groups: list[str]
    item_count: int
    colors: list[str]
    confidence: float
    plate_share: dict[str, float]
    new_foods: list[str]
    source: MealSource

    @classmethod
    def from_record(cls, meal: MealRecord) -> MealOut:
        return cls(
            id=meal.id,
            logged_at=meal.logged_at,
            local_day=meal.local_day,
            meal_type=MealType(meal.meal_type),
            description=meal.description,
            items=meal.items,
            food_groups=meal.food_groups,
            item_count=meal.item_count,
            colors=meal.colors,
            confidence=meal.confidence,
            plate_share=meal.plate_share,
            new_foods=meal.new_foods,
            source=meal.source,
        )


class LogMealResponse(BaseModel):
    meal: MealOut
    pet: PetSummary
    events: list[PetEvent]

    @classmethod
    def from_result(cls, result: LogMealResult) -> LogMealResponse:
        return cls(
            meal=MealOut.from_record(result.meal),
            pet=PetSummary.from_view(result.pet),
            events=list(result.events),
        )


class MealListResponse(BaseModel):
    items: list[MealOut]
    next_cursor: str | None

    @classmethod
    def from_page(cls, page: MealPage) -> MealListResponse:
        return cls(items=[MealOut.from_record(m) for m in page.items], next_cursor=page.next_cursor)


class MealPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[str] | None = Field(default=None, max_length=30)
    meal_type: MealType | None = None


class ManualMealRequest(BaseModel):
    """RF-95: a meal registered by choosing items by hand (no photo, no AI)."""

    model_config = ConfigDict(extra="forbid")

    items: list[str] = Field(min_length=1, max_length=30)
    meal_type: MealType
