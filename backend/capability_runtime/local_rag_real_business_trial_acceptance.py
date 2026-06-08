"""Acceptance report for real local business RAG trials."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


LOCAL_RAG_REAL_BUSINESS_TRIAL_ACCEPTANCE_ID = "local-rag-real-business-trial-acceptance-v1"
DEFAULT_OUTPUT_DIR = Path("docs/integration/local-rag-real-business-trial-acceptance")
DEFAULT_UPLOAD_REPORT_PATH = Path(
    "docs/integration/document-rag-upload-to-use-loop/document-rag-upload-to-use-loop.json"
)
DEFAULT_QUESTION_REPORT_PATH = Path(
    "docs/integration/local-rag-question-trial-entrypoint/local-rag-question-trial-entrypoint.json"
)
OUTPUT_JSON_FILENAME = "local-rag-real-business-trial-acceptance.json"
OUTPUT_MARKDOWN_FILENAME = "local-rag-real-business-trial-acceptance.md"


@dataclass(frozen=True)
class AcceptanceQuestionCase:
    id: str
    question: str
    expected_mode: str
    report_path: Path
    decision: str
    reason_code: str
    answer_status: str | None
    status: str
    follow_up_area: str
    citations: list[str] = field(default_factory=list)
    invalid_citations: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class LocalRagRealBusinessTrialAcceptanceReport:
    id: str
    generated_at: str
    decision: str
    reason_code: str
    source_id: str
    document_path: str | None
    provider_base_url: str
    upload_report_path: Path | None
    upload_summary: dict[str, Any]
    question_cases: list[AcceptanceQuestionCase]
    follow_up_area: str
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    recommended_actions: list[str] = field(default_factory=list)
    non_goals: list[str] = field(default_factory=list)
    json_path: Path | None = None
    markdown_path: Path | None = None


def export_local_rag_real_business_trial_acceptance(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    upload_report_path: Path | None = DEFAULT_UPLOAD_REPORT_PATH,
    question_report_paths: list[Path] | None = None,
    expected_modes: dict[str, str] | None = None,
    source_id: str | None = None,
    document_path: str | None = None,
    provider_base_url: str | None = None,
) -> LocalRagRealBusinessTrialAcceptanceReport:
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_local_rag_real_business_trial_acceptance(
        upload_report_path=upload_report_path,
        question_report_paths=question_report_paths,
        expected_modes=expected_modes,
        source_id=source_id,
        document_path=document_path,
        provider_base_url=provider_base_url,
    )
    json_path = output_dir / OUTPUT_JSON_FILENAME
    markdown_path = output_dir / OUTPUT_MARKDOWN_FILENAME
    exported = LocalRagRealBusinessTrialAcceptanceReport(
        id=report.id,
        generated_at=report.generated_at,
        decision=report.decision,
        reason_code=report.reason_code,
        source_id=report.source_id,
        document_path=report.document_path,
        provider_base_url=report.provider_base_url,
        upload_report_path=report.upload_report_path,
        upload_summary=report.upload_summary,
        question_cases=report.question_cases,
        follow_up_area=report.follow_up_area,
        blockers=report.blockers,
        warnings=report.warnings,
        summary=report.summary,
        recommended_actions=report.recommended_actions,
        non_goals=report.non_goals,
        json_path=json_path,
        markdown_path=markdown_path,
    )
    json_path.write_text(
        json.dumps(local_rag_real_business_trial_acceptance_to_dict(exported), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_local_rag_real_business_trial_acceptance_markdown(exported), encoding="utf-8")
    return exported


def build_local_rag_real_business_trial_acceptance(
    *,
    upload_report_path: Path | None = DEFAULT_UPLOAD_REPORT_PATH,
    question_report_paths: list[Path] | None = None,
    expected_modes: dict[str, str] | None = None,
    source_id: str | None = None,
    document_path: str | None = None,
    provider_base_url: str | None = None,
) -> LocalRagRealBusinessTrialAcceptanceReport:
    blockers: list[str] = []
    warnings: list[str] = []
    upload_payload: dict[str, Any] = {}
    upload_summary: dict[str, Any] = {"status": "not_supplied"}
    normalized_upload_path = upload_report_path if upload_report_path and str(upload_report_path) else None
    if normalized_upload_path is not None:
        upload_payload, upload_error = _load_json(normalized_upload_path)
        if upload_error:
            blockers.append(upload_error)
            upload_summary = {"status": "missing_or_invalid", "path": str(normalized_upload_path)}
        else:
            upload_summary = _upload_summary(upload_payload, normalized_upload_path)
            upload_decision = str(upload_payload.get("decision") or "")
            if upload_decision == "blocked":
                blockers.append("upload_report_blocked")
            elif upload_decision == "review":
                warnings.append("upload_report_needs_review")
    else:
        warnings.append("upload_report_not_supplied")

    active_question_paths = question_report_paths if question_report_paths is not None else [DEFAULT_QUESTION_REPORT_PATH]
    question_cases: list[AcceptanceQuestionCase] = []
    for index, question_report_path in enumerate(active_question_paths, start=1):
        payload, error = _load_json(question_report_path)
        if error:
            blockers.append(error)
            question_cases.append(
                AcceptanceQuestionCase(
                    id=f"question_{index}",
                    question="",
                    expected_mode=_expected_mode(question_report_path, expected_modes),
                    report_path=question_report_path,
                    decision="blocked",
                    reason_code="question_report_missing_or_invalid",
                    answer_status=None,
                    status="blocked",
                    follow_up_area="operator_flow",
                    notes=[error],
                )
            )
            continue
        question_case = _question_case(
            payload,
            report_path=question_report_path,
            fallback_id=f"question_{index}",
            expected_mode=_expected_mode(question_report_path, expected_modes),
        )
        question_cases.append(question_case)
        if question_case.status == "blocked":
            blockers.append(f"{question_case.id}:{question_case.reason_code}")
        elif question_case.status == "review":
            warnings.append(f"{question_case.id}:{question_case.reason_code}")

    inferred_source_id = source_id or _first_non_empty(
        upload_payload.get("source_id"),
        upload_payload.get("summary", {}).get("source_id") if isinstance(upload_payload.get("summary"), dict) else None,
        *(case.notes[0].removeprefix("source_id=") for case in question_cases if case.notes and case.notes[0].startswith("source_id=")),
    )
    inferred_document_path = document_path or _first_non_empty(
        upload_payload.get("document_path"),
        upload_payload.get("summary", {}).get("document_path") if isinstance(upload_payload.get("summary"), dict) else None,
    )
    inferred_provider_base_url = provider_base_url or _first_non_empty(
        upload_payload.get("provider_base_url"),
        *(case.notes[1].removeprefix("provider_base_url=") for case in question_cases if len(case.notes) > 1 and case.notes[1].startswith("provider_base_url=")),
    )

    if blockers:
        decision = "blocked"
        reason_code = "local_rag_real_business_trial_blocked"
    elif warnings:
        decision = "review"
        reason_code = "local_rag_real_business_trial_needs_review"
    else:
        decision = "go"
        reason_code = "local_rag_real_business_trial_accepted"
    follow_up_area = _follow_up_area(decision, upload_summary, question_cases, blockers, warnings)
    return LocalRagRealBusinessTrialAcceptanceReport(
        id=LOCAL_RAG_REAL_BUSINESS_TRIAL_ACCEPTANCE_ID,
        generated_at=datetime.now(UTC).isoformat(),
        decision=decision,
        reason_code=reason_code,
        source_id=str(inferred_source_id or ""),
        document_path=str(inferred_document_path) if inferred_document_path else None,
        provider_base_url=str(inferred_provider_base_url or ""),
        upload_report_path=normalized_upload_path,
        upload_summary=upload_summary,
        question_cases=question_cases,
        follow_up_area=follow_up_area,
        blockers=list(dict.fromkeys(blockers)),
        warnings=list(dict.fromkeys(warnings)),
        summary={
            "final_decision": decision,
            "question_case_count": len(question_cases),
            "ready_question_count": sum(1 for case in question_cases if case.status == "ready"),
            "review_question_count": sum(1 for case in question_cases if case.status == "review"),
            "blocked_question_count": sum(1 for case in question_cases if case.status == "blocked"),
            "answerable_case_count": sum(1 for case in question_cases if case.expected_mode == "answerable"),
            "negative_control_case_count": sum(
                1 for case in question_cases if case.expected_mode == "insufficient_evidence"
            ),
            "follow_up_area": follow_up_area,
            "default_chat_retrieval_injection": "not_enabled",
            "source_binding_status": "not_created",
            "memory_write_status": "not_written",
            "audit_write_status": "not_written",
            "trace_write_status": "not_written",
            "service_start_status": "not_started",
            "graph_execution_status": "not_executed",
        },
        recommended_actions=_recommended_actions(decision, follow_up_area),
        non_goals=_non_goals(),
    )


def local_rag_real_business_trial_acceptance_to_dict(
    report: LocalRagRealBusinessTrialAcceptanceReport,
) -> dict[str, Any]:
    payload = asdict(report)
    for key in ["upload_report_path", "json_path", "markdown_path"]:
        if payload[key] is not None:
            payload[key] = str(payload[key])
    for case in payload["question_cases"]:
        case["report_path"] = str(case["report_path"])
    return payload


def render_local_rag_real_business_trial_acceptance_markdown(
    report: LocalRagRealBusinessTrialAcceptanceReport,
) -> str:
    lines = [
        "# Local RAG Real Business Trial Acceptance",
        "",
        f"- Report: `{report.id}`",
        f"- Decision: `{report.decision}`",
        f"- Reason: `{report.reason_code}`",
        f"- Follow-Up Area: `{report.follow_up_area}`",
        f"- Source ID: `{report.source_id or 'n/a'}`",
        f"- Document Path: `{report.document_path or 'n/a'}`",
        f"- Provider Base URL: `{report.provider_base_url or 'n/a'}`",
        f"- Generated At: `{report.generated_at}`",
        "",
        "## Upload",
        "",
        f"- Path: `{report.upload_report_path or 'n/a'}`",
        f"- Decision: `{report.upload_summary.get('decision') or report.upload_summary.get('status') or 'n/a'}`",
        f"- Reason: `{report.upload_summary.get('reason_code') or 'n/a'}`",
        "",
        "## Question Cases",
        "",
        "| Case | Expected | Status | Reason | Answer Status | Citations | Invalid |",
        "|---|---|---|---|---|---|---|",
    ]
    for case in report.question_cases:
        lines.append(
            f"| `{case.id}` | `{case.expected_mode}` | `{case.status}` | `{case.reason_code}` | "
            f"`{case.answer_status or 'n/a'}` | `{len(case.citations)}` | `{len(case.invalid_citations)}` |"
        )
    lines.extend(["", "## Blockers", ""])
    lines.extend(f"- {item}" for item in report.blockers)
    if not report.blockers:
        lines.append("- n/a")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in report.warnings)
    if not report.warnings:
        lines.append("- n/a")
    lines.extend(["", "## Recommended Actions", ""])
    lines.extend(f"- {action}" for action in report.recommended_actions)
    lines.extend(["", "## Non-Goals", ""])
    lines.extend(f"- {item}" for item in report.non_goals)
    lines.append("")
    return "\n".join(lines)


def _question_case(
    payload: dict[str, Any],
    *,
    report_path: Path,
    fallback_id: str,
    expected_mode: str,
) -> AcceptanceQuestionCase:
    decision = str(payload.get("decision") or "")
    reason_code = str(payload.get("reason_code") or "")
    answer_status = str(payload.get("answer_status") or "") or None
    citations = _string_list(payload.get("citations"))
    invalid_citations = _string_list(payload.get("invalid_citations"))
    notes = [
        f"source_id={payload.get('source_id') or ''}",
        f"provider_base_url={payload.get('provider_base_url') or ''}",
    ]
    if decision == "blocked" or reason_code in {"local_provider_unreachable", "retrieve_http_error", "answer_http_error"}:
        status = "blocked"
        follow_up_area = "provider_availability"
    elif invalid_citations:
        status = "review"
        follow_up_area = "citation_evidence"
    elif expected_mode == "answerable":
        if decision == "go" and answer_status == "answered" and citations:
            status = "ready"
            follow_up_area = "no_follow_up_required"
        else:
            status = "review"
            follow_up_area = "retrieval_quality"
    elif expected_mode == "insufficient_evidence":
        if decision == "go" and answer_status == "insufficient_evidence" and not citations:
            status = "ready"
            follow_up_area = "no_follow_up_required"
        else:
            status = "review"
            follow_up_area = "citation_evidence"
    else:
        status = "review"
        follow_up_area = "operator_flow"
    return AcceptanceQuestionCase(
        id=str(payload.get("case_id") or payload.get("id") or fallback_id),
        question=str(payload.get("question") or ""),
        expected_mode=expected_mode,
        report_path=report_path,
        decision=decision,
        reason_code=reason_code or "question_report_unknown",
        answer_status=answer_status,
        status=status,
        follow_up_area=follow_up_area,
        citations=citations,
        invalid_citations=invalid_citations,
        notes=notes,
    )


def _upload_summary(payload: dict[str, Any], path: Path) -> dict[str, Any]:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    return {
        "status": "supplied",
        "path": str(path),
        "decision": payload.get("decision"),
        "reason_code": payload.get("reason_code"),
        "source_id": payload.get("source_id") or summary.get("source_id"),
        "document_path": payload.get("document_path") or summary.get("document_path"),
        "parser_artifact_path": payload.get("parser_artifact_path"),
        "provider_ingestion_status": summary.get("provider_ingestion_status"),
    }


def _load_json(path: Path) -> tuple[dict[str, Any], str | None]:
    if not path.exists():
        return {}, f"missing_report:{path}"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, f"invalid_report:{path}:{exc}"
    if not isinstance(payload, dict):
        return {}, f"invalid_report_shape:{path}"
    return payload, None


def _expected_mode(path: Path, expected_modes: dict[str, str] | None) -> str:
    if not expected_modes:
        return "answerable"
    return (
        expected_modes.get(str(path))
        or expected_modes.get(path.name)
        or expected_modes.get(path.stem)
        or "answerable"
    )


def _follow_up_area(
    decision: str,
    upload_summary: dict[str, Any],
    question_cases: list[AcceptanceQuestionCase],
    blockers: list[str],
    warnings: list[str],
) -> str:
    if decision == "go":
        return "no_follow_up_required"
    if any("missing_report" in blocker or "invalid_report" in blocker for blocker in blockers):
        return "operator_flow"
    if upload_summary.get("decision") == "blocked":
        return "operator_flow"
    if any(case.follow_up_area == "provider_availability" for case in question_cases):
        return "provider_availability"
    if any(case.follow_up_area == "citation_evidence" for case in question_cases):
        return "citation_evidence"
    if any(case.follow_up_area == "retrieval_quality" for case in question_cases):
        return "retrieval_quality"
    if upload_summary.get("decision") == "review" or warnings:
        return "parser_ocr"
    return "operator_flow"


def _recommended_actions(decision: str, follow_up_area: str) -> list[str]:
    if decision == "go":
        return ["continue_with_more_real_business_documents_or_questions"]
    actions = {
        "operator_flow": ["rerun_upload_to_use_and_question_trials_with_existing_settings_entrypoint"],
        "parser_ocr": ["review_document_parser_output_and_try_smaller_or_layout_parse_slice"],
        "citation_evidence": ["inspect_citation_allowlist_and_provider_evidence_pack_behavior"],
        "retrieval_quality": ["collect_failed_questions_before_opening_retrieval_quality_tuning_change"],
        "provider_availability": ["start_or_repair_unified_knowledge_provider_then_rerun_question_trials"],
    }
    return actions.get(follow_up_area, ["review_acceptance_report_and_choose_next_small_slice"])


def _non_goals() -> list[str]:
    return [
        "does_not_enable_default_chat_retrieval_injection",
        "does_not_create_source_to_agent_binding",
        "does_not_mutate_domain_agent_manifests",
        "does_not_start_external_services",
        "does_not_add_graphrag_vector_backend_hybrid_or_rerank_promotion",
        "does_not_write_memory_audit_approval_trace_or_governance_records",
    ]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _first_non_empty(*values: Any) -> Any:
    for value in values:
        if value:
            return value
    return None
