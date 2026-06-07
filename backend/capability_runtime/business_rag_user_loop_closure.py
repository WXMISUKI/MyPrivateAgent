"""Local closure report for the MyPrivateAgent business RAG user loop."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.capability_runtime.local_knowledge_provider_corpus_trial import (
    DEFAULT_OUTPUT_DIR as DEFAULT_CORPUS_TRIAL_OUTPUT_DIR,
    OUTPUT_JSON_FILENAME as CORPUS_TRIAL_JSON_FILENAME,
)
from backend.services.company_profile_explicit_api_local_smoke_service import (
    DEFAULT_OUTPUT_DIR as DEFAULT_EXPLICIT_API_SMOKE_OUTPUT_DIR,
    OUTPUT_JSON_FILENAME as EXPLICIT_API_SMOKE_JSON_FILENAME,
)


CLOSURE_CONTRACT_VERSION = "business-rag-user-loop-closure-v1"
DEFAULT_SOURCE_ID = "company_profile_2025_trial"
DEFAULT_OUTPUT_DIR = Path("docs/integration/business-rag-user-loop-closure")
OUTPUT_JSON_FILENAME = "business-rag-user-loop-closure.json"
OUTPUT_MARKDOWN_FILENAME = "business-rag-user-loop-closure.md"

DEFAULT_CORPUS_TRIAL_JSON_PATH = DEFAULT_CORPUS_TRIAL_OUTPUT_DIR / CORPUS_TRIAL_JSON_FILENAME
DEFAULT_EXPLICIT_API_SMOKE_JSON_PATH = DEFAULT_EXPLICIT_API_SMOKE_OUTPUT_DIR / EXPLICIT_API_SMOKE_JSON_FILENAME


@dataclass(frozen=True)
class BusinessRagUserLoopClosureReport:
    contract_version: str
    generated_at: str
    decision: str
    reason_code: str
    recommended_next_action: str
    source_id: str
    provider_base_url: str | None
    corpus_trial: dict[str, Any] = field(default_factory=dict)
    explicit_api_smoke: dict[str, Any] = field(default_factory=dict)
    citations: list[str] = field(default_factory=list)
    blockers: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    boundary: dict[str, Any] = field(default_factory=dict)
    inputs: dict[str, Any] = field(default_factory=dict)
    json_path: Path | None = None
    markdown_path: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.json_path is not None:
            payload["json_path"] = str(self.json_path)
        if self.markdown_path is not None:
            payload["markdown_path"] = str(self.markdown_path)
        return payload


def build_business_rag_user_loop_closure(
    *,
    corpus_trial_json_path: Path = DEFAULT_CORPUS_TRIAL_JSON_PATH,
    explicit_api_smoke_json_path: Path = DEFAULT_EXPLICIT_API_SMOKE_JSON_PATH,
    source_id: str = DEFAULT_SOURCE_ID,
) -> BusinessRagUserLoopClosureReport:
    clean_source_id = _clean(source_id) or DEFAULT_SOURCE_ID
    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    corpus_trial = _load_json(corpus_trial_json_path, "corpus_trial", blockers)
    explicit_api_smoke = _load_json(explicit_api_smoke_json_path, "explicit_api_smoke", blockers)

    if corpus_trial:
        _check_decision(
            payload=corpus_trial,
            component="corpus_trial",
            decision_field="decision",
            go_value="go",
            blockers=blockers,
            warnings=warnings,
        )
        _check_corpus_source(corpus_trial, clean_source_id, blockers)

    boundary: dict[str, Any] = {}
    citations: list[str] = []
    if explicit_api_smoke:
        _check_decision(
            payload=explicit_api_smoke,
            component="explicit_api_smoke",
            decision_field="decision",
            go_value="go",
            blockers=blockers,
            warnings=warnings,
        )
        boundary = dict(explicit_api_smoke.get("boundary") or {})
        citations = _string_list(explicit_api_smoke.get("citations"))
        _check_boundary(boundary, blockers)
        _check_citations(citations, clean_source_id, blockers)

    provider_base_url = _provider_base_url(corpus_trial, explicit_api_smoke)
    if corpus_trial and explicit_api_smoke:
        _check_provider_url_alignment(corpus_trial, explicit_api_smoke, warnings)

    decision, reason_code = _decision(blockers, warnings)
    return BusinessRagUserLoopClosureReport(
        contract_version=CLOSURE_CONTRACT_VERSION,
        generated_at=datetime.now(UTC).isoformat(),
        decision=decision,
        reason_code=reason_code,
        recommended_next_action=_next_action(decision),
        source_id=clean_source_id,
        provider_base_url=provider_base_url,
        corpus_trial=_corpus_summary(corpus_trial),
        explicit_api_smoke=_explicit_api_summary(explicit_api_smoke),
        citations=citations,
        blockers=blockers,
        warnings=warnings,
        boundary=boundary,
        inputs={
            "corpus_trial_json_path": str(corpus_trial_json_path),
            "explicit_api_smoke_json_path": str(explicit_api_smoke_json_path),
        },
    )


def export_business_rag_user_loop_closure(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    **kwargs: Any,
) -> BusinessRagUserLoopClosureReport:
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_business_rag_user_loop_closure(**kwargs)
    json_path = output_dir / OUTPUT_JSON_FILENAME
    markdown_path = output_dir / OUTPUT_MARKDOWN_FILENAME
    exported = BusinessRagUserLoopClosureReport(
        contract_version=report.contract_version,
        generated_at=report.generated_at,
        decision=report.decision,
        reason_code=report.reason_code,
        recommended_next_action=report.recommended_next_action,
        source_id=report.source_id,
        provider_base_url=report.provider_base_url,
        corpus_trial=report.corpus_trial,
        explicit_api_smoke=report.explicit_api_smoke,
        citations=report.citations,
        blockers=report.blockers,
        warnings=report.warnings,
        boundary=report.boundary,
        inputs=report.inputs,
        json_path=json_path,
        markdown_path=markdown_path,
    )
    json_path.write_text(json.dumps(exported.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_business_rag_user_loop_closure_markdown(exported), encoding="utf-8")
    return exported


def render_business_rag_user_loop_closure_markdown(report: BusinessRagUserLoopClosureReport) -> str:
    lines = [
        "# Business RAG User Loop Closure",
        "",
        f"- Contract: `{report.contract_version}`",
        f"- Decision: `{report.decision}`",
        f"- Reason: `{report.reason_code}`",
        f"- Next Action: `{report.recommended_next_action}`",
        f"- Source: `{report.source_id}`",
        f"- Provider: `{report.provider_base_url}`",
        f"- Generated At: `{report.generated_at}`",
        "",
        "## Inputs",
        "",
        "| Input | Path |",
        "|---|---|",
    ]
    for key, value in report.inputs.items():
        lines.append(f"| `{key}` | `{value}` |")
    lines.extend(
        [
            "",
            "## Result",
            "",
            "| Metric | Value |",
            "|---|---|",
            f"| `corpus_trial_decision` | `{report.corpus_trial.get('decision')}` |",
            f"| `explicit_api_smoke_decision` | `{report.explicit_api_smoke.get('decision')}` |",
            f"| `citation_count` | `{len(report.citations)}` |",
            f"| `citations` | `{json.dumps(report.citations, ensure_ascii=False)}` |",
            "",
            "## Boundary",
            "",
            "| Boundary | Value |",
            "|---|---|",
        ]
    )
    for key, value in report.boundary.items():
        lines.append(f"| `{key}` | `{value}` |")
    lines.extend(["", "## Blockers", ""])
    lines.append(json.dumps(report.blockers, ensure_ascii=False) if report.blockers else "None.")
    lines.extend(["", "## Warnings", ""])
    lines.append(json.dumps(report.warnings, ensure_ascii=False) if report.warnings else "None.")
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
    *,
    payload: dict[str, Any],
    component: str,
    decision_field: str,
    go_value: str,
    blockers: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> None:
    decision = _clean(payload.get(decision_field)).lower()
    reason_code = _clean(payload.get("reason_code")) or "unknown"
    if decision == go_value:
        return
    issue = _issue(component, reason_code, status="blocked" if decision == "blocked" else "review")
    if decision == "blocked":
        blockers.append(issue)
    else:
        warnings.append(issue)


def _check_corpus_source(payload: dict[str, Any], source_id: str, blockers: list[dict[str, Any]]) -> None:
    actual = _clean(payload.get("source_id"))
    if actual and actual != source_id:
        blockers.append(
            _issue(
                "corpus_trial",
                "source_id_mismatch",
                status="blocked",
                expected=source_id,
                actual=actual,
            )
        )


def _check_boundary(boundary: dict[str, Any], blockers: list[dict[str, Any]]) -> None:
    expected = {
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
    for key, expected_value in expected.items():
        actual = boundary.get(key)
        if actual != expected_value:
            blockers.append(
                _issue(
                    "boundary",
                    "explicit_boundary_drift",
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


def _check_provider_url_alignment(
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


def _provider_base_url(corpus_trial: dict[str, Any], explicit_api_smoke: dict[str, Any]) -> str | None:
    return _clean(explicit_api_smoke.get("provider_base_url")) or _clean(corpus_trial.get("provider_base_url")) or None


def _corpus_summary(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    return {
        "id": payload.get("id"),
        "generated_at": payload.get("generated_at"),
        "decision": payload.get("decision"),
        "reason_code": payload.get("reason_code"),
        "provider_base_url": payload.get("provider_base_url"),
        "source_id": payload.get("source_id"),
        "case_count": summary.get("case_count"),
        "ready_case_count": summary.get("ready_case_count"),
        "blocked_case_count": summary.get("blocked_case_count"),
        "invalid_citation_count": summary.get("invalid_citation_count"),
    }


def _explicit_api_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "contract_version": payload.get("contract_version"),
        "generated_at": payload.get("generated_at"),
        "decision": payload.get("decision"),
        "reason_code": payload.get("reason_code"),
        "endpoint": payload.get("endpoint"),
        "agent_id": payload.get("agent_id"),
        "domain": payload.get("domain"),
        "query": payload.get("query"),
        "provider_base_url": payload.get("provider_base_url"),
        "http_status_code": payload.get("http_status_code"),
        "document_count": payload.get("document_count"),
        "api_status": payload.get("api_status"),
        "answer_preview": payload.get("answer_preview"),
    }


def _decision(blockers: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> tuple[str, str]:
    if blockers:
        return "blocked", _clean(blockers[0].get("reason_code")) or "business_rag_user_loop_blocked"
    if warnings:
        return "review", "business_rag_user_loop_review_required"
    return "go", "business_rag_user_loop_ready"


def _next_action(decision: str) -> str:
    if decision == "go":
        return "use_explicit_company_profile_rag_for_local_business_qa_trial"
    if decision == "review":
        return "review_business_rag_user_loop_warnings_before_trial"
    return "rerun_or_fix_required_local_rag_trial_artifacts"


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


def _clean(value: Any) -> str:
    return str(value or "").strip()

