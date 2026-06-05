"""Repo-side trial outcome for the unified knowledge provider."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx


TRIAL_OUTCOME_ID = "unified-knowledge-provider-repo-side-trial-v1"
DEFAULT_PROVIDER_BASE_URL = "http://127.0.0.1:8020"
DEFAULT_TRIAL_QUERY = "refund policy"
OUTPUT_JSON_FILENAME = "unified-knowledge-provider-trial-outcome.json"
OUTPUT_MARKDOWN_FILENAME = "unified-knowledge-provider-trial-outcome.md"


@dataclass(frozen=True)
class TrialCheck:
    id: str
    endpoint: str
    status: str
    summary: dict[str, Any]
    recommended_action: str
    error: dict[str, Any] | None = None


@dataclass(frozen=True)
class KnowledgeProviderTrialOutcome:
    id: str
    generated_at: str
    status: str
    decision: str
    provider_base_url: str
    api_key_configured: bool
    summary: dict[str, Any]
    checks: list[TrialCheck]
    notes: list[str] = field(default_factory=list)
    json_path: Path | None = None
    markdown_path: Path | None = None


def build_knowledge_provider_trial_outcome(
    *,
    provider_base_url: str = DEFAULT_PROVIDER_BASE_URL,
    provider_api_key: str | None = None,
    query: str = DEFAULT_TRIAL_QUERY,
    timeout_seconds: float = 5.0,
    transport: httpx.BaseTransport | None = None,
) -> KnowledgeProviderTrialOutcome:
    base_url = provider_base_url.rstrip("/")
    headers = _provider_headers(provider_api_key)
    checks: list[TrialCheck] = []
    with httpx.Client(timeout=timeout_seconds, transport=transport, trust_env=False) as client:
        checks.append(_health_check(client, base_url))
        checks.append(_manifest_check(client, base_url, headers))
        checks.append(_preflight_check(client, base_url, headers))
        source_bindings_check, selected_source_ids = _source_bindings_check(client, base_url, headers)
        checks.append(source_bindings_check)
        checks.append(_retrieve_check(client, base_url, headers, query, selected_source_ids))

    status = _overall_status(checks)
    return KnowledgeProviderTrialOutcome(
        id=TRIAL_OUTCOME_ID,
        generated_at=datetime.now(UTC).isoformat(),
        status=status,
        decision=_decision(status),
        provider_base_url=base_url,
        api_key_configured=bool(provider_api_key),
        summary={
            "total_checks": len(checks),
            "ready_checks": len([check for check in checks if check.status == "ready"]),
            "review_checks": len([check for check in checks if check.status == "review"]),
            "blocked_checks": len([check for check in checks if check.status == "blocked"]),
            "ready_check_ids": [check.id for check in checks if check.status == "ready"],
            "review_check_ids": [check.id for check in checks if check.status == "review"],
            "blocked_check_ids": [check.id for check in checks if check.status == "blocked"],
            "query": query,
            "source_binding_policy_owner": "caller",
            "runtime_promotion_status": "unchanged",
        },
        checks=checks,
        notes=[
            "This outcome is a read-only MyPrivateAgent repo-side trial over the external knowledge provider contract.",
            "The trial does not create source-to-agent binding, approvals, audit records, runtime promotions, or final answer policy.",
            "Provider API key values are never written to this artifact.",
        ],
    )


def export_knowledge_provider_trial_outcome(
    *,
    output_dir: Path = Path("docs/integration/unified-knowledge-provider-trial"),
    provider_base_url: str = DEFAULT_PROVIDER_BASE_URL,
    provider_api_key: str | None = None,
    query: str = DEFAULT_TRIAL_QUERY,
    timeout_seconds: float = 5.0,
    transport: httpx.BaseTransport | None = None,
) -> KnowledgeProviderTrialOutcome:
    output_dir.mkdir(parents=True, exist_ok=True)
    outcome = build_knowledge_provider_trial_outcome(
        provider_base_url=provider_base_url,
        provider_api_key=provider_api_key,
        query=query,
        timeout_seconds=timeout_seconds,
        transport=transport,
    )
    json_path = output_dir / OUTPUT_JSON_FILENAME
    markdown_path = output_dir / OUTPUT_MARKDOWN_FILENAME
    exported = KnowledgeProviderTrialOutcome(
        id=outcome.id,
        generated_at=outcome.generated_at,
        status=outcome.status,
        decision=outcome.decision,
        provider_base_url=outcome.provider_base_url,
        api_key_configured=outcome.api_key_configured,
        summary=outcome.summary,
        checks=outcome.checks,
        notes=outcome.notes,
        json_path=json_path,
        markdown_path=markdown_path,
    )
    json_path.write_text(
        json.dumps(knowledge_provider_trial_outcome_to_dict(exported), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_knowledge_provider_trial_outcome_markdown(exported), encoding="utf-8")
    return exported


def knowledge_provider_trial_outcome_to_dict(outcome: KnowledgeProviderTrialOutcome) -> dict[str, Any]:
    payload = asdict(outcome)
    if outcome.json_path is not None:
        payload["json_path"] = str(outcome.json_path)
    if outcome.markdown_path is not None:
        payload["markdown_path"] = str(outcome.markdown_path)
    return payload


def render_knowledge_provider_trial_outcome_markdown(outcome: KnowledgeProviderTrialOutcome) -> str:
    lines = [
        "# Unified Knowledge Provider Trial Outcome",
        "",
        f"- Report: `{outcome.id}`",
        f"- Status: `{outcome.status}`",
        f"- Decision: `{outcome.decision}`",
        f"- Provider Base URL: `{outcome.provider_base_url}`",
        f"- API Key Configured: `{outcome.api_key_configured}`",
        f"- Generated At: `{outcome.generated_at}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    for key, value in outcome.summary.items():
        lines.append(f"| `{key}` | `{_format_value(value)}` |")
    lines.extend(["", "## Checks", "", "| Check | Endpoint | Status | Recommended Action | Summary |", "|---|---|---|---|---|"])
    for check in outcome.checks:
        lines.append(
            f"| `{check.id}` | `{check.endpoint}` | `{check.status}` | "
            f"`{check.recommended_action}` | `{_format_value(check.summary)}` |"
        )
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in outcome.notes)
    lines.append("")
    return "\n".join(lines)


def _health_check(client: httpx.Client, base_url: str) -> TrialCheck:
    endpoint = "/health"
    payload, error = _request_json(client, "GET", f"{base_url}{endpoint}")
    if error is not None:
        return _blocked("provider_health", endpoint, "start_or_repair_unified_knowledge_provider", error)
    status = str(payload.get("status") or "unknown")
    ready = status in {"ok", "ready"}
    return TrialCheck(
        id="provider_health",
        endpoint=endpoint,
        status="ready" if ready else "review",
        summary={"provider_status": status, "service": payload.get("service")},
        recommended_action="no_action_required" if ready else "review_provider_health",
    )


def _manifest_check(client: httpx.Client, base_url: str, headers: dict[str, str]) -> TrialCheck:
    endpoint = "/api/provider/manifest"
    payload, error = _request_json(client, "GET", f"{base_url}{endpoint}", headers=headers)
    if error is not None:
        return _blocked("provider_manifest", endpoint, "repair_provider_manifest_access", error)
    provider_id = str(payload.get("provider_id") or "")
    endpoints = payload.get("endpoints") if isinstance(payload.get("endpoints"), dict) else {}
    required_endpoint_ids = {"preflight", "rag_retrieve", "source_bindings"}
    missing_endpoints = sorted(required_endpoint_ids - set(endpoints))
    if provider_id != "unifiedKnowledgeProvider" or missing_endpoints:
        return TrialCheck(
            id="provider_manifest",
            endpoint=endpoint,
            status="blocked",
            summary={"provider_id": provider_id, "missing_endpoint_ids": missing_endpoints},
            recommended_action="align_provider_manifest_contract",
            error={"code": "PROVIDER_MANIFEST_CONTRACT_MISMATCH"},
        )
    return TrialCheck(
        id="provider_manifest",
        endpoint=endpoint,
        status="ready",
        summary={
            "provider_id": provider_id,
            "contract_version": payload.get("contract_version"),
            "capability_count": len(payload.get("capability_ids") or []),
        },
        recommended_action="no_action_required",
    )


def _preflight_check(client: httpx.Client, base_url: str, headers: dict[str, str]) -> TrialCheck:
    endpoint = "/api/provider/preflight"
    payload, error = _request_json(client, "GET", f"{base_url}{endpoint}", headers=headers)
    if error is not None:
        return _blocked("provider_preflight", endpoint, "repair_provider_preflight_access", error)
    bindable = payload.get("bindable") is True
    status = "ready" if bindable else "review"
    return TrialCheck(
        id="provider_preflight",
        endpoint=endpoint,
        status=status,
        summary={
            "bindable": bindable,
            "status": payload.get("status"),
            "required_capability_count": len(payload.get("required_capability_ids") or []),
        },
        recommended_action="no_action_required" if bindable else "review_provider_preflight",
    )


def _retrieve_check(
    client: httpx.Client,
    base_url: str,
    headers: dict[str, str],
    query: str,
    knowledge_base_ids: list[str],
) -> TrialCheck:
    endpoint = "/api/rag/retrieve"
    payload, error = _request_json(
        client,
        "POST",
        f"{base_url}{endpoint}",
        headers=headers,
        json_payload={"query": query, "knowledge_base_ids": knowledge_base_ids, "top_k": 3},
    )
    if error is not None:
        return _blocked("rag_retrieve", endpoint, "repair_rag_retrieve_access", error)
    result = _result_payload(payload)
    documents = result.get("documents")
    metadata = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
    evidence_pack = metadata.get("evidence_pack") if isinstance(metadata.get("evidence_pack"), dict) else None
    if not isinstance(documents, list) or evidence_pack is None:
        return TrialCheck(
            id="rag_retrieve",
            endpoint=endpoint,
            status="blocked",
            summary={"has_documents": isinstance(documents, list), "has_evidence_pack": evidence_pack is not None},
            recommended_action="align_rag_retrieve_evidence_pack_contract",
            error={"code": "RAG_RETRIEVE_CONTRACT_MISMATCH"},
        )
    pack_status = str(evidence_pack.get("status") or "unknown")
    ready = pack_status in {"answerable", "insufficient_evidence"}
    return TrialCheck(
        id="rag_retrieve",
        endpoint=endpoint,
        status="ready" if ready else "review",
        summary={
            "document_count": len(documents),
            "knowledge_base_ids": knowledge_base_ids,
            "evidence_pack_version": evidence_pack.get("version"),
            "evidence_pack_status": pack_status,
            "citation_policy": evidence_pack.get("citation_policy"),
        },
        recommended_action="no_action_required" if ready else "review_evidence_pack_status",
    )


def _source_bindings_check(
    client: httpx.Client,
    base_url: str,
    headers: dict[str, str],
) -> tuple[TrialCheck, list[str]]:
    endpoint = "/api/provider/source-bindings"
    payload, error = _request_json(client, "GET", f"{base_url}{endpoint}", headers=headers)
    if error is not None:
        return _blocked("source_bindings", endpoint, "repair_source_binding_review_access", error), []
    source_count = _int(payload.get("source_count"), fallback=None)
    if source_count is None:
        source_count = _int(payload.get("total_source_count"), fallback=None)
    bindable_count = _int(payload.get("bindable_source_count"), fallback=None)
    status = str(payload.get("status") or "unknown")
    if source_count is None or bindable_count is None:
        return TrialCheck(
            id="source_bindings",
            endpoint=endpoint,
            status="blocked",
            summary={"status": status, "source_count": source_count, "bindable_source_count": bindable_count},
            recommended_action="align_source_binding_review_contract",
            error={"code": "SOURCE_BINDING_CONTRACT_MISMATCH"},
        ), []
    source_ids = _bindable_source_ids(payload)
    ready = status == "ready" and source_count >= 0 and bindable_count >= 0
    if not source_ids:
        return TrialCheck(
            id="source_bindings",
            endpoint=endpoint,
            status="blocked",
            summary={
                "status": status,
                "source_count": source_count,
                "bindable_source_count": bindable_count,
                "selected_source_ids": [],
            },
            recommended_action="review_source_binding_readiness",
            error={"code": "NO_BINDABLE_SOURCES"},
        ), []
    return TrialCheck(
        id="source_bindings",
        endpoint=endpoint,
        status="ready" if ready else "review",
        summary={
            "status": status,
            "source_count": source_count,
            "bindable_source_count": bindable_count,
            "selected_source_ids": source_ids,
            "source_binding_policy_owner": "caller",
        },
        recommended_action="no_action_required" if ready else "review_source_binding_readiness",
    ), source_ids


def _request_json(
    client: httpx.Client,
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    json_payload: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    try:
        response = client.request(method, url, headers=headers, json=json_payload)
        payload = response.json()
        if not isinstance(payload, dict):
            return {}, {"code": "INVALID_JSON_SHAPE", "message": "Provider returned non-object JSON."}
        if response.status_code >= 400:
            error = payload.get("error") if isinstance(payload.get("error"), dict) else {}
            return {}, {
                "code": str(error.get("code") or "PROVIDER_HTTP_ERROR"),
                "message": str(error.get("message") or response.text or response.status_code),
                "status_code": response.status_code,
            }
        return payload, None
    except httpx.RequestError as exc:
        return {}, {"code": "PROVIDER_UNREACHABLE", "message": str(exc)}
    except ValueError as exc:
        return {}, {"code": "INVALID_JSON", "message": str(exc)}


def _provider_headers(provider_api_key: str | None) -> dict[str, str]:
    if not provider_api_key:
        return {}
    return {
        "Authorization": f"Bearer {provider_api_key}",
        "X-Provider-Api-Key": provider_api_key,
    }


def _result_payload(payload: dict[str, Any]) -> dict[str, Any]:
    result = payload.get("result")
    return result if isinstance(result, dict) else payload


def _bindable_source_ids(payload: dict[str, Any]) -> list[str]:
    sources = payload.get("sources")
    if isinstance(sources, list):
        source_ids = [
            str(source.get("source_id"))
            for source in sources
            if isinstance(source, dict)
            and source.get("bindable") is True
            and source.get("source_id")
        ]
        if source_ids:
            return source_ids[:3]
    source_ids = payload.get("source_ids")
    if isinstance(source_ids, list):
        return [str(source_id) for source_id in source_ids if source_id][:3]
    return []


def _blocked(
    check_id: str,
    endpoint: str,
    recommended_action: str,
    error: dict[str, Any],
) -> TrialCheck:
    return TrialCheck(
        id=check_id,
        endpoint=endpoint,
        status="blocked",
        summary={"error_code": error.get("code"), "error_message": error.get("message")},
        recommended_action=recommended_action,
        error=error,
    )


def _overall_status(checks: list[TrialCheck]) -> str:
    statuses = {check.status for check in checks}
    if "blocked" in statuses:
        return "trial_blocked"
    if "review" in statuses:
        return "trial_review"
    return "trial_passed"


def _decision(status: str) -> str:
    if status == "trial_passed":
        return "proceed_with_myprivateagent_integration_hardening"
    if status == "trial_review":
        return "review_trial_context_before_integration_hardening"
    return "resolve_trial_blockers_before_integration"


def _int(value: Any, *, fallback: int | None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _format_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)
