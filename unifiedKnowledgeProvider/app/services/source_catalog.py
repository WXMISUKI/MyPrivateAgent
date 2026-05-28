"""Static source catalog for the first provider slice."""

from __future__ import annotations

from ..models import CatalogSource


RAG_SOURCES: dict[str, CatalogSource] = {
    "refund_policy_docs": CatalogSource(
        id="refund_policy_docs",
        type="rag",
        status="ready",
        owner="ecommerce",
        version="2026-05-28",
        description="Demo after-sales refund policy documents.",
        metadata={
            "framework_target": "llamaindex",
            "freshness": "static-demo",
            "embedding_model": "not-configured",
        },
    ),
    "logistics_faq": CatalogSource(
        id="logistics_faq",
        type="rag",
        status="ready",
        owner="ecommerce",
        version="2026-05-28",
        description="Demo logistics FAQ documents.",
        metadata={
            "framework_target": "llamaindex",
            "freshness": "static-demo",
            "embedding_model": "not-configured",
        },
    ),
}


GRAPH_SOURCES: dict[str, CatalogSource] = {
    "ecommerce_order_graph": CatalogSource(
        id="ecommerce_order_graph",
        type="graph",
        status="ready",
        owner="ecommerce",
        version="2026-05-28",
        description="Demo graph namespace for order, logistics, refund, and after-sales relations.",
        metadata={
            "framework_target": "neo4j-graphrag",
            "ontology_version": "demo-2026-05",
            "graph_store": "static-demo",
        },
    )
}


def list_catalog() -> dict[str, list[dict]]:
    return {
        "knowledge_bases": [source.model_dump() for source in RAG_SOURCES.values()],
        "graphs": [source.model_dump() for source in GRAPH_SOURCES.values()],
    }


def readiness_summary() -> dict[str, object]:
    sources = [*RAG_SOURCES.values(), *GRAPH_SOURCES.values()]
    degraded = [source.id for source in sources if source.status != "ready"]
    return {
        "status": "ready" if not degraded else "degraded",
        "total_sources": len(sources),
        "degraded_sources": degraded,
    }

