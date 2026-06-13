"""HTTP provider definitions for an external Knowledge Provider service."""

from __future__ import annotations

from typing import Any

from ..clients.http_client import CapabilityProviderError, HttpCapabilityClient
from ..contracts import CapabilityDefinition


EXTERNAL_PROVIDER_ID = "unifiedKnowledgeProvider"


def build_http_knowledge_capabilities(
    *,
    base_url: str,
    timeout_seconds: float = 5.0,
    client: HttpCapabilityClient | None = None,
) -> list[CapabilityDefinition]:
    http_client = client or HttpCapabilityClient(base_url=base_url, timeout_seconds=timeout_seconds)
    return [
        CapabilityDefinition(
            capability_id="knowledge.rag.retrieve",
            kind="rag",
            transport="http",
            provider=EXTERNAL_PROVIDER_ID,
            title="Knowledge RAG Retrieve",
            description="Retrieve citation-backed document context through an external Knowledge Provider.",
            endpoint="/api/capabilities/knowledge.rag.retrieve/invoke",
            input_schema={
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {"type": "string"},
                    "knowledge_base_ids": {"type": "array", "items": {"type": "string"}},
                    "top_k": {"type": "integer", "minimum": 1},
                    "filters": {"type": "object"},
                },
            },
            output_schema={
                "type": "object",
                "required": ["answer_context", "documents"],
                "properties": {
                    "answer_context": {"type": "string"},
                    "documents": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["source_id", "document_id", "title", "snippet", "score", "citation"],
                            "properties": {
                                "source_id": {"type": "string"},
                                "document_id": {"type": "string"},
                                "title": {"type": "string"},
                                "snippet": {"type": "string"},
                                "score": {"type": "number"},
                                "citation": {"type": "string"},
                            },
                        },
                    },
                },
            },
            metadata=_metadata(base_url, "/health", "/api/rag/retrieve", sources_path="/api/rag/sources"),
            invoker=_invoke(http_client, "/api/rag/retrieve", "knowledge.rag.retrieve"),
            health_checker=_provider_health(http_client),
            heartbeat_checker=_provider_health(http_client),
        ),
        CapabilityDefinition(
            capability_id="knowledge.graph.query",
            kind="knowledge_graph",
            transport="http",
            provider=EXTERNAL_PROVIDER_ID,
            title="Knowledge Graph Query",
            description="Query entity, relation, and path evidence through an external Knowledge Provider.",
            endpoint="/api/capabilities/knowledge.graph.query/invoke",
            input_schema={
                "type": "object",
                "properties": {
                    "graph_id": {"type": "string"},
                    "query": {"type": "string"},
                    "entity_ids": {"type": "array", "items": {"type": "string"}},
                    "relation_types": {"type": "array", "items": {"type": "string"}},
                    "filters": {"type": "object"},
                },
            },
            output_schema={
                "type": "object",
                "required": ["graph_id", "entities", "relations", "paths", "evidence"],
                "properties": {
                    "graph_id": {"type": "string"},
                    "entities": {"type": "array"},
                    "relations": {"type": "array"},
                    "paths": {"type": "array"},
                    "evidence": {"type": "array"},
                },
            },
            metadata=_metadata(base_url, "/health", "/api/graph/query", schemas_path="/api/graph/schemas"),
            invoker=_invoke(http_client, "/api/graph/query", "knowledge.graph.query"),
            health_checker=_provider_health(http_client),
            heartbeat_checker=_provider_health(http_client),
        ),
    ]


def _metadata(
    base_url: str,
    health_path: str,
    invoke_path: str,
    *,
    sources_path: str | None = None,
    schemas_path: str | None = None,
) -> dict[str, Any]:
    metadata = {
        "provider_base_url": base_url.rstrip("/"),
        "provider_health_path": health_path,
        "provider_invoke_path": invoke_path,
        "provider_heartbeat_path": health_path,
        "external_provider": EXTERNAL_PROVIDER_ID,
    }
    if sources_path:
        metadata["provider_sources_path"] = sources_path
    if schemas_path:
        metadata["provider_schemas_path"] = schemas_path
    return metadata


