"""Unified AI capability runtime API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

try:
    from capability_runtime.service import get_capability_runtime_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.capability_runtime.service import get_capability_runtime_service


router = APIRouter(prefix="/api", tags=["capabilities"])


def _not_found(capability_id: str) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "CAPABILITY_NOT_FOUND",
                "message": f"Capability not found: {capability_id}",
                "capability_id": capability_id,
            }
        },
    )


@router.get("/capabilities")
def list_capabilities() -> dict[str, Any]:
    return get_capability_runtime_service().list_capabilities()


@router.get("/capabilities/{capability_id}")
def get_capability(capability_id: str):
    try:
        return get_capability_runtime_service().get_capability(capability_id)
    except LookupError:
        return _not_found(capability_id)


@router.get("/capabilities/{capability_id}/health")
def get_capability_health(capability_id: str):
    try:
        return get_capability_runtime_service().get_capability_health(capability_id)
    except LookupError:
        return _not_found(capability_id)


@router.post("/capabilities/{capability_id}/invoke")
def invoke_capability(capability_id: str, payload: dict[str, Any]):
    try:
        result = get_capability_runtime_service().invoke(capability_id, payload)
    except LookupError:
        return _not_found(capability_id)
    if result.get("ok"):
        return result
    return JSONResponse(status_code=503, content=result)
