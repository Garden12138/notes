"""FastAPI entry point for the intelligent travel assistant."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config import get_settings
from .routes import system_router, trip_router


def create_app() -> FastAPI:
    """Create a configured application without starting external services."""
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="HelloAgents 智能旅行助手后端",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(system_router, prefix=settings.api_prefix)
    application.include_router(trip_router, prefix=settings.api_prefix)

    @application.get("/", tags=["system"])
    def root() -> dict[str, str]:
        return {
            "name": settings.app_name,
            "docs": "/docs",
            "health": f"{settings.api_prefix}/system/health",
            "trip_validation": f"{settings.api_prefix}/trip/validate",
        }

    return application


app = create_app()
