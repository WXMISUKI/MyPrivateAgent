"""Document artifact persistence API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

try:
    from services.document_artifact_service import (
        DocumentArtifactNotFound,
        get_document_artifact_service,
    )
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.document_artifact_service import (
        DocumentArtifactNotFound,
        get_document_artifact_service,
    )


router = APIRouter(prefix="/api", tags=["document-artifacts"])


@router.post("/document-artifacts")
def persist_document_artifact(payload: dict[str, Any]):
    try:
        artifact = get_document_artifact_service().persist(payload)
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={
                "ok": False,
                "error": {
                    "code": "DOCUMENT_ARTIFACT_INVALID_INPUT",
                    "message": str(exc),
                },
            },
        )
    return {
        "ok": True,
        "artifact": artifact.metadata,
    }


@router.get("/document-artifacts")
def list_document_artifacts(limit: int = 50) -> dict[str, Any]:
    return {
        "ok": True,
        "artifacts": get_document_artifact_service().list(limit=limit),
    }


@router.get("/document-artifacts/{artifact_id}")
def get_document_artifact(artifact_id: str):
    try:
        artifact = get_document_artifact_service().get(artifact_id)
    except DocumentArtifactNotFound:
        return JSONResponse(
            status_code=404,
            content={
                "ok": False,
                "error": {
                    "code": "DOCUMENT_ARTIFACT_NOT_FOUND",
                    "message": f"Document artifact not found: {artifact_id}",
                    "artifact_id": artifact_id,
                },
            },
        )
    return {
        "ok": True,
        "artifact": artifact.metadata,
        "payload": artifact.payload,
    }
