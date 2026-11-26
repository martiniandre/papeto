"""PaymentProvider port (stub, Stripe first). TODO: checkout, portal and webhook verification."""

from __future__ import annotations

from typing import Protocol


class PaymentProvider(Protocol):
    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """True when the signature is valid. Verify before storing any payment_event."""
        ...