def _provider_health(client: HttpCapabilityClient):
    def check() -> dict[str, Any]:
        provider_configured = bool(str(getattr(client, "base_url", "") or "").strip())
        try:
            health = client.get_json("/health")
        except CapabilityProviderError as exc:
            error_payload = exc.to_payload()
            return {
                "status": "unreachable",
                "reason": exc.message,
                "error": error_payload,
                "governance_readiness": _build_governance_readiness(
                    provider_status="unreachable",
                    provider_configured=provider_configured,
                    reason=exc.message,
                    error=error_payload,
                ),
            }
        status = str(health.get("status") or "unknown")
        if status == "ok":
            status = "ready"
        reason = str(health.get("message") or health.get("reason") or "")
        catalog_summary: dict[str, Any] | None = None
        source_catalog: dict[str, Any] | None = None
        try:
            catalog = client.get_json("/api/catalog")
            source_catalog = catalog.get("catalog") if isinstance(catalog.get("catalog"), dict) else None
            if source_catalog is not None:
                knowledge_bases = source_catalog.get("knowledge_bases") or []
                graphs = source_catalog.get("graphs") or []
                degraded_sources = [
                    source.get("id")
                    for source in [*knowledge_bases, *graphs]
                    if isinstance(source, dict) and str(source.get("status") or "").lower() != "ready"
                ]
                catalog_summary = {
                    "status": str(catalog.get("status") or "unknown"),
                    "knowledge_base_count": len(knowledge_bases),
                    "graph_count": len(graphs),
                    "source_count": len(knowledge_bases) + len(graphs),
                    "degraded_sources": degraded_sources,
                }
                if degraded_sources or catalog_summary["status"] not in {"ready", "ok"}:
                    status = "degraded" if status == "ready" else status
                    if not reason:
                        reason = "Provider source catalog reports degraded sources."
        except CapabilityProviderError as exc:
            catalog_summary = {
                "status": "unreachable",
                "error": exc.to_payload(),
            }
            if status == "ready":
                status = "degraded"
            if not reason:
                reason = "Provider source catalog is unavailable."
        return {
            "status": status,
            "reason": reason,
            "raw": health,
            "catalog": source_catalog,
            "catalog_summary": catalog_summary,
            "governance_readiness": _build_governance_readiness(
                provider_status=status,
                provider_configured=provider_configured,
                reason=reason,
                catalog_summary=catalog_summary,
            ),
        }

    return check


def _build_governance_readiness(
    *,
    provider_status: str,
    provider_configured: bool,
    reason: str = "",
    catalog_summary: dict[str, Any] | None = None,
    error: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_status = str(provider_status or "unknown").strip() or "unknown"
    catalog = dict(catalog_summary or {})
    catalog_status = str(catalog.get("status") or "unknown").strip() or "unknown"
    source_count = int(catalog.get("source_count") or 0)
    degraded_sources = [
        str(source_id or "").strip()
        for source_id in (catalog.get("degraded_sources") or [])
        if str(source_id or "").strip()
    ]
    if normalized_status == "unreachable":
        overall_status = "unreachable"
        rag_status = "unreachable"
    elif normalized_status == "ready" and catalog_status in {"ready", "ok"} and source_count > 0 and not degraded_sources:
        overall_status = "ready"
        rag_status = "ready"
    elif normalized_status == "ready" and catalog_status in {"ready", "ok"} and source_count == 0:
        overall_status = "degraded"
        rag_status = "degraded"
        reason = reason or "Provider source catalog has no ready sources."
    elif normalized_status in {"ready", "degraded"}:
        overall_status = "degraded"
        rag_status = "ready" if source_count > 0 and catalog_status in {"ready", "ok", "degraded"} else "degraded"
    else:
        overall_status = normalized_status
        rag_status = normalized_status

    readiness = {
        "contract_version": "knowledge-provider-governance-readiness-v1",
        "provider_id": EXTERNAL_PROVIDER_ID,
        "provider_configured": provider_configured,
        "overall_status": overall_status,
        "reason": str(reason or "").strip(),
        "rag_retrieve": {
            "status": rag_status,
            "capability_id": "knowledge.rag.retrieve",
            "usable_for_explicit_calls": rag_status == "ready",
        },
        "source_catalog": {
            "status": catalog_status,
            "source_count": source_count,
            "knowledge_base_count": int(catalog.get("knowledge_base_count") or 0),
            "graph_count": int(catalog.get("graph_count") or 0),
            "degraded_sources": degraded_sources,
        },
        "graph_query": {
            "status": "gated",
            "capability_id": "knowledge.graph.query",
            "reason": "GraphRAG execution remains separately gated.",
        },
        "default_chat_grounding": {
            "status": "gated",
            "reason": "Default /api/chat retrieval injection remains disabled.",
        },
        "boundaries": {
            "source_binding_automation": "disabled",
            "graphrag_execution": "not_promoted",
            "default_chat_retrieval_injection": "disabled",
            "answer_policy_change": "not_changed",
        },
    }
    if error:
        readiness["error"] = dict(error)
    return readiness


def _invoke(client: HttpCapabilityClient, path: str, capability_id: str):
    def invoke(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            data = client.post_json(path, payload)
        except CapabilityProviderError as exc:
            return {
                "ok": False,
                "error": exc.to_payload(),
            }
        if data.get("ok"):
            return {
                "ok": True,
                "capability_id": str(data.get("capability_id") or capability_id),
                "provider": str(data.get("provider") or EXTERNAL_PROVIDER_ID),
                "result": data.get("result") or {},
            }
        return {
            "ok": False,
            "error": data.get("error") or {
                "code": "KNOWLEDGE_PROVIDER_INVOCATION_FAILED",
                "message": "Knowledge Provider invocation failed.",
            },
        }

    return invoke
