"""Push token and notification scenarios against real Postgres."""

from __future__ import annotations

import pytest

from tests.notification_cases import PushTokenCases

pytestmark = pytest.mark.integration


class TestPushTokensPostgres(PushTokenCases):
    pass
