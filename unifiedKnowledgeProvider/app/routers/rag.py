"""RAG retrieval endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from ..models import RagRetrieveRequest
from ..services.llamaindex_rag_service import retrieve
from ..services.source_catalog import RAG_SOURCES

router = APIRouter()


@router.get("/sources")
def sources() -> dict[str, object]:
    return {
        "ok": True,
        "sources": [source.model_dump() for source in RAG_SOURCES.values()],
    }


@router.post("/retrieve")
def retrieve_rag(request: RagRetrieveRequest) -> dict[str, object]:
    missing_sources = [
        source_id for source_id in request.knowledge_base_ids if source_id not in RAG_SOURCES
    ]
    if missing_sources:
        return {
            "ok": False,
            "error": {
                "code": "RAG_SOURCE_NOT_FOUND",
                "message": "One or more requested knowledge bases are not registered.",
                "details": {"missing_sources": missing_sources},
            },
        }

    result = retrieve(request)
    return {
        "ok": True,
        "capability_id": "knowledge.rag.retrieve",
        "provider": "unifiedKnowledgeProvider",
        "result": result.model_dump(),
    }

