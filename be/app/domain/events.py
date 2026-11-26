"""Product event names for the funnel and retention metrics (RF-70).

Events carry only a random analytics id and coarse properties (enums, counts, booleans). Never a
name, an email, meal text or a photo. See docs/product-rules.md and docs/api.md.
"""

from __future__ import annotations

from enum import StrEnum


class ProductEvent(StrEnum):
    SIGNUP_COMPLETED = "signup_completed"
    CONSENTS_ACCEPTED = "consents_accepted"
    PET_NAMED = "pet_named"
    MEAL_LOGGED = "meal_logged"  # property `source`: photo | manual
    PET_FAINTED = "pet_fainted"
    PET_WOKE_UP = "pet_woke_up"
    LIFE_LOST = "life_lost"
    NOTIFICATION_SENT = "notification_sent"
    ACCOUNT_DELETION_REQUESTED = "account_deletion_requested"
    EXPORT_REQUESTED = "export_requested"
