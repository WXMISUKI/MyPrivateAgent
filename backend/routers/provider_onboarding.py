"""Provider onboarding catalog API."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

try:
    from capability_runtime.provider_onboarding_catalog import get_provider_onboarding_catalog_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.capability_runtime.provider_onboarding_catalog import get_provider_onboarding_catalog_service


router = APIRouter(prefix="/api", tags=["provider-onboarding"])


def _not_found(onboarding_id: str) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "PROVIDER_ONBOARDING_NOT_FOUND",
                "message": f"Provider onboarding entry not found: {onboarding_id}",
                "onboarding_id": onboarding_id,
            }
        },
    )


@router.get("/provider-onboarding")
def list_provider_onboarding():
    return get_provider_onboarding_catalog_service().list_entries()


@router.get("/provider-onboarding/{onboarding_id}")
def get_provider_onboarding(onboarding_id: str):
    try:
        return get_provider_onboarding_catalog_service().get_entry(onboarding_id)
    except LookupError:
        return _not_found(onboarding_id)


@router.get("/provider-onboarding/{onboarding_id}/readiness")
def get_provider_onboarding_readiness(onboarding_id: str):
    try:
        return get_provider_onboarding_catalog_service().get_readiness(onboarding_id)
    except LookupError:
        return _not_found(onboarding_id)
