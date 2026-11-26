"""ARQ task functions. Thin: they pull dependencies from the worker context and call services.

Tests call these functions directly with a hand-built context (no Redis needed).
"""

from __future__ import annotations

from typing import Any

from app.ports import PushProvider
from app.services.context import ServiceContext
from app.services.notices import run_notice_cycle
from app.services.retention import purge_deleted_accounts

SERVICE_CONTEXT_KEY = "service_ctx"
PUSH_KEY = "push"


def worker_context(service_ctx: ServiceContext, push: PushProvider) -> dict[str, Any]:
    return {SERVICE_CONTEXT_KEY: service_ctx, PUSH_KEY: push}


async def send_notices(ctx: dict[str, Any]) -> dict[str, int]:
    """Cron: send the pet notices that are due. Never changes lives."""
    report = await run_notice_cycle(ctx[SERVICE_CONTEXT_KEY], ctx[PUSH_KEY])
    return {
        "users_checked": report.users_checked,
        "notices_sent": report.notices_sent,
        "failures": report.failures,
    }


async def purge_accounts(ctx: dict[str, Any]) -> dict[str, int]:
    """Cron: erase accounts whose deletion has been pending for more than the grace period."""
    report = await purge_deleted_accounts(ctx[SERVICE_CONTEXT_KEY])
    return {"anonymized": report.anonymized, "removed": report.removed}
