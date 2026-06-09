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
DEFAULT_TRIAL_AGENT_ID = "myprivateagent_repo_side_trial"
OUTPUT_JSON_FILENAME = "unified-knowledge-provider-trial-outcome.json"
OUTPUT_MARKDOWN_FILENAME = "unified-knowledge-provider-trial-outcome.md"
PROVIDER_READINESS_CHECK_ID = "provider_document_rag_readiness"


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
    agent_id: str
    api_key_configured: bool
    summary: dict[str, Any]
    checks: list[TrialCheck]
    provider_feedback_input: dict[str, Any]
    notes: list[str] = field(default_factory=list)
    json_path: Path | None = None
    markdown_path: Path | None = None


def build_knowledge_provider_trial_outcome(
    *,
    provider_base_url: str = DEFAULT_PROVIDER_BASE_URL,
    provider_api_key: str | None = None,
    provider_readiness_path: Path | None = None,
    agent_id: str = DEFAULT_TRIAL_AGENT_ID,
    query: str = DEFAULT_TRIAL_QUERY,
    timeout_seconds: float = 5.0,
    transport: httpx.BaseTransport | None = None,
) -> KnowledgeProviderTrialOutcome:
    base_url = provider_base_url.rstrip("/")
    headers = _provider_headers(provider_api_key)
    checks: list[TrialCheck] = []
    provider_readiness_summary = _provider_readiness_summary(provider_readiness_path)
    if provider_readiness_path is not None:
        checks.append(_provider_readiness_check(provider_readiness_path))
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
        agent_id=agent_id,
        api_key_configured=bool(provider_api_key),
        summary={
            "total_checks": len(checks),
            "ready_checks": len([check for check in checks if check.status == "ready"]),
            "review_checks": len([check for check in checks if check.status == "review"]),
            "blocked_checks": len([check for check in checks if check.status == "blocked"]),
            "ready_check_ids": [check.id for check in checks if check.status == "ready"],
            "review_check_ids": [check.id for check in checks if check.status == "review"],
            "blocked_check_ids": [check.id for check in checks if check.status == "blocked"],
            "agent_id": agent_id,
            "query": query,
            "provider_document_rag_readiness": provider_readiness_summary,
            "source_binding_policy_owner": "caller",
            "runtime_promotion_status": "unchanged",
        },
        checks=checks,
        provider_feedback_input=_build_provider_feedback_input(
            overall_status=status,
            decision=_decision(status),
            provider_base_url=base_url,
            agent_id=agent_id,
            query=query,
            checks=checks,
        ),
        notes=[
            "This outcome is a read-only MyPrivateAgent repo-side trial over the external knowledge provider contract.",
            "The trial does not create source-to-agent binding, approvals, audit records, runtime promotions, or final answer policy.",
            "Provider API key values are never written to this artifact.",
            "The provider_feedback_input payload is caller-owned and can be passed into unifiedKnowledgeRAG Phase 25 feedback without manual field reconstruction.",
        ],
    )


