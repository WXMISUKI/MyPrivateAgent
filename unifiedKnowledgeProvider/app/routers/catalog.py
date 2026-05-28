"""Provider source catalog endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from ..services.source_catalog import list_catalog, readiness_summary

router = APIRouter()


@router.get("/catalog")
def catalog() -> dict[str, object]:
    return {
        "ok": True,
        "provider": "unifiedKnowledgeProvider",
        "status": readiness_summary()["status"],
        "catalog": list_catalog(),
    }

