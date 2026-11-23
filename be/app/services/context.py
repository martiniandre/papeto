"""ServiceContext: everything a use case needs, injected by the container."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.domain import DEFAULT_RULES, PetRulesConfig
from app.ports import (
    AnalyticsProvider,
    AuthProvider,
    Clock,
    ErrorReporter,
    FoodVisionProvider,
    IdGenerator,
)
from app.ports.repositories import UnitOfWork


@dataclass(frozen=True)
class ServiceContext:
    uow_factory: Callable[[], UnitOfWork]
    clock: Clock
    ids: IdGenerator
    vision: FoodVisionProvider
    auth: AuthProvider
    analytics: AnalyticsProvider
    error_reporter: ErrorReporter
    rules: PetRulesConfig = DEFAULT_RULES
    deletion_grace_days: int = 30
    default_timezone: str = "America/Sao_Paulo"
