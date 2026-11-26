"""FastAPI app factory.

`uvicorn app.main:app` works through the lazy module attribute below, so importing this module
never needs environment variables (tests build apps with `create_app`).
"""

from __future__ import annotations

import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4

import structlog
from fastapi import FastAPI, Request, Response
from starlette.formparsers import MultiPartParser

from app.api import health_router, v1_router
from app.api.errors import install_error_handlers
from app.config import Settings
from app.container import Container, build_container
from app.logging import configure_logging

log = structlog.get_logger()


def create_app(settings: Settings | None = None, container: Container | None = None) -> FastAPI:
    resolved = settings or Settings()  # type: ignore[call-arg]  # jwt_secret comes from the env
    configure_logging(resolved.log_level)
    built = container or build_container(resolved)

    # Keep uploaded photos in memory: Starlette would otherwise spool uploads above 1 MiB to a
    # temporary file on disk, and photos are never written to disk.
    MultiPartParser.spool_max_size = resolved.max_upload_bytes + 1024 * 1024

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        await built.shutdown()

    app = FastAPI(title="Papeto API", version="1.0.0", lifespan=lifespan)
    app.state.ctx = built.ctx
    app.state.readiness = built.readiness
    app.state.max_upload_bytes = resolved.max_upload_bytes
    install_error_handlers(app)
    app.include_router(health_router)
    app.include_router(v1_router)

    @app.middleware("http")
    async def access_log(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = str(uuid4())
        started = time.perf_counter()
        response = await call_next(request)
        route = request.scope.get("route")
        log.info(
            "request",
            request_id=request_id,
            method=request.method,
            route=getattr(route, "path", "unmatched"),  # template only: no ids, no query string
            status=response.status_code,
            duration_ms=round((time.perf_counter() - started) * 1000, 1),
        )
        response.headers["X-Request-ID"] = request_id
        return response

    return app


def __getattr__(name: str) -> Any:
    if name == "app":
        return create_app()
    raise AttributeError(name)
