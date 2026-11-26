"""Liveness and readiness (mounted at the root, outside /v1)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.deps import ReadinessCheck, get_readiness

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str


class ReadyResponse(BaseModel):
    status: str
    checks: dict[str, str]


@router.get("/health")
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/health/ready", response_model=ReadyResponse)
async def ready(check: Annotated[ReadinessCheck, Depends(get_readiness)]) -> JSONResponse:
    results = await check()
    ok = all(results.values())
    body = ReadyResponse(
        status="ready" if ok else "unavailable",
        checks={name: "ok" if up else "down" for name, up in results.items()},
    )
    return JSONResponse(status_code=200 if ok else 503, content=body.model_dump())
