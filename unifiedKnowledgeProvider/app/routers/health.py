"""Health endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from ..services.source_catalog import readiness_summary

router = APIRouter()


@router.get("/health")
def health() -> dict[str, object]:
    readiness = readiness_summary()
    return {
        "status": "ok" if readiness["status"] == "ready" else "degraded",
        "service": "unifiedKnowledgeProvider",
        "rag": {"status": readiness["status"]},
        "graph": {"status": readiness["status"]},
        "catalog": readiness,
    }

