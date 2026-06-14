"""External service provider management API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

try:
    from capability_runtime.provider_consumption_service import get_provider_consumption_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.capability_runtime.provider_consumption_service import get_provider_consumption_service


router = APIRouter(prefix="/api", tags=["service-providers"])


def _provider_not_found(provider_id: str) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "SERVICE_PROVIDER_NOT_FOUND",
                "message": f"Service provider not found: {provider_id}",
                "provider_id": provider_id,
            }
        },
    )


@router.get("/service-providers")
def list_service_providers() -> dict[str, Any]:
    return get_provider_consumption_service().list_providers()


@router.get("/service-providers/{provider_id}")
def get_service_provider(provider_id: str):
    try:
        return get_provider_consumption_service().get_provider(provider_id)
    except LookupError:
        return _provider_not_found(provider_id)


@router.get("/service-providers/{provider_id}/evidence-preview")
def preview_service_provider_evidence(provider_id: str):
    try:
        return get_provider_consumption_service().preview_evidence(provider_id)
    except LookupError:
        return _provider_not_found(provider_id)


@router.post("/service-providers/{provider_id}/capabilities/{capability_id}/invoke")
def invoke_service_provider_capability(provider_id: str, capability_id: str, payload: dict[str, Any]):
    try:
        result = get_provider_consumption_service().invoke_provider_capability(
            provider_id=provider_id,
            capability_id=capability_id,
            payload=payload,
        )
    except LookupError:
        return _provider_not_found(provider_id)
    if result.get("ok"):
        return result
    error_code = str(result.get("error", {}).get("code") or "")
    status_code = 400 if error_code == "SERVICE_PROVIDER_CAPABILITY_NOT_OWNED" else 503
    return JSONResponse(status_code=status_code, content=result)
