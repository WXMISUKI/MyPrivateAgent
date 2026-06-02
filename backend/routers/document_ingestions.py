"""Document ingestion workflow API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

try:
    from services.document_ingestion_service import (
        DocumentIngestionError,
        DocumentIngestionNotFound,
        get_document_ingestion_service,
    )
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.document_ingestion_service import (
        DocumentIngestionError,
        DocumentIngestionNotFound,
        get_document_ingestion_service,
    )


router = APIRouter(prefix="/api", tags=["document-ingestions"])


@router.post("/document-ingestions")
def submit_document_ingestion(payload: dict[str, Any]):
    try:
        record = get_document_ingestion_service().submit(payload)
    except DocumentIngestionError as exc:
        return _error_response(exc)
    status_code = 503 if record.metadata.get("status") == "failed" else 200
    return JSONResponse(
        status_code=status_code,
        content={
            "ok": record.metadata.get("status") != "failed",
            "ingestion": record.metadata,
            **({"error": record.metadata.get("error") or {}} if record.metadata.get("status") == "failed" else {}),
        },
    )


@router.get("/document-ingestions")
def list_document_ingestions(limit: int = 50) -> dict[str, Any]:
    return {
        "ok": True,
        "ingestions": get_document_ingestion_service().list(limit=limit),
    }


@router.get("/document-ingestions/{ingest_id}")
def get_document_ingestion(ingest_id: str):
    try:
        record = get_document_ingestion_service().get(ingest_id)
    except DocumentIngestionNotFound as exc:
        return _error_response(exc)
    return {
        "ok": True,
        "ingestion": record.metadata,
    }


@router.get("/document-ingestions/{ingest_id}/result")
def get_document_ingestion_result(ingest_id: str):
    try:
        result = get_document_ingestion_service().get_result(ingest_id)
    except DocumentIngestionError as exc:
        return _error_response(exc)
    return {
        "ok": True,
        **result,
    }


def _error_response(exc: DocumentIngestionError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "ok": False,
            "error": exc.to_payload(),
        },
    )