def export_knowledge_provider_trial_outcome(
    *,
    output_dir: Path = Path("docs/integration/unified-knowledge-provider-trial"),
    provider_base_url: str = DEFAULT_PROVIDER_BASE_URL,
    provider_api_key: str | None = None,
    provider_readiness_path: Path | None = None,
    agent_id: str = DEFAULT_TRIAL_AGENT_ID,
    query: str = DEFAULT_TRIAL_QUERY,
    timeout_seconds: float = 5.0,
    transport: httpx.BaseTransport | None = None,
) -> KnowledgeProviderTrialOutcome:
    output_dir.mkdir(parents=True, exist_ok=True)
    outcome = build_knowledge_provider_trial_outcome(
        provider_base_url=provider_base_url,
        provider_api_key=provider_api_key,
        provider_readiness_path=provider_readiness_path,
        agent_id=agent_id,
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
        agent_id=outcome.agent_id,
        api_key_configured=outcome.api_key_configured,
        summary=outcome.summary,
        checks=outcome.checks,
        provider_feedback_input=outcome.provider_feedback_input,
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
        f"- Agent ID: `{outcome.agent_id}`",
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
    lines.extend(["", "## Provider Feedback Input", "", "| Field | Value |", "|---|---|"])
    for key, value in outcome.provider_feedback_input.items():
        lines.append(f"| `{key}` | `{_format_value(value)}` |")
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


def _provider_readiness_summary(provider_readiness_path: Path | None) -> dict[str, Any]:
    if provider_readiness_path is None:
        return {
            "supplied": False,
            "status": "not_supplied",
            "recommended_action": "supply_phase24_provider_readiness_artifact_for_document_rag_trial_context",
        }
    check = _provider_readiness_check(provider_readiness_path)
    summary = dict(check.summary)
    summary.update(
        {
            "supplied": True,
            "status": check.status,
            "recommended_action": check.recommended_action,
        }
    )
    if check.error is not None:
        summary["error"] = check.error
    return summary


def _provider_readiness_check(provider_readiness_path: Path) -> TrialCheck:
    endpoint = str(provider_readiness_path)
    payload, error = _load_provider_readiness(provider_readiness_path)
    if error is not None:
        return _blocked(PROVIDER_READINESS_CHECK_ID, endpoint, "refresh_phase24_document_rag_readiness", error)

    decision = str(payload.get("decision") or "unknown")
    readiness_state = str(payload.get("trial_readiness_state") or "unknown")
    status = str(payload.get("status") or "unknown")
    primitive_gate_status = str(_nested(payload, "summary", "primitive_gate_status") or "unknown")
    ready = decision == "go" and readiness_state == "ready_for_repo_side_document_rag_trial"
    blocked = decision == "blocked" or status == "blocked"
    check_status = "ready" if ready else "blocked" if blocked else "review"
    return TrialCheck(
        id=PROVIDER_READINESS_CHECK_ID,
        endpoint=endpoint,
        status=check_status,
        summary={
            "decision": decision,
            "trial_readiness_state": readiness_state,
            "provider_status": status,
            "primitive_gate_status": primitive_gate_status,
            "generated_at": payload.get("generated_at"),
        },
        recommended_action="no_action_required" if ready else "resolve_phase24_document_rag_readiness",
        error=None if check_status != "blocked" else {"code": "PROVIDER_DOCUMENT_RAG_READINESS_BLOCKED"},
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
    allowed_citations = _string_items(
        evidence_pack.get("allowed_citations") or metadata.get("allowed_citations")
    )
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
            "allowed_citations": allowed_citations,
            "allowed_citation_count": len(allowed_citations),
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


def _load_provider_readiness(path: Path) -> tuple[dict[str, Any], dict[str, Any] | None]:
    if not path.exists():
        return {}, {"code": "PROVIDER_READINESS_MISSING", "message": f"Missing provider readiness artifact: {path}"}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        return {}, {"code": "PROVIDER_READINESS_INVALID_JSON", "message": str(exc)}
    if not isinstance(payload, dict):
        return {}, {
            "code": "PROVIDER_READINESS_INVALID_SHAPE",
            "message": "Provider readiness artifact must be a JSON object.",
        }
    return payload, None


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


def _build_provider_feedback_input(
    *,
    overall_status: str,
    decision: str,
    provider_base_url: str,
    agent_id: str,
    query: str,
    checks: list[TrialCheck],
) -> dict[str, Any]:
    retrieve_check = next((check for check in checks if check.id == "rag_retrieve"), None)
    retrieve_summary = retrieve_check.summary if retrieve_check is not None else {}
    retrieve_error = retrieve_check.error if retrieve_check is not None else None
    allowed_citations = _string_items(retrieve_summary.get("allowed_citations"))
    retrieve_status = _phase25_retrieve_status(retrieve_check, allowed_citations)
    retrieve_reason_code = _phase25_retrieve_reason_code(
        retrieve_check=retrieve_check,
        retrieve_status=retrieve_status,
        allowed_citations=allowed_citations,
    )
    blockers = _provider_feedback_blockers(checks, retrieve_check, allowed_citations)
    warnings = _provider_feedback_warnings(checks, retrieve_check, allowed_citations)
    evidence_pack_status = str(retrieve_summary.get("evidence_pack_status") or "unknown")
    citation_policy = str(retrieve_summary.get("citation_policy") or "")
    payload: dict[str, Any] = {
        "live_trial_status": _phase25_live_trial_status(overall_status),
        "reason_code": _phase25_live_trial_reason_code(overall_status, decision),
        "provider_base_url": provider_base_url,
        "agent_id": agent_id,
        "query": query,
        "provider_retrieve": {
            "status": retrieve_status,
            "reason_code": retrieve_reason_code,
            "document_count": _int(retrieve_summary.get("document_count"), fallback=0) or 0,
            "evidence_pack_status": evidence_pack_status,
            "citation_policy": citation_policy,
            "allowed_citations": allowed_citations,
            "blockers": blockers,
            "warnings": warnings,
            "evidence_pack": {
                "status": evidence_pack_status,
                "citation_policy": citation_policy,
                "allowed_citations": allowed_citations,
            },
        },
        "blockers": blockers,
        "warnings": warnings,
    }
    if retrieve_error is not None:
        payload["provider_retrieve"]["error"] = retrieve_error
    return payload


def _phase25_live_trial_status(status: str) -> str:
    if status == "trial_passed":
        return "go"
    if status == "trial_review":
        return "review"
    return "blocked"


def _phase25_live_trial_reason_code(status: str, decision: str) -> str:
    if status == "trial_passed":
        return "repo_side_trial_passed"
    if status == "trial_review":
        return "repo_side_trial_needs_review"
    if decision:
        return "repo_side_trial_blocked"
    return "repo_side_trial_unclassified"


def _phase25_retrieve_status(
    retrieve_check: TrialCheck | None,
    allowed_citations: list[str],
) -> str:
    if retrieve_check is None:
        return "blocked"
    if retrieve_check.status == "blocked":
        return "blocked"
    if retrieve_check.status == "review":
        return "review"
    if not allowed_citations:
        return "review"
    return "ready"


def _phase25_retrieve_reason_code(
    *,
    retrieve_check: TrialCheck | None,
    retrieve_status: str,
    allowed_citations: list[str],
) -> str:
    if retrieve_check is None:
        return "provider_retrieve_check_missing"
    if retrieve_check.error is not None:
        return str(retrieve_check.error.get("code") or "provider_retrieve_failed")
    if retrieve_status == "ready":
        return "provider_retrieve_ready"
    if retrieve_check.status == "review":
        return "provider_retrieve_needs_review"
    if retrieve_status == "review" and not allowed_citations:
        return "provider_retrieve_allowed_citations_missing"
    return "provider_retrieve_blocked"


def _provider_feedback_blockers(
    checks: list[TrialCheck],
    retrieve_check: TrialCheck | None,
    allowed_citations: list[str],
) -> list[str]:
    blockers = [check.id for check in checks if check.status == "blocked"]
    if retrieve_check is None:
        blockers.append("rag_retrieve_check_missing")
    if retrieve_check is not None and retrieve_check.status == "blocked" and retrieve_check.error is not None:
        error_code = str(retrieve_check.error.get("code") or "").strip()
        if error_code:
            blockers.append(error_code)
    if retrieve_check is not None and retrieve_check.status == "ready" and not allowed_citations:
        blockers.append("provider_retrieve_allowed_citations_missing")
    return blockers


def _provider_feedback_warnings(
    checks: list[TrialCheck],
    retrieve_check: TrialCheck | None,
    allowed_citations: list[str],
) -> list[str]:
    warnings = [check.id for check in checks if check.status == "review"]
    if retrieve_check is not None:
        evidence_pack_status = str(retrieve_check.summary.get("evidence_pack_status") or "")
        if evidence_pack_status == "insufficient_evidence":
            warnings.append("provider_retrieve_insufficient_evidence")
    if retrieve_check is not None and retrieve_check.status == "ready" and not allowed_citations:
        warnings.append("provider_retrieve_allowed_citations_missing")
    return warnings


def _int(value: Any, *, fallback: int | None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _nested(payload: dict[str, Any], *keys: str) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _string_items(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str) and item.strip()]


def _format_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)
