"""Use-case errors. Each carries a stable `code`; `app.api.errors` maps codes to HTTP statuses."""

from __future__ import annotations


class ServiceError(Exception):
    code = "INTERNAL_ERROR"
    message = "Something went wrong."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or type(self).message
        super().__init__(self.message)


class InvalidCredentials(ServiceError):
    code = "INVALID_CREDENTIALS"
    message = "Email or password is incorrect."


class InvalidToken(ServiceError):
    code = "INVALID_TOKEN"
    message = "The token is invalid or expired."


class EmailAlreadyRegistered(ServiceError):
    code = "EMAIL_ALREADY_REGISTERED"
    message = "This email is already registered."


class AdultConfirmationRequired(ServiceError):
    code = "ADULT_CONFIRMATION_REQUIRED"
    message = "You must confirm you are 18 or older."


class InvalidTimezone(ServiceError):
    code = "INVALID_TIMEZONE"
    message = "Unknown IANA timezone."


class ValidationFailed(ServiceError):
    code = "VALIDATION_ERROR"
    message = "The request is not valid."


class MealConsentRequired(ServiceError):
    code = "MEAL_CONSENT_REQUIRED"
    message = "An active meal_data consent is required."


class DailyLimitReached(ServiceError):
    code = "DAILY_LIMIT_REACHED"
    message = "Daily photo limit reached. You can log again tomorrow."


class PhotoNotReadable(ServiceError):
    code = "PHOTO_NOT_READABLE"
    message = "The photo could not be read. Try again."


class NotFood(ServiceError):
    code = "NOT_FOOD"
    message = "No food was found in the photo."


class VisionUnavailable(ServiceError):
    code = "VISION_UNAVAILABLE"
    message = "Photo analysis is unavailable right now. Try again later."


class PremiumRequired(ServiceError):
    code = "PREMIUM_REQUIRED"
    message = "This feature needs Premium."


class MealNotFound(ServiceError):
    code = "MEAL_NOT_FOUND"
    message = "Meal not found."


class PetAlreadyPaused(ServiceError):
    code = "PET_ALREADY_PAUSED"
    message = "The pet is already paused."


class PetNotPaused(ServiceError):
    code = "PET_NOT_PAUSED"
    message = "The pet is not paused."


class PetNotFound(ServiceError):
    code = "PET_NOT_FOUND"
    message = "Pet not found."


class InvalidResetToken(ServiceError):
    code = "INVALID_RESET_TOKEN"
    message = "The password reset link is invalid or expired."


class InvalidCursor(ServiceError):
    code = "INVALID_CURSOR"
    message = "The pagination cursor is not valid."


ALL_ERRORS: tuple[type[ServiceError], ...] = tuple(ServiceError.__subclasses__())
