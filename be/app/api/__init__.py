"""HTTP layer: routers and request/response schemas only (no business rules)."""

from fastapi import APIRouter

from app.api.routers import auth, health, me, meals, pet, push_tokens

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(auth.router)
v1_router.include_router(me.router)
v1_router.include_router(pet.router)
v1_router.include_router(meals.router)
v1_router.include_router(push_tokens.router)

health_router = health.router

__all__ = ["health_router", "v1_router"]
