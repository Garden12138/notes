"""Bootstrap endpoints used before the planning workflow is implemented."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ...config import Settings, get_settings
from ...services import build_architecture_snapshot


router = APIRouter(prefix="/system", tags=["system"])


@router.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict[str, object]:
    """Report process health and credential presence without secret values."""
    integrations = settings.integration_status()
    return {
        "status": "ok",
        "application": settings.app_name,
        "version": settings.app_version,
        "integrations": integrations,
        "planning_ready": all(integrations.values()),
    }


@router.get("/architecture")
def architecture(
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    """Return the four-layer architecture consumed by the bootstrap UI."""
    return build_architecture_snapshot(settings.integration_status())

