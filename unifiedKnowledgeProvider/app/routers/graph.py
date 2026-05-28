"""Knowledge graph endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from ..models import GraphQueryRequest
from ..services.neo4j_graphrag_service import query_graph
from ..services.source_catalog import GRAPH_SOURCES

router = APIRouter()


@router.get("/schemas")
def schemas() -> dict[str, object]:
    return {
        "ok": True,
        "schemas": [
            {
                "graph_id": graph.id,
                "status": graph.status,
                "ontology_version": graph.metadata.get("ontology_version"),
                "entity_types": ["order", "refund", "shipment"],
                "relation_types": ["has_refund", "shipped_by"],
            }
            for graph in GRAPH_SOURCES.values()
        ],
    }


@router.post("/query")
def query(request: GraphQueryRequest) -> dict[str, object]:
    graph_id = request.graph_id or next(iter(GRAPH_SOURCES))
    if graph_id not in GRAPH_SOURCES:
        return {
            "ok": False,
            "error": {
                "code": "GRAPH_SOURCE_NOT_FOUND",
                "message": "Requested graph is not registered.",
                "details": {"graph_id": graph_id},
            },
        }

    result = query_graph(request.model_copy(update={"graph_id": graph_id}))
    return {
        "ok": True,
        "capability_id": "knowledge.graph.query",
        "provider": "unifiedKnowledgeProvider",
        "result": result.model_dump(),
    }

