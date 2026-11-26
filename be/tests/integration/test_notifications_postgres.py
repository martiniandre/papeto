"""Push token, preference and notice scenarios against real Postgres."""

from __future__ import annotations

import pytest

from tests.notice_cases import NoticeCases
from tests.notification_cases import PreferenceCases, PushTokenCases
from tests.retention_cases import RetentionCases

pytestmark = pytest.mark.integration


class TestPushTokensPostgres(PushTokenCases):
    pass


class TestPreferencesPostgres(PreferenceCases):
    pass


class TestNoticesPostgres(NoticeCases):
    pass


class TestRetentionPostgres(RetentionCases):
    pass
