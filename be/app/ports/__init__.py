"""Ports: Protocols for every external service plus Clock and IdGenerator."""

from app.ports.analytics import AnalyticsProvider
from app.ports.auth import (
    AuthProvider,
    AuthProviderUnavailableError,
    GoogleIdentity,
    InvalidTokenError,
    SocialEmailNotVerifiedError,
    SocialTokenInvalidError,
    TokenKind,
)
from app.ports.clock import Clock
from app.ports.email import EmailProvider
from app.ports.errors import ErrorReporter
from app.ports.ids import IdGenerator
from app.ports.payment import PaymentProvider
from app.ports.push import PushOutcome, PushProvider, PushUnavailableError
from app.ports.storage import StorageProvider
from app.ports.vision import (
    FoodVisionProvider,
    MealType,
    NotFoodError,
    PhotoNotReadableError,
    PhotoTooLargeError,
    VisionResult,
    VisionTimeoutError,
    VisionUnavailableError,
)

__all__ = [
    "AnalyticsProvider",
    "AuthProvider",
    "AuthProviderUnavailableError",
    "Clock",
    "EmailProvider",
    "ErrorReporter",
    "FoodVisionProvider",
    "GoogleIdentity",
    "IdGenerator",
    "InvalidTokenError",
    "MealType",
    "NotFoodError",
    "PaymentProvider",
    "PhotoNotReadableError",
    "PhotoTooLargeError",
    "PushOutcome",
    "PushProvider",
    "PushUnavailableError",
    "SocialEmailNotVerifiedError",
    "SocialTokenInvalidError",
    "StorageProvider",
    "TokenKind",
    "VisionResult",
    "VisionTimeoutError",
    "VisionUnavailableError",
]
