"""Local RAG question trial entrypoint for already-ingested sources."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

try:
    from backend.capability_runtime.local_knowledge_provider_corpus_trial import (
        DEFAULT_PROVIDER_BASE_URL,
        DEFAULT_SOURCE_ID,
        DEFAULT_TIMEOUT_SECONDS,
        DEFAULT_TOP_K,
    )
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from capability_runtime.local_knowledge_provider_corpus_trial import (
        DEFAULT_PROVIDER_BASE_URL,
        DEFAULT_SOURCE_ID,
        DEFAULT_TIMEOUT_SECONDS,
        DEFAULT_TOP_K,
    )


LOCAL_RAG_QUESTION_TRIAL_ENTRYPOINT_ID = "local-rag-question-trial-entrypoint-v1"
DEFAULT_OUTPUT_DIR = Path("docs/integration/local-rag-question-trial-entrypoint")
OUTPUT_JSON_FILENAME = "local-rag-question-trial-entrypoint.json"
OUTPUT_MARKDOWN_FILENAME = "local-rag-question-trial-entrypoint.md"
DEFAULT_QUESTION = "公司主营业务和服务范围是什么？"


@dataclass(frozen=True)
class LocalRagQuestionTrialReport:
    id: str
    generated_at: str
    provider_base_url: str
    source_id: str
    question: str
    top_k: int
    decision: str
    reason_code: str
    answer_status: str | None
    answer: str
    citations: list[str] = field(default_factory=list)
    allowed_citations: list[str] = field(default_factory=list)
    invalid_citations: list[str] = field(default_factory=list)
    retrieval: dict[str, Any] = field(default_factory=dict)
    evidence_pack: dict[str, Any] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)
    recommended_actions: list[str] = field(default_factory=list)
    non_goals: list[str] = field(default_factory=list)
    api_key_configured: bool = False
    json_path: Path | None = None
    markdown_path: Path | None = None


def export_local_rag_question_trial_entrypoint(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    provider_base_url: str = DEFAULT_PROVIDER_BASE_URL,
    provider_api_key: str | None = None,
    source_id: str = DEFAULT_SOURCE_ID,
    question: str = DEFAULT_QUESTION,
    top_k: int = DEFAULT_TOP_K,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    transport: httpx.BaseTransport | None = None,
) -> LocalRagQuestionTrialReport:
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_local_rag_question_trial_entrypoint(
        provider_base_url=provider_base_url,
        provider_api_key=provider_api_key,
        source_id=source_id,
        question=question,
        top_k=top_k,
        timeout_seconds=timeout_seconds,
        transport=transport,
    )
    json_path = output_dir / OUTPUT_JSON_FILENAME
    markdown_path = output_dir / OUTPUT_MARKDOWN_FILENAME
    exported = LocalRagQuestionTrialReport(
        id=report.id,
        generated_at=report.generated_at,
        provider_base_url=report.provider_base_url,
        source_id=report.source_id,
        question=report.question,
        top_k=report.top_k,
        decision=report.decision,
        reason_code=report.reason_code,
        answer_status=report.answer_status,
        answer=report.answer,
        citations=report.citations,
        allowed_citations=report.allowed_citations,
        invalid_citations=report.invalid_citations,
        retrieval=report.retrieval,
        evidence_pack=report.evidence_pack,
        summary=report.summary,
        recommended_actions=report.recommended_actions,
        non_goals=report.non_goals,
        api_key_configured=report.api_key_configured,
        json_path=json_path,
        markdown_path=markdown_path,
    )
    json_path.write_text(
        json.dumps(local_rag_question_trial_entrypoint_to_dict(exported), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_local_rag_question_trial_entrypoint_markdown(exported), encoding="utf-8")
    return exported


def build_local_rag_question_trial_entrypoint(
    *,
    provider_base_url: str = DEFAULT_PROVIDER_BASE_URL,
    provider_api_key: str | None = None,
    source_id: str = DEFAULT_SOURCE_ID,
    question: str = DEFAULT_QUESTION,
    top_k: int = DEFAULT_TOP_K,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    transport: httpx.BaseTransport | None = None,
) -> LocalRagQuestionTrialReport:
    base_url = str(provider_base_url or DEFAULT_PROVIDER_BASE_URL).rstrip("/")
    normalized_source_id = str(source_id or "").strip()
    normalized_question = str(question or "").strip()
    normalized_top_k = _positive_int(top_k) or DEFAULT_TOP_K
    if not normalized_source_id:
        return _report(
            provider_base_url=base_url,
            provider_api_key=provider_api_key,
            source_id=normalized_source_id,
            question=normalized_question,
            top_k=normalized_top_k,
            decision="blocked",
            reason_code="source_id_required",
        )
    if not normalized_question:
        return _report(
            provider_base_url=base_url,
            provider_api_key=provider_api_key,
            source_id=normalized_source_id,
            question=normalized_question,
            top_k=normalized_top_k,
            decision="blocked",
            reason_code="question_required",
        )

    headers = _provider_headers(provider_api_key)
    request_payload = {
        "query": normalized_question,
        "knowledge_base_ids": [normalized_source_id],
        "top_k": normalized_top_k,
    }
    with httpx.Client(timeout=timeout_seconds, transport=transport, trust_env=False) as client:
        retrieve, retrieve_error = _request_json(
            client,
            "POST",
            f"{base_url}/api/rag/retrieve",
            headers=headers,
            json_payload=request_payload,
        )
        if retrieve_error is not None:
            return _report(
                provider_base_url=base_url,
                provider_api_key=provider_api_key,
                source_id=normalized_source_id,
                question=normalized_question,
                top_k=normalized_top_k,
                decision="blocked",
                reason_code=_error_reason("retrieve_http_error", retrieve_error),
                retrieval={"error": retrieve_error},
            )
        answer, answer_error = _request_json(
            client,
            "POST",
            f"{base_url}/api/rag/answer",
            headers=headers,
            json_payload=request_payload,
        )
        if answer_error is not None:
            return _report(
                provider_base_url=base_url,
                provider_api_key=provider_api_key,
                source_id=normalized_source_id,
                question=normalized_question,
                top_k=normalized_top_k,
                decision="blocked",
                reason_code=_error_reason("answer_http_error", answer_error),
                retrieval=_retrieval_summary(retrieve),
                evidence_pack={},
            )

    retrieve_ok = retrieve.get("ok") is True
    answer_ok = answer.get("ok") is True
    documents = retrieve.get("result", {}).get("documents", []) if retrieve_ok else []
    answer_result = answer.get("result", {}) if answer_ok else {}
    if not isinstance(documents, list) or not isinstance(answer_result, dict):
        return _report(
            provider_base_url=base_url,
            provider_api_key=provider_api_key,
            source_id=normalized_source_id,
            question=normalized_question,
            top_k=normalized_top_k,
            decision="blocked",
            reason_code="rag_question_trial_contract_mismatch",
            retrieval=_retrieval_summary(retrieve),
            evidence_pack={},
        )

    allowed_citations = [
        document.get("citation")
        for document in documents
        if isinstance(document, dict) and isinstance(document.get("citation"), str)
    ]
    citations = [citation for citation in answer_result.get("citations", []) if isinstance(citation, str)]
    invalid_citations = [citation for citation in citations if citation not in set(allowed_citations)]
    answer_status = str(answer_result.get("answer_status") or "")
    evidence_pack = answer_result.get("evidence_pack") if isinstance(answer_result.get("evidence_pack"), dict) else {}
    answer_text = str(answer_result.get("answer") or "")

    if invalid_citations:
        decision = "review"
        reason_code = "answer_citation_outside_retrieval_allowlist"
    elif not retrieve_ok or not answer_ok:
        decision = "blocked"
        reason_code = "rag_question_trial_contract_not_ok"
    elif answer_status == "answered" and documents and citations:
        decision = "go"
        reason_code = "rag_question_answered"
    elif answer_status == "insufficient_evidence" and not invalid_citations:
        decision = "go"
        reason_code = "rag_question_insufficient_evidence"
    else:
        decision = "review"
        reason_code = "rag_question_answer_status_needs_review"

    return _report(
        provider_base_url=base_url,
        provider_api_key=provider_api_key,
        source_id=normalized_source_id,
        question=normalized_question,
        top_k=normalized_top_k,
        decision=decision,
        reason_code=reason_code,
        answer_status=answer_status or None,
        answer=answer_text,
        citations=citations,
        allowed_citations=allowed_citations,
        invalid_citations=invalid_citations,
        retrieval=_retrieval_summary(retrieve),
        evidence_pack=evidence_pack,
    )


def local_rag_question_trial_entrypoint_to_dict(report: LocalRagQuestionTrialReport) -> dict[str, Any]:
    payload = asdict(report)
    if report.json_path is not None:
        payload["json_path"] = str(report.json_path)
    if report.markdown_path is not None:
        payload["markdown_path"] = str(report.markdown_path)
    return payload


def render_local_rag_question_trial_entrypoint_markdown(report: LocalRagQuestionTrialReport) -> str:
    lines = [
        "# Local RAG Question Trial Entrypoint",
        "",
        f"- Report: `{report.id}`",
        f"- Decision: `{report.decision}`",
        f"- Reason: `{report.reason_code}`",
        f"- Provider Base URL: `{report.provider_base_url}`",
        f"- Source ID: `{report.source_id}`",
        f"- Question: `{report.question}`",
        f"- Answer Status: `{report.answer_status or 'n/a'}`",
        f"- Evidence Status: `{report.evidence_pack.get('status') or 'n/a'}`",
        f"- Generated At: `{report.generated_at}`",
        "",
        "## Answer",
        "",
        report.answer or "(empty)",
        "",
        "## Citations",
        "",
    ]
    lines.extend(f"- `{citation}`" for citation in report.citations)
    if not report.citations:
        lines.append("- n/a")
    lines.extend(["", "## Summary", "", "| Metric | Value |", "|---|---|"])
    for key, value in report.summary.items():
        lines.append(f"| `{key}` | `{_format_value(value)}` |")
    lines.extend(["", "## Recommended Actions", ""])
    lines.extend(f"- {action}" for action in report.recommended_actions)
    lines.extend(["", "## Non-Goals", ""])
    lines.extend(f"- {item}" for item in report.non_goals)
    lines.append("")
    return "\n".join(lines)


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


def _report(
    *,
    provider_base_url: str,
    provider_api_key: str | None,
    source_id: str,
    question: str,
    top_k: int,
    decision: str,
    reason_code: str,
    answer_status: str | None = None,
    answer: str = "",
    citations: list[str] | None = None,
    allowed_citations: list[str] | None = None,
    invalid_citations: list[str] | None = None,
    retrieval: dict[str, Any] | None = None,
    evidence_pack: dict[str, Any] | None = None,
) -> LocalRagQuestionTrialReport:
    citations = citations or []
    allowed_citations = allowed_citations or []
    invalid_citations = invalid_citations or []
    retrieval = retrieval or {}
    evidence_pack = evidence_pack or {}
    return LocalRagQuestionTrialReport(
        id=LOCAL_RAG_QUESTION_TRIAL_ENTRYPOINT_ID,
        generated_at=datetime.now(UTC).isoformat(),
        provider_base_url=provider_base_url,
        source_id=source_id,
        question=question,
        top_k=top_k,
        decision=decision,
        reason_code=reason_code,
        answer_status=answer_status,
        answer=answer,
        citations=citations,
        allowed_citations=allowed_citations,
        invalid_citations=invalid_citations,
        retrieval=retrieval,
        evidence_pack=evidence_pack,
        summary={
            "final_decision": decision,
            "answer_status": answer_status,
            "retrieved_document_count": retrieval.get("document_count", 0),
            "citation_count": len(citations),
            "invalid_citation_count": len(invalid_citations),
            "evidence_status": evidence_pack.get("status"),
            "source_binding_status": "not_created",
            "default_chat_retrieval_injection": "not_enabled",
            "memory_write_status": "not_written",
            "audit_write_status": "not_written",
            "service_start_status": "not_started",
            "graph_execution_status": "not_executed",
        },
        recommended_actions=_recommended_actions(decision, reason_code),
        non_goals=_non_goals(),
        api_key_configured=bool(provider_api_key),
    )


def _retrieval_summary(payload: dict[str, Any]) -> dict[str, Any]:
    documents = payload.get("result", {}).get("documents", []) if payload.get("ok") is True else []
    if not isinstance(documents, list):
        documents = []
    return {
        "ok": payload.get("ok") is True,
        "document_count": len(documents),
        "citations": [
            document.get("citation")
            for document in documents
            if isinstance(document, dict) and isinstance(document.get("citation"), str)
        ],
        "top_scores": [
            document.get("score")
            for document in documents[:5]
            if isinstance(document, dict) and document.get("score") is not None
        ],
    }


def _provider_headers(provider_api_key: str | None) -> dict[str, str]:
    if not provider_api_key:
        return {}
    return {
        "Authorization": f"Bearer {provider_api_key}",
        "X-Provider-Api-Key": provider_api_key,
    }


def _recommended_actions(decision: str, reason_code: str) -> list[str]:
    if decision == "go":
        if reason_code == "rag_question_insufficient_evidence":
            return ["adjust_question_or_ingest_more_relevant_local_documents"]
        return ["use_this_source_id_for_explicit_local_business_rag_trial"]
    if decision == "review":
        return ["review_provider_answer_citations_or_answer_status", "rerun_question_trial_after_provider_adjustment"]
    return ["start_or_repair_unified_knowledge_provider", "rerun_local_rag_question_trial_after_fix"]


def _non_goals() -> list[str]:
    return [
        "does_not_enable_default_chat_retrieval_injection",
        "does_not_create_source_to_agent_binding",
        "does_not_mutate_domain_agent_manifests",
        "does_not_write_memory_audit_approval_or_governance_records",
        "does_not_start_external_services",
        "does_not_execute_graphrag",
    ]


def _error_reason(default: str, error: dict[str, Any] | None) -> str:
    if error and error.get("code") == "PROVIDER_UNREACHABLE":
        return "local_provider_unreachable"
    return default


def _positive_int(value: Any) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _format_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)
