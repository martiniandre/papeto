"""Consent, profile and export schemas."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain import Plan
from app.ports.repositories import ConsentRecord, ConsentType, UserExport
from app.services.views import MeView


class ConsentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: ConsentType
    version: str = Field(min_length=1, max_length=32)
    accepted: bool


class ConsentOut(BaseModel):
    type: ConsentType
    version: str
    accepted: bool
    recorded_at: datetime

    @classmethod
    def from_record(cls, record: ConsentRecord) -> ConsentOut:
        return cls(
            type=record.type,
            version=record.version,
            accepted=record.accepted,
            recorded_at=record.created_at,
        )


class MeResponse(BaseModel):
    id: UUID
    email: EmailStr
    name: str
    timezone: str
    plan: Plan
    analytics_opt_out: bool
    consents: list[ConsentOut]
    deletion_scheduled_for: datetime | None

    @classmethod
    def from_view(cls, view: MeView) -> MeResponse:
        return cls(
            id=view.user.id,
            email=view.user.email,
            name=view.user.name,
            timezone=view.user.timezone,
            plan=view.plan,
            analytics_opt_out=view.user.analytics_opt_out,
            consents=[ConsentOut.from_record(c) for c in view.consents.values()],
            deletion_scheduled_for=view.deletion_scheduled_for,
        )


class MePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timezone: str | None = Field(default=None, max_length=64)
    analytics_opt_out: bool | None = None


class ExportPet(BaseModel):
    name: str | None
    color: str
    lives: int
    streak_days: int
    last_log_day: date | None
    rest_until: datetime | None


class ExportPause(BaseModel):
    started_at: datetime
    ends_at: datetime


class ExportMeal(BaseModel):
    id: UUID
    logged_at: datetime
    local_day: date
    meal_type: str
    description: str
    items: list[str]
    food_groups: list[str]
    colors: list[str]
    deleted_at: datetime | None


class ExportPoints(BaseModel):
    reason: str
    amount: int
    local_day: date
    created_at: datetime


class ExportSubscription(BaseModel):
    provider: str
    status: str
    current_period_end: datetime | None


class ExportUser(BaseModel):
    id: UUID
    email: EmailStr
    name: str
    timezone: str
    analytics_opt_out: bool
    created_at: datetime
    adult_confirmed_at: datetime
    deletion_requested_at: datetime | None


class ExportResponse(BaseModel):
    user: ExportUser
    consents: list[ConsentOut]
    pet: ExportPet | None
    pauses: list[ExportPause]
    meals: list[ExportMeal]
    points: list[ExportPoints]
    subscription: ExportSubscription | None

    @classmethod
    def from_export(cls, data: UserExport) -> ExportResponse:
        user = data.user
        pet = data.pet
        sub = data.subscription
        return cls(
            user=ExportUser(
                id=user.id,
                email=user.email,
                name=user.name,
                timezone=user.timezone,
                analytics_opt_out=user.analytics_opt_out,
                created_at=user.created_at,
                adult_confirmed_at=user.adult_confirmed_at,
                deletion_requested_at=user.deletion_requested_at,
            ),
            consents=[ConsentOut.from_record(c) for c in data.consents],
            pet=ExportPet(
                name=pet.name,
                color=pet.color,
                lives=pet.state.lives,
                streak_days=pet.state.streak_days,
                last_log_day=pet.state.last_log_day,
                rest_until=pet.state.rest_until,
            )
            if pet
            else None,
            pauses=[ExportPause(started_at=p.started_at, ends_at=p.ends_at) for p in data.pauses],
            meals=[
                ExportMeal(
                    id=m.id,
                    logged_at=m.logged_at,
                    local_day=m.local_day,
                    meal_type=m.meal_type,
                    description=m.description,
                    items=m.items,
                    food_groups=m.food_groups,
                    colors=m.colors,
                    deleted_at=m.deleted_at,
                )
                for m in data.meals
            ],
            points=[
                ExportPoints(
                    reason=e.reason.value,
                    amount=e.amount,
                    local_day=e.local_day,
                    created_at=e.created_at,
                )
                for e in data.points
            ],
            subscription=ExportSubscription(
                provider=sub.provider,
                status=sub.status,
                current_period_end=sub.current_period_end,
            )
            if sub
            else None,
        )
