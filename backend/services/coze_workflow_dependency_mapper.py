"""Shared dependency mapping helpers for Coze workflow migration assets."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict, List

try:
    from capability_runtime.provider_onboarding_catalog import get_provider_onboarding_catalog_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.capability_runtime.provider_onboarding_catalog import get_provider_onboarding_catalog_service


SUPPORTED_RUNTIME_CAPABILITIES = {
    "document.file_type.detect",
    "http.request",
    "spreadsheet.table.extract",
    "llm.structured_json.generate",
    "json_schema.validate",
}

PROVIDER_BACKED_CAPABILITIES = {
    "document.ocr.extract": {
        "provider_id": "paddleOCRProvider",
        "onboarding_id": "document-ocr-provider",
        "onboarding_path": "/api/provider-onboarding/document-ocr-provider",
    },
    "document.layout.parse": {
        "provider_id": "paddleLayoutProvider",
        "onboarding_id": "document-layout-provider",
        "onboarding_path": "/api/provider-onboarding/document-layout-provider",
    },
    "document.vlm.parse": {
        "provider_id": "documentVlmProvider",
        "onboarding_id": "document-vlm-provider",
        "onboarding_path": "/api/provider-onboarding/document-vlm-provider",
    },
    "knowledge.rag.retrieve": {
        "provider_id": "unifiedKnowledgeProvider",
        "onboarding_id": "knowledge-rag-provider",
        "onboarding_path": "/api/provider-onboarding/knowledge-rag-provider",
    },
    "knowledge.graph.query": {
        "provider_id": "unifiedKnowledgeProvider",
        "onboarding_id": "knowledge-rag-provider",
        "onboarding_path": "/api/provider-onboarding/knowledge-rag-provider",
    },
    "voice.asr.vosk": {
        "provider_id": "unifiedTTSandASR",
        "onboarding_id": "voice-asr-tts-provider",
        "onboarding_path": "/api/provider-onboarding/voice-asr-tts-provider",
    },
    "voice.tts.edge": {
        "provider_id": "unifiedTTSandASR",
        "onboarding_id": "voice-asr-tts-provider",
        "onboarding_path": "/api/provider-onboarding/voice-asr-tts-provider",
    },
}

NODE_CAPABILITY_HINTS = {
    "http": "http.request",
    "http request": "http.request",
    "HTTP 请求": "http.request",
    "LinkReaderPlugin": "spreadsheet.table.extract",
    "get_file_type": "document.file_type.detect",
    "ocr": "document.ocr.extract",
    "vlm": "document.vlm.parse",
    "rag": "knowledge.rag.retrieve",
}


def build_dependency_summary(workflow: Mapping[str, Any]) -> Dict[str, Any]:
    dependencies = dict(workflow.get("dependencies") or {})
    return {
        "tools": list(dependencies.get("tools") or []),
        "mcp_capabilities": list(dependencies.get("mcp_capabilities") or []),
        "skills": list(dependencies.get("skills") or []),
        "providers": list(dependencies.get("providers") or []),
        "knowledge_sources": list(dependencies.get("knowledge_sources") or []),
        "runtime_capabilities": list(dependencies.get("runtime_capabilities") or []),
    }


def build_dependency_mapping(workflow: Mapping[str, Any]) -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []
    dependencies = dict(workflow.get("dependencies") or {})
    source = dict(workflow.get("source") or {})

    items.extend(_map_runtime_capabilities(dependencies))
    items.extend(_map_named_dependencies("provider", dependencies.get("providers") or []))
    items.extend(_map_named_dependencies("tool", dependencies.get("tools") or []))
    items.extend(_map_named_dependencies("mcp_capability", dependencies.get("mcp_capabilities") or []))
    items.extend(_map_named_dependencies("skill", dependencies.get("skills") or []))
    items.extend(_map_unsupported_nodes(source.get("unsupported_nodes") or []))
    items.extend(_map_file_inputs(workflow))

    blockers = [
        item.get("blocker")
        for item in items
        if item.get("status") == "blocked" and item.get("blocker")
    ]
    if blockers:
        status = "blocked"
        reason = "One or more workflow dependencies are not mapped to supported runtime capabilities."
    else:
        status = "ready"
        reason = "All declared dependencies are mapped for lab diagnostics."

    return {
        "status": status,
        "reason": reason,
        "blockers": blockers,
        "items": items,
    }


def build_dependency_contract(workflow: Mapping[str, Any]) -> Dict[str, Any]:
    summary = build_dependency_summary(workflow)
    mapping = build_dependency_mapping(workflow)
    return {
        "summary": summary,
        "mapping": mapping,
        "blockers": list(mapping.get("blockers") or []),
    }


def build_dependency_blockers(workflow: Mapping[str, Any]) -> List[str]:
    return list(build_dependency_contract(workflow).get("blockers") or [])


def _map_runtime_capabilities(dependencies: Mapping[str, Any]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for capability_id in _string_list(dependencies.get("runtime_capabilities")):
        provider = PROVIDER_BACKED_CAPABILITIES.get(capability_id)
        supported = capability_id in SUPPORTED_RUNTIME_CAPABILITIES
        item = _base_dependency_item(
            kind="runtime_capability",
            source=capability_id,
            target_capability_id=capability_id,
            status="ready" if supported else "blocked",
            blocker=None if supported else f"missing_runtime_capability:{capability_id}",
        )
        if provider is not None:
            provider_fields = _provider_dependency_fields(capability_id, provider)
            item.update(provider_fields)
            provider_status = str(provider_fields.get("provider_readiness", {}).get("configuration_status") or "")
            item["status"] = "ready" if provider_status == "configured" else "blocked"
            item["blocker"] = (
                None
                if provider_status == "configured"
                else f"provider_not_ready:{provider['provider_id']}:{capability_id}"
            )
        items.append(item)
    return items


def _map_named_dependencies(kind: str, values: Any) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for value in _string_list(values):
        item = _base_dependency_item(
            kind=kind,
            source=value,
            target_capability_id=None,
            status="declared",
        )
        if kind == "provider":
            item["provider_id"] = value
            item.update(_provider_fields_for_provider_id(value))
            onboarding_id = str(item.get("onboarding_id") or "").strip()
            provider_status = str(item.get("provider_readiness", {}).get("configuration_status") or "")
            if onboarding_id and provider_status != "configured":
                item["kind"] = "explicit_blocker"
                item["status"] = "blocked"
                item["blocker"] = f"provider_not_ready:{value}"
            else:
                item["kind"] = "provider_backed"
        items.append(item)
    return items


def _map_unsupported_nodes(nodes: Any) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for node in _string_list(nodes):
        target = _capability_hint_for_node(node)
        supported = bool(target and target in SUPPORTED_RUNTIME_CAPABILITIES)
        provider = PROVIDER_BACKED_CAPABILITIES.get(str(target or ""))
        item = _base_dependency_item(
            kind="coze_node",
            source=node,
            target_capability_id=target,
            status="mapped" if supported or provider is not None else "blocked",
            blocker=None if supported or provider is not None else f"unsupported_coze_node:{node}",
        )
        if provider is not None:
            item.update(_provider_dependency_fields(str(target), provider))
            provider_status = str(item.get("provider_readiness", {}).get("configuration_status") or "")
            if provider_status != "configured":
                item["kind"] = "explicit_blocker"
                item["status"] = "blocked"
                item["blocker"] = f"provider_not_ready:{provider['provider_id']}:{target}"
            else:
                item["kind"] = "runtime_capability"
        elif supported:
            item["kind"] = "runtime_capability"
        else:
            item["kind"] = "explicit_blocker"
        items.append(item)
    return items


def _map_file_inputs(workflow: Mapping[str, Any]) -> List[Dict[str, Any]]:
    schema = workflow.get("inputs", {}).get("schema") if isinstance(workflow.get("inputs"), Mapping) else {}
    properties = schema.get("properties") if isinstance(schema, Mapping) else {}
    items: List[Dict[str, Any]] = []
    if isinstance(properties, Mapping) and "file" in properties:
            items.append(
                {
                    **_base_dependency_item(
                        kind="artifact_input",
                        source="inputs.file",
                    target_capability_id=None,
                    status="declared",
                ),
                "accepted_reference_types": ["content_ref", "artifact_id", "runtime_file_ref"],
                "external_invocation_note": "External callers should pass runtime-managed references, not local filesystem paths.",
                "artifact_flow": {
                    "local_fixture": "allowed_for_lab_only",
                    "upload": "expected_before_invocation",
                    "artifact_id": "supported_contract_shape",
                    "provider_owned_job_ref": "supported_for_large_or_async_document_workflows",
                },
            }
        )
    return items


def _provider_dependency_fields(capability_id: str, provider: Mapping[str, str]) -> Dict[str, Any]:
    provider_id = str(provider.get("provider_id") or "")
    onboarding_id = str(provider.get("onboarding_id") or "")
    fields = {
        "provider_id": provider_id,
        "onboarding_id": onboarding_id,
        "onboarding_path": str(provider.get("onboarding_path") or ""),
        "service_provider_detail_path": f"/api/service-providers/{provider_id}",
        "service_provider_evidence_preview_path": f"/api/service-providers/{provider_id}/evidence-preview",
        "provider_readiness": _provider_readiness(onboarding_id),
        "invocation_boundary": "explicit_capability_only",
        "default_chat_behavior": "not_changed",
    }
    fields["provider_readiness"]["capability_id"] = capability_id
    return fields


def _provider_fields_for_provider_id(provider_id: str) -> Dict[str, Any]:
    onboarding_service = get_provider_onboarding_catalog_service()
    onboarding_id = onboarding_service.onboarding_id_for_provider(provider_id)
    if not onboarding_id:
        return {
            "provider_readiness": {
                "configuration_status": "unknown",
                "checks": [],
                "recommended_action": "inspect_provider_registration",
            },
            "service_provider_detail_path": f"/api/service-providers/{provider_id}",
            "service_provider_evidence_preview_path": f"/api/service-providers/{provider_id}/evidence-preview",
            "default_chat_behavior": "not_changed",
        }
    return {
        "onboarding_id": onboarding_id,
        "onboarding_path": f"/api/provider-onboarding/{onboarding_id}",
        "service_provider_detail_path": f"/api/service-providers/{provider_id}",
        "service_provider_evidence_preview_path": f"/api/service-providers/{provider_id}/evidence-preview",
        "provider_readiness": _provider_readiness(onboarding_id),
        "default_chat_behavior": "not_changed",
    }


def _provider_readiness(onboarding_id: str) -> Dict[str, Any]:
    if not onboarding_id:
        return {
            "configuration_status": "unknown",
            "checks": [],
            "recommended_action": "inspect_provider_registration",
        }
    readiness = get_provider_onboarding_catalog_service().get_readiness(onboarding_id)
    return {
        "configuration_status": readiness.get("configuration_status"),
        "checks": list(readiness.get("checks") or []),
        "recommended_action": readiness.get("recommended_action"),
        "live_probe_hints": dict(readiness.get("live_probe_hints") or {}),
        "boundaries": dict(readiness.get("boundaries") or {}),
    }


def _base_dependency_item(
    *,
    kind: str,
    source: str,
    target_capability_id: str | None,
    status: str,
    blocker: str | None = None,
) -> Dict[str, Any]:
    return {
        "kind": kind,
        "source": source,
        "target_capability_id": target_capability_id,
        "status": status,
        "provider_id": None,
        "onboarding_id": None,
        "onboarding_path": None,
        "service_provider_detail_path": None,
        "service_provider_evidence_preview_path": None,
        "blocker": blocker,
    }


def _capability_hint_for_node(node: str) -> str | None:
    normalized = node.strip()
    lowered = normalized.lower()
    for key, capability_id in NODE_CAPABILITY_HINTS.items():
        if key in normalized or key.lower() in lowered:
            return capability_id
    return None


def _string_list(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    return [str(value).strip() for value in values if str(value).strip()]
