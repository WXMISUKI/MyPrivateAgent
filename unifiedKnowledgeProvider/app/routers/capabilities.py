"""Capability metadata endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from ..services.source_catalog import readiness_summary

router = APIRouter()


@router.get("/capabilities")
def capabilities() -> dict[str, object]:
    return {
        "ok": True,
        "provider": "unifiedKnowledgeProvider",
        "status": readiness_summary()["status"],
        "capabilities": [
            {
                "capability_id": "knowledge.rag.retrieve",
                "kind": "rag",
                "transport": "http",
                "endpoint": "/api/rag/retrieve",
                "sources_path": "/api/rag/sources",
            },
            {
                "capability_id": "knowledge.graph.query",
                "kind": "knowledge_graph",
                "transport": "http",
                "endpoint": "/api/graph/query",
                "schemas_path": "/api/graph/schemas",
            },
        ],
    }

