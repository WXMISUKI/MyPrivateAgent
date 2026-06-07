"""Caller-side local corpus trial for an external Knowledge Provider."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx


LOCAL_CORPUS_TRIAL_ID = "local-knowledge-provider-corpus-trial-v1"
DEFAULT_PROVIDER_BASE_URL = "http://127.0.0.1:8020"
DEFAULT_SOURCE_ID = "company_profile_2025_trial"
DEFAULT_TOP_K = 3
DEFAULT_TIMEOUT_SECONDS = 5.0
DEFAULT_OUTPUT_DIR = Path("docs/integration/local-knowledge-provider-corpus-trial")
OUTPUT_JSON_FILENAME = "local-knowledge-provider-corpus-trial.json"
OUTPUT_MARKDOWN_FILENAME = "local-knowledge-provider-corpus-trial.md"


@dataclass(frozen=True)
class CorpusTrialCase:
    id: str
    query: str
    expected_mode: str
    description: str


@dataclass(frozen=True)
class CorpusTrialCaseResult:
    id: str
    query: str
    expected_mode: str
    status: str
    reason_code: str
    retrieve_ok: bool
    retrieve_count: int
    answer_ok: bool
    answer_status: str | None
    citations: list[str] = field(default_factory=list)
    allowed_citations: list[str] = field(default_factory=list)
    invalid_citations: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class LocalKnowledgeProviderCorpusTrial:
    id: str
    generated_at: str
    provider_base_url: str
    source_id: str
    top_k: int
    decision: str
    reason_code: str
    api_key_configured: bool
    summary: dict[str, Any]
    cases: list[CorpusTrialCaseResult]
    recommended_actions: list[str] = field(default_factory=list)
    non_goals: list[str] = field(default_factory=list)
    json_path: Path | None = None
    markdown_path: Path | None = None


DEFAULT_CASES = [
    CorpusTrialCase(
        id="business_scope",
        query="公司主营业务是什么？",
        expected_mode="answerable",
        description="Main business scope should be answerable from company profile.",
    ),
    CorpusTrialCase(
        id="qualifications",
        query="公司有哪些资质？",
        expected_mode="answerable",
        description="Company qualifications should be answerable from company profile.",
    ),
    CorpusTrialCase(
        id="organization",
        query="公司组织机构包括哪些部门？",
        expected_mode="answerable",
        description="Organization departments should be answerable from company profile.",
    ),
    CorpusTrialCase(
        id="project_scale",
        query="公司完成过哪些工程规模？",
        expected_mode="answerable",
        description="Historical engineering scale should be answerable from company profile.",
    ),
    CorpusTrialCase(
        id="negative_refund_policy",
        query="售后退款凭证规则",
        expected_mode="insufficient_evidence",
        description="Unrelated refund policy should not be answered from company profile.",
    ),
]


def build_local_knowledge_provider_corpus_trial(
    *,
    provider_base_url: str = DEFAULT_PROVIDER_BASE_URL,
    provider_api_key: str | None = None,
    source_id: str = DEFAULT_SOURCE_ID,
    cases: list[CorpusTrialCase] | None = None,
    top_k: int = DEFAULT_TOP_K,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    transport: httpx.BaseTransport | None = None,
) -> LocalKnowledgeProviderCorpusTrial:
    base_url = provider_base_url.rstrip("/")
    active_cases = cases or DEFAULT_CASES
    headers = _provider_headers(provider_api_key)
    with httpx.Client(timeout=timeout_seconds, transport=transport, trust_env=False) as client:
        catalog_result = _catalog_source_check(client, base_url, source_id, headers)
        manifest_result = _manifest_check(client, base_url, source_id, headers)
        if catalog_result is not None or manifest_result is not None:
            case_results = [
                result for result in [catalog_result, manifest_result] if result is not None
            ]
            decision, reason_code = _decision(case_results)
            return _trial(
                provider_base_url=base_url,
                source_id=source_id,
                top_k=top_k,
                api_key_configured=bool(provider_api_key),
                decision=decision,
                reason_code=reason_code,
                cases=case_results,
            )

        case_results = [
            _run_case(
                client,
                provider_base_url=base_url,
                source_id=source_id,
                case=case,
                top_k=top_k,
                headers=headers,
            )
            for case in active_cases
        ]

    decision, reason_code = _decision(case_results)
    return _trial(
        provider_base_url=base_url,
        source_id=source_id,
        top_k=top_k,
        api_key_configured=bool(provider_api_key),
        decision=decision,
        reason_code=reason_code,
        cases=case_results,
    )


def export_local_knowledge_provider_corpus_trial(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    provider_base_url: str = DEFAULT_PROVIDER_BASE_URL,
    provider_api_key: str | None = None,
    source_id: str = DEFAULT_SOURCE_ID,
    case_file: Path | None = None,
    top_k: int = DEFAULT_TOP_K,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    transport: httpx.BaseTransport | None = None,
) -> LocalKnowledgeProviderCorpusTrial:
    output_dir.mkdir(parents=True, exist_ok=True)
    trial = build_local_knowledge_provider_corpus_trial(
        provider_base_url=provider_base_url,
        provider_api_key=provider_api_key,
        source_id=source_id,
        cases=_load_cases(case_file),
        top_k=top_k,
        timeout_seconds=timeout_seconds,
        transport=transport,
    )
    json_path = output_dir / OUTPUT_JSON_FILENAME
    markdown_path = output_dir / OUTPUT_MARKDOWN_FILENAME
    exported = LocalKnowledgeProviderCorpusTrial(
        id=trial.id,
        generated_at=trial.generated_at,
        provider_base_url=trial.provider_base_url,
        source_id=trial.source_id,
        top_k=trial.top_k,
        decision=trial.decision,
        reason_code=trial.reason_code,
        api_key_configured=trial.api_key_configured,
        summary=trial.summary,
        cases=trial.cases,
        recommended_actions=trial.recommended_actions,
        non_goals=trial.non_goals,
        json_path=json_path,
        markdown_path=markdown_path,
    )
    json_path.write_text(
        json.dumps(local_knowledge_provider_corpus_trial_to_dict(exported), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_local_knowledge_provider_corpus_trial_markdown(exported), encoding="utf-8")
    return exported


def local_knowledge_provider_corpus_trial_to_dict(
    trial: LocalKnowledgeProviderCorpusTrial,
) -> dict[str, Any]:
    payload = asdict(trial)
    if trial.json_path is not None:
        payload["json_path"] = str(trial.json_path)
    if trial.markdown_path is not None:
        payload["markdown_path"] = str(trial.markdown_path)
    return payload


def render_local_knowledge_provider_corpus_trial_markdown(
    trial: LocalKnowledgeProviderCorpusTrial,
) -> str:
    lines = [
        "# Local Knowledge Provider Corpus Trial",
        "",
        f"- Report: `{trial.id}`",
        f"- Decision: `{trial.decision}`",
        f"- Reason: `{trial.reason_code}`",
        f"- Provider Base URL: `{trial.provider_base_url}`",
        f"- Source ID: `{trial.source_id}`",
        f"- API Key Configured: `{trial.api_key_configured}`",
        f"- Generated At: `{trial.generated_at}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    for key, value in trial.summary.items():
        lines.append(f"| `{key}` | `{_format_value(value)}` |")
    lines.extend(
        [
            "",
            "## Cases",
            "",
            "| Case | Expected | Status | Reason | Retrieve | Answer | Citations | Invalid |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )
    for case in trial.cases:
        lines.append(
            f"| `{case.id}` | `{case.expected_mode}` | `{case.status}` | "
            f"`{case.reason_code}` | `{case.retrieve_count}` | "
            f"`{case.answer_status or 'n/a'}` | `{len(case.citations)}` | "
            f"`{len(case.invalid_citations)}` |"
        )
    lines.extend(["", "## Recommended Actions", ""])
    lines.extend(f"- {action}" for action in trial.recommended_actions)
    lines.extend(["", "## Non-Goals", ""])
    lines.extend(f"- {item}" for item in trial.non_goals)
    lines.append("")
    return "\n".join(lines)


def _catalog_source_check(
    client: httpx.Client,
    provider_base_url: str,
    source_id: str,
    headers: dict[str, str],
) -> CorpusTrialCaseResult | None:
    payload, error = _request_json(client, "GET", f"{provider_base_url}/api/rag/sources", headers=headers)
    if error is not None:
        return _blocked_case("catalog_visibility", _error_reason("catalog_http_error", error), error)
    sources = payload.get("knowledge_bases")
    if not isinstance(sources, list):
        return _blocked_case("catalog_visibility", "catalog_contract_mismatch")
    if not any(isinstance(source, dict) and source.get("id") == source_id for source in sources):
        return _blocked_case("catalog_visibility", "source_not_registered")
    return None


def _manifest_check(
    client: httpx.Client,
    provider_base_url: str,
    source_id: str,
    headers: dict[str, str],
) -> CorpusTrialCaseResult | None:
    payload, error = _request_json(
        client,
        "GET",
        f"{provider_base_url}/api/rag/sources/{source_id}/documents",
        headers=headers,
    )
    if error is not None:
        return _blocked_case("source_manifest", _error_reason("manifest_http_error", error), error)
    if payload.get("ok") is not True:
        return _blocked_case("source_manifest", "manifest_not_ok")
    documents = payload.get("result", {}).get("documents", [])
    if not isinstance(documents, list) or not documents:
        return _blocked_case("source_manifest", "manifest_documents_missing")
    return None


def _run_case(
    client: httpx.Client,
    *,
    provider_base_url: str,
    source_id: str,
    case: CorpusTrialCase,
    top_k: int,
    headers: dict[str, str],
) -> CorpusTrialCaseResult:
    request = {
        "query": case.query,
        "knowledge_base_ids": [source_id],
        "top_k": top_k,
    }
    retrieve, retrieve_error = _request_json(
        client,
        "POST",
        f"{provider_base_url}/api/rag/retrieve",
        headers=headers,
        json_payload=request,
    )
    answer, answer_error = _request_json(
        client,
        "POST",
        f"{provider_base_url}/api/rag/answer",
        headers=headers,
        json_payload=request,
    )
    if retrieve_error is not None or answer_error is not None:
        return _case_result(
            case=case,
            status="blocked",
            reason_code=_error_reason("rag_http_error", retrieve_error or answer_error),
            retrieve_ok=False,
            answer_ok=False,
            notes=_error_notes(retrieve_error, answer_error),
        )

    retrieve_ok = retrieve.get("ok") is True
    answer_ok = answer.get("ok") is True
    documents = retrieve.get("result", {}).get("documents", []) if retrieve_ok else []
    answer_result = answer.get("result", {}) if answer_ok else {}
    if not isinstance(documents, list) or not isinstance(answer_result, dict):
        return _case_result(
            case=case,
            status="blocked",
            reason_code="rag_contract_mismatch",
            retrieve_ok=retrieve_ok,
            answer_ok=answer_ok,
        )
    citations = [citation for citation in answer_result.get("citations", []) if isinstance(citation, str)]
    allowed_citations = [
        document.get("citation")
        for document in documents
        if isinstance(document, dict) and isinstance(document.get("citation"), str)
    ]
    invalid_citations = [
        citation for citation in citations if citation not in set(allowed_citations)
    ]
    answer_status = answer_result.get("answer_status")
    if invalid_citations:
        status = "blocked"
        reason_code = "answer_citation_outside_retrieval_allowlist"
    elif not retrieve_ok or not answer_ok:
        status = "blocked"
        reason_code = "rag_contract_not_ok"
    elif case.expected_mode == "answerable":
        if documents and answer_status == "answered" and citations:
            status = "ready"
            reason_code = "answerable_case_passed"
        else:
            status = "review"
            reason_code = "expected_answerable_evidence_missing"
    else:
        if not documents and answer_status == "insufficient_evidence" and not citations:
            status = "ready"
            reason_code = "negative_control_passed"
        else:
            status = "review"
            reason_code = "negative_control_returned_evidence"
    return _case_result(
        case=case,
        status=status,
        reason_code=reason_code,
        retrieve_ok=retrieve_ok,
        retrieve_count=len(documents),
        answer_ok=answer_ok,
        answer_status=str(answer_status) if answer_status else None,
        citations=citations,
        allowed_citations=allowed_citations,
        invalid_citations=invalid_citations,
    )


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


def _decision(cases: list[CorpusTrialCaseResult]) -> tuple[str, str]:
    if any(case.status == "blocked" for case in cases):
        first_blocked = next(case for case in cases if case.status == "blocked")
        return "blocked", first_blocked.reason_code
    if any(case.status == "review" for case in cases):
        return "review", "local_corpus_trial_needs_review"
    return "go", "local_corpus_trial_accepted"


def _trial(
    *,
    provider_base_url: str,
    source_id: str,
    top_k: int,
    api_key_configured: bool,
    decision: str,
    reason_code: str,
    cases: list[CorpusTrialCaseResult],
) -> LocalKnowledgeProviderCorpusTrial:
    return LocalKnowledgeProviderCorpusTrial(
        id=LOCAL_CORPUS_TRIAL_ID,
        generated_at=datetime.now(UTC).isoformat(),
        provider_base_url=provider_base_url,
        source_id=source_id,
        top_k=top_k,
        decision=decision,
        reason_code=reason_code,
        api_key_configured=api_key_configured,
        summary={
            "case_count": len(cases),
            "ready_case_count": sum(1 for case in cases if case.status == "ready"),
            "review_case_count": sum(1 for case in cases if case.status == "review"),
            "blocked_case_count": sum(1 for case in cases if case.status == "blocked"),
            "invalid_citation_count": sum(len(case.invalid_citations) for case in cases),
            "source_binding_status": "not_created",
            "default_chat_retrieval_injection": "not_enabled",
            "graph_execution_status": "not_executed",
            "runtime_promotion_status": "unchanged",
        },
        cases=cases,
        recommended_actions=_recommended_actions(decision),
        non_goals=_non_goals(),
    )


def _case_result(
    *,
    case: CorpusTrialCase,
    status: str,
    reason_code: str,
    retrieve_ok: bool,
    answer_ok: bool,
    retrieve_count: int = 0,
    answer_status: str | None = None,
    citations: list[str] | None = None,
    allowed_citations: list[str] | None = None,
    invalid_citations: list[str] | None = None,
    notes: list[str] | None = None,
) -> CorpusTrialCaseResult:
    return CorpusTrialCaseResult(
        id=case.id,
        query=case.query,
        expected_mode=case.expected_mode,
        status=status,
        reason_code=reason_code,
        retrieve_ok=retrieve_ok,
        retrieve_count=retrieve_count,
        answer_ok=answer_ok,
        answer_status=answer_status,
        citations=citations or [],
        allowed_citations=allowed_citations or [],
        invalid_citations=invalid_citations or [],
        notes=notes or [],
    )


def _blocked_case(
    case_id: str,
    reason_code: str,
    error: dict[str, Any] | None = None,
) -> CorpusTrialCaseResult:
    return CorpusTrialCaseResult(
        id=case_id,
        query="",
        expected_mode="provider_contract",
        status="blocked",
        reason_code=reason_code,
        retrieve_ok=False,
        retrieve_count=0,
        answer_ok=False,
        answer_status=None,
        notes=_error_notes(error),
    )


def _load_cases(case_file: Path | None) -> list[CorpusTrialCase]:
    if case_file is None:
        return DEFAULT_CASES
    payload = json.loads(case_file.read_text(encoding="utf-8"))
    return [
        CorpusTrialCase(
            id=str(item["id"]),
            query=str(item["query"]),
            expected_mode=str(item["expected_mode"]),
            description=str(item.get("description", "")),
        )
        for item in payload
    ]


def _provider_headers(provider_api_key: str | None) -> dict[str, str]:
    if not provider_api_key:
        return {}
    return {
        "Authorization": f"Bearer {provider_api_key}",
        "X-Provider-Api-Key": provider_api_key,
    }


def _error_reason(default: str, error: dict[str, Any] | None) -> str:
    if error and error.get("code") == "PROVIDER_UNREACHABLE":
        return "local_provider_unreachable"
    return default


def _error_notes(*errors: dict[str, Any] | None) -> list[str]:
    notes: list[str] = []
    for error in errors:
        if error:
            notes.append(f"{error.get('code')}: {error.get('message')}")
    return notes


def _recommended_actions(decision: str) -> list[str]:
    if decision == "go":
        return [
            "use_company_profile_source_for_explicit_myprivateagent_domain_trial",
            "keep_source_to_agent_binding_in_caller_control_plane",
            "do_not_enable_default_chat_retrieval_without_grounding_promotion",
        ]
    if decision == "review":
        return [
            "review_provider_corpus_queries_or_citation_behavior",
            "rerun_local_corpus_trial_after_adjustment",
        ]
    return [
        "start_or_repair_unified_knowledge_provider",
        "fix_blocked_source_manifest_retrieve_answer_or_citation_contract",
        "rerun_local_corpus_trial_after_fix",
    ]


def _non_goals() -> list[str]:
    return [
        "does_not_start_provider_service",
        "does_not_create_source_to_agent_binding",
        "does_not_mutate_domain_agent_manifest",
        "does_not_write_audit_or_memory_records",
        "does_not_enable_default_chat_retrieval_injection",
        "does_not_run_myprivateagent_orchestration",
        "does_not_promote_retrieval_backend",
        "does_not_start_ocr_services",
        "does_not_execute_graphrag",
    ]


def _format_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)
