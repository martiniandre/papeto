"""ARQ worker settings. Run with `uv run arq app.worker.settings.WorkerSettings`.

Needs the same environment variables as the API (DATABASE_URL, REDIS_URL, JWT_SECRET, ...).
"""

from __future__ import annotations

import os
from typing import Any, ClassVar

from arq import cron
from arq.connections import RedisSettings

from app.config import Settings
from app.container import build_container, build_push
from app.worker.tasks import PUSH_KEY, SERVICE_CONTEXT_KEY, send_notices

SHUTDOWN_KEY = "shutdown"


async def on_startup(ctx: dict[str, Any]) -> None:
    settings = Settings()  # type: ignore[call-arg]  # jwt_secret comes from the env
    container = build_container(settings)
    ctx[SERVICE_CONTEXT_KEY] = container.ctx
    ctx[PUSH_KEY] = build_push(settings)
    ctx[SHUTDOWN_KEY] = container.shutdown


async def on_shutdown(ctx: dict[str, Any]) -> None:
    await ctx[SHUTDOWN_KEY]()


class WorkerSettings:
    functions: ClassVar[list[Any]] = [send_notices]
    cron_jobs: ClassVar[list[Any]] = [
        # Every 15 minutes; quiet hours and caps are decided per user in local time.
        cron(send_notices, minute={0, 15, 30, 45}, run_at_startup=False, unique=True),
    ]
    on_startup = on_startup
    on_shutdown = on_shutdown
    redis_settings = RedisSettings.from_dsn(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
