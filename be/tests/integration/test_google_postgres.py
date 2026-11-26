"""Google sign-in and adult confirmation against real Postgres."""

from __future__ import annotations

import pytest

from tests.google_cases import AdultConfirmationCases, GoogleSignInCases

pytestmark = pytest.mark.integration


class TestGoogleSignInPostgres(GoogleSignInCases):
    pass


class TestAdultConfirmationPostgres(AdultConfirmationCases):
    pass
