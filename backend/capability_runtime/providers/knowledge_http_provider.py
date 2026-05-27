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
        try:
            data = client.get_json("/health")
        except CapabilityProviderError as exc:
            return {
                "status": "unreachable",
                "reason": exc.message,
                "error": exc.to_payload(),
            }
        status = str(data.get("status") or "unknown")
        if status == "ok":
            status = "ready"
        return {
            "status": status,
            "reason": str(data.get("message") or data.get("reason") or ""),
            "raw": data,
        }

    return check


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
