"""Read-only local knowledge base user-loop package for MyPrivateAgent."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.capability_runtime.local_knowledge_provider_corpus_trial import (
    DEFAULT_OUTPUT_DIR as DEFAULT_CORPUS_TRIAL_OUTPUT_DIR,
    DEFAULT_SOURCE_ID,
    OUTPUT_JSON_FILENAME as CORPUS_TRIAL_JSON_FILENAME,
)
from backend.services.company_profile_explicit_api_local_smoke_service import (
    DEFAULT_OUTPUT_DIR as DEFAULT_EXPLICIT_API_SMOKE_OUTPUT_DIR,
    OUTPUT_JSON_FILENAME as EXPLICIT_API_SMOKE_JSON_FILENAME,
)


LOCAL_KNOWLEDGE_BASE_USER_LOOP_VERSION = "local-knowledge-base-user-loop-v1"
DEFAULT_OUTPUT_DIR = Path("docs/integration/local-knowledge-base-user-loop")
OUTPUT_JSON_FILENAME = "local-knowledge-base-user-loop.json"
OUTPUT_MARKDOWN_FILENAME = "local-knowledge-base-user-loop.md"

DEFAULT_CORPUS_TRIAL_JSON_PATH = DEFAULT_CORPUS_TRIAL_OUTPUT_DIR / CORPUS_TRIAL_JSON_FILENAME
DEFAULT_EXPLICIT_API_SMOKE_JSON_PATH = DEFAULT_EXPLICIT_API_SMOKE_OUTPUT_DIR / EXPLICIT_API_SMOKE_JSON_FILENAME

EXPECTED_BOUNDARY = {
    "default_chat_retrieval_injection": "disabled",
    "chat_invocation": "not_performed",
    "model_invocation": "not_performed",
    "tool_execution": "not_performed",
    "source_binding_creation": "not_performed",
    "memory_write": "not_performed",
    "audit_write": "not_performed",
    "trace_write": "not_performed",
    "graphrag_execution": "not_promoted",
    "runtime_behavior_changed": False,
}


@dataclass(frozen=True)
class LocalKnowledgeBaseUserLoopReport:
    contract_version: str
    generated_at: str
    decision: str
    reason_code: str
    recommended_next_action: str
    source: dict[str, Any]
    entrypoint: dict[str, Any]
    citation_summary: dict[str, Any]
    suggested_questions: list[dict[str, str]]
    boundary: dict[str, Any]
    inputs: dict[str, Any]
    warnings: list[dict[str, Any]] = field(default_factory=list)
    blockers: list[dict[str, Any]] = field(default_factory=list)
    json_path: Path | None = None
    markdown_path: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.json_path is not None:
            payload["json_path"] = str(self.json_path)
        if self.markdown_path is not None:
            payload["markdown_path"] = str(self.markdown_path)
        return payload


def build_local_knowledge_base_user_loop(
    *,
    corpus_trial_json_path: Path = DEFAULT_CORPUS_TRIAL_JSON_PATH,
    explicit_api_smoke_json_path: Path = DEFAULT_EXPLICIT_API_SMOKE_JSON_PATH,
    source_id: str = DEFAULT_SOURCE_ID,
) -> LocalKnowledgeBaseUserLoopReport:
    clean_source_id = _clean(source_id) or DEFAULT_SOURCE_ID
    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    corpus_trial = _load_json(corpus_trial_json_path, "corpus_trial", blockers)
    explicit_api_smoke = _load_json(explicit_api_smoke_json_path, "explicit_api_smoke", blockers)

    if corpus_trial:
        _check_decision(
            corpus_trial,
            component="corpus_trial",
            blockers=blockers,
            warnings=warnings,
            blocked_reason_code="corpus_trial_blocked",
        )
        _check_source(corpus_trial.get("source_id"), clean_source_id, "corpus_trial", blockers)

    if explicit_api_smoke:
        _check_decision(
            explicit_api_smoke,
            component="explicit_api_smoke",
            blockers=blockers,
            warnings=warnings,
            blocked_reason_code="explicit_api_smoke_blocked",
        )
        _check_boundary(explicit_api_smoke.get("boundary"), blockers)

    citations = _string_list(explicit_api_smoke.get("citations")) if explicit_api_smoke else []
    if explicit_api_smoke:
        _check_citations(citations, clean_source_id, blockers)

    provider_base_url = _clean(explicit_api_smoke.get("provider_base_url")) or _clean(corpus_trial.get("provider_base_url"))
    _check_provider_alignment(corpus_trial, explicit_api_smoke, warnings)

    decision, reason_code = _decision(blockers, warnings)
    return LocalKnowledgeBaseUserLoopReport(
        contract_version=LOCAL_KNOWLEDGE_BASE_USER_LOOP_VERSION,
        generated_at=datetime.now(UTC).isoformat(),
        decision=decision,
        reason_code=reason_code,
        recommended_next_action=_next_action(decision),
        source=_source_summary(corpus_trial, clean_source_id, provider_base_url),
        entrypoint=_entrypoint_summary(explicit_api_smoke),
        citation_summary=_citation_summary(citations, clean_source_id),
        suggested_questions=_suggested_questions(),
        boundary=_boundary_summary(explicit_api_smoke.get("boundary") if explicit_api_smoke else {}),
        inputs={
            "corpus_trial_json_path": str(corpus_trial_json_path),
            "explicit_api_smoke_json_path": str(explicit_api_smoke_json_path),
        },
        warnings=warnings,
        blockers=blockers,
    )


def export_local_knowledge_base_user_loop(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    **kwargs: Any,
) -> LocalKnowledgeBaseUserLoopReport:
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_local_knowledge_base_user_loop(**kwargs)
    json_path = output_dir / OUTPUT_JSON_FILENAME
    markdown_path = output_dir / OUTPUT_MARKDOWN_FILENAME
    exported = LocalKnowledgeBaseUserLoopReport(
        contract_version=report.contract_version,
        generated_at=report.generated_at,
        decision=report.decision,
        reason_code=report.reason_code,
        recommended_next_action=report.recommended_next_action,
        source=report.source,
        entrypoint=report.entrypoint,
        citation_summary=report.citation_summary,
        suggested_questions=report.suggested_questions,
        boundary=report.boundary,
        inputs=report.inputs,
        warnings=report.warnings,
        blockers=report.blockers,
        json_path=json_path,
        markdown_path=markdown_path,
    )
    json_path.write_text(json.dumps(exported.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_local_knowledge_base_user_loop_markdown(exported), encoding="utf-8")
    return exported


def render_local_knowledge_base_user_loop_markdown(report: LocalKnowledgeBaseUserLoopReport) -> str:
    lines = [
        "# Local Knowledge Base User Loop",
        "",
        f"- Contract: `{report.contract_version}`",
        f"- Decision: `{report.decision}`",
        f"- Reason: `{report.reason_code}`",
        f"- Next Action: `{report.recommended_next_action}`",
        f"- Source: `{report.source.get('source_id')}`",
        f"- Provider: `{report.source.get('provider_base_url')}`",
        f"- Generated At: `{report.generated_at}`",
        "",
        "## Entry Point",
        "",
        "| Field | Value |",
        "|---|---|",
    ]
    for key, value in report.entrypoint.items():
        lines.append(f"| `{key}` | `{_format_value(value)}` |")
    lines.extend(
        [
            "",
            "## Suggested Questions",
            "",
            "| Question | Expected Mode |",
            "|---|---|",
        ]
    )
    for question in report.suggested_questions:
        lines.append(f"| {question['query']} | `{question['expected_mode']}` |")
    lines.extend(
        [
            "",
            "## Citations",
            "",
            f"- Count: `{report.citation_summary.get('citation_count')}`",
            f"- Values: `{json.dumps(report.citation_summary.get('citations'), ensure_ascii=False)}`",
            "",
            "## Boundary",
            "",
            "| Boundary | Value |",
            "|---|---|",
        ]
    )
    for key, value in report.boundary.items():
        lines.append(f"| `{key}` | `{_format_value(value)}` |")
    lines.extend(["", "## Warnings", ""])
    lines.append(json.dumps(report.warnings, ensure_ascii=False) if report.warnings else "None.")
    lines.extend(["", "## Blockers", ""])
    lines.append(json.dumps(report.blockers, ensure_ascii=False) if report.blockers else "None.")
    lines.append("")
    return "\n".join(lines)


def _load_json(path: Path, component: str, blockers: list[dict[str, Any]]) -> dict[str, Any]:
    if not path.exists():
        blockers.append(_issue(component, "input_artifact_missing", status="blocked", path=path))
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        blockers.append(_issue(component, "input_artifact_unreadable", status="blocked", path=path, message=str(exc)))
        return {}
    if not isinstance(payload, dict):
        blockers.append(_issue(component, "input_artifact_invalid_shape", status="blocked", path=path))
        return {}
    return payload


def _check_decision(
    payload: dict[str, Any],
    *,
    component: str,
    blockers: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    blocked_reason_code: str,
) -> None:
    decision = _clean(payload.get("decision")).lower()
    reason_code = _clean(payload.get("reason_code")) or blocked_reason_code
    if decision == "go":
        return
    issue = _issue(component, reason_code, status="blocked" if decision == "blocked" else "review")
    if decision == "blocked":
        blockers.append(issue)
    else:
        warnings.append(issue)


def _check_source(actual: Any, expected: str, component: str, blockers: list[dict[str, Any]]) -> None:
    clean_actual = _clean(actual)
    if clean_actual and clean_actual != expected:
        blockers.append(
            _issue(component, "source_id_mismatch", status="blocked", expected=expected, actual=clean_actual)
        )


def _check_boundary(boundary: Any, blockers: list[dict[str, Any]]) -> None:
    if not isinstance(boundary, dict):
        blockers.append(_issue("boundary", "runtime_boundary_missing", status="blocked"))
        return
    for key, expected_value in EXPECTED_BOUNDARY.items():
        actual = boundary.get(key)
        if actual != expected_value:
            blockers.append(
                _issue(
                    "boundary",
                    "runtime_boundary_drift",
                    status="blocked",
                    field=key,
                    expected=expected_value,
                    actual=actual,
                )
            )


def _check_citations(citations: list[str], source_id: str, blockers: list[dict[str, Any]]) -> None:
    if not citations:
        blockers.append(_issue("explicit_api_smoke", "citations_missing", status="blocked"))
        return
    invalid = [citation for citation in citations if not citation.startswith(f"{source_id}#")]
    if invalid:
        blockers.append(
            _issue(
                "explicit_api_smoke",
                "citation_source_mismatch",
                status="blocked",
                expected_prefix=f"{source_id}#",
                actual=invalid,
            )
        )


def _check_provider_alignment(
    corpus_trial: dict[str, Any],
    explicit_api_smoke: dict[str, Any],
    warnings: list[dict[str, Any]],
) -> None:
    corpus_url = _clean(corpus_trial.get("provider_base_url"))
    explicit_url = _clean(explicit_api_smoke.get("provider_base_url"))
    if corpus_url and explicit_url and corpus_url != explicit_url:
        warnings.append(
            _issue(
                "provider",
                "provider_base_url_mismatch",
                status="review",
                corpus_trial=corpus_url,
                explicit_api_smoke=explicit_url,
            )
        )


def _decision(blockers: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> tuple[str, str]:
    if blockers:
        return "blocked", _clean(blockers[0].get("reason_code")) or "local_knowledge_base_user_loop_blocked"
    if warnings:
        return "review", "local_knowledge_base_user_loop_review_required"
    return "go", "local_knowledge_base_user_loop_ready"


def _next_action(decision: str) -> str:
    if decision == "go":
        return "start_local_business_qa_trial_with_explicit_company_profile_entrypoint"
    if decision == "review":
        return "review_local_knowledge_warnings_before_broader_user_trial"
    return "fix_required_local_knowledge_user_loop_inputs_before_trial"


def _source_summary(corpus_trial: dict[str, Any], source_id: str, provider_base_url: str) -> dict[str, Any]:
    summary = corpus_trial.get("summary") if isinstance(corpus_trial.get("summary"), dict) else {}
    return {
        "source_id": source_id,
        "provider_base_url": provider_base_url or None,
        "corpus_trial_decision": corpus_trial.get("decision"),
        "corpus_trial_reason_code": corpus_trial.get("reason_code"),
        "case_count": summary.get("case_count"),
        "ready_case_count": summary.get("ready_case_count"),
        "review_case_count": summary.get("review_case_count"),
        "blocked_case_count": summary.get("blocked_case_count"),
        "invalid_citation_count": summary.get("invalid_citation_count"),
    }


def _entrypoint_summary(explicit_api_smoke: dict[str, Any]) -> dict[str, Any]:
    return {
        "endpoint": explicit_api_smoke.get("endpoint"),
        "agent_id": explicit_api_smoke.get("agent_id"),
        "domain": explicit_api_smoke.get("domain"),
        "query": explicit_api_smoke.get("query"),
        "http_status_code": explicit_api_smoke.get("http_status_code"),
        "api_status": explicit_api_smoke.get("api_status"),
        "document_count": explicit_api_smoke.get("document_count"),
        "answer_preview": explicit_api_smoke.get("answer_preview"),
    }


def _citation_summary(citations: list[str], source_id: str) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "citation_count": len(citations),
        "citations": citations,
    }


def _boundary_summary(boundary: Any) -> dict[str, Any]:
    if not isinstance(boundary, dict):
        return {}
    return {key: boundary.get(key) for key in EXPECTED_BOUNDARY}


def _suggested_questions() -> list[dict[str, str]]:
    return [
        {"query": "公司主营业务是什么？", "expected_mode": "answerable"},
        {"query": "公司有哪些资质？", "expected_mode": "answerable"},
        {"query": "公司组织机构包括哪些部门？", "expected_mode": "answerable"},
        {"query": "公司完成过哪些工程规模？", "expected_mode": "answerable"},
        {"query": "售后退款凭证规则", "expected_mode": "insufficient_evidence"},
    ]


def _issue(component: str, reason_code: str, *, status: str, **details: Any) -> dict[str, Any]:
    issue = {
        "component": component,
        "status": status,
        "reason_code": reason_code,
    }
    for key, value in details.items():
        if isinstance(value, Path):
            issue[key] = str(value)
        elif value is not None:
            issue[key] = value
    return issue


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_clean(item) for item in value if _clean(item)]


def _format_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def _clean(value: Any) -> str:
    return str(value or "").strip()
