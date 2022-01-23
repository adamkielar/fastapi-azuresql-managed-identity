from fastapi import APIRouter

from app.api.api_v1.endpoints import health


api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
