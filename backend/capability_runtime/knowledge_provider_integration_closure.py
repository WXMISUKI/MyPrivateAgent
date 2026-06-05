"""Phase 20 closure decision for unified knowledge provider integration."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


CLOSURE_DECISION_ID = "phase20-unified-knowledge-provider-integration-closure-v1"
DEFAULT_TRIAL_OUTCOME_PATH = Path(
    "docs/integration/unified-knowledge-provider-trial/unified-knowledge-provider-trial-outcome.json"
)
DEFAULT_OUTPUT_DIR = Path("docs/integration/unified-knowledge-provider-trial")
OUTPUT_JSON_FILENAME = "phase20-integration-closure-decision.json"
OUTPUT_MARKDOWN_FILENAME = "phase20-integration-closure-decision.md"
REQUIRED_TRIAL_CHECK_IDS = (
    "provider_health",
    "provider_manifest",
    "provider_preflight",
    "source_bindings",
    "rag_retrieve",
)


@dataclass(frozen=True)
class IntegrationClosureAction:
    id: str
    owner: str
    status: str
    summary: str


@dataclass(frozen=True)
class KnowledgeProviderIntegrationClosure:
    id: str
    generated_at: str
    decision: str
    evidence_chain_status: str
    recommended_next_line: str
    trial_outcome_path: Path
    trial_status: str | None
    trial_decision: str | None
    provider_base_url: str | None
    summary: dict[str, Any]
    required_checks: list[dict[str, Any]]
    boundary: dict[str, Any]
    actions: list[IntegrationClosureAction]
    notes: list[str] = field(default_factory=list)
    json_path: Path | None = None
    markdown_path: Path | None = None


def build_knowledge_provider_integration_closure(
    *,
    trial_outcome_path: Path = DEFAULT_TRIAL_OUTCOME_PATH,
) -> KnowledgeProviderIntegrationClosure:
    payload, load_error = _load_trial_outcome(trial_outcome_path)
    if load_error is not None:
        return _blocked_closure(trial_outcome_path, load_error)

    trial_status = _string_or_none(payload.get("status"))
    trial_decision = _string_or_none(payload.get("decision"))
    provider_base_url = _string_or_none(payload.get("provider_base_url"))
    checks = payload.get("checks") if isinstance(payload.get("checks"), list) else []
    check_by_id = {check.get("id"): check for check in checks if isinstance(check, dict)}
    required_checks = [_closure_check(check_by_id.get(check_id), check_id) for check_id in REQUIRED_TRIAL_CHECK_IDS]
    blocked_checks = [check for check in required_checks if check["status"] == "blocked"]
    review_checks = [check for check in required_checks if check["status"] == "review"]
    missing_checks = [check for check in required_checks if check["status"] == "missing"]
    boundary = _boundary(payload)

    if trial_status == "trial_blocked" or blocked_checks or missing_checks:
        decision = "blocked"
        evidence_chain_status = "blocked"
        recommended_next_line = "resolve_provider_trial_blockers_before_integration"
    elif (
        trial_status == "trial_passed"
        and trial_decision == "proceed_with_myprivateagent_integration_hardening"
        and not review_checks
        and boundary["runtime_promotion_status"] == "unchanged"
    ):
        decision = "go"
        evidence_chain_status = "closed"
        recommended_next_line = "continue_with_agent_grounding_policy_contract"
    else:
        decision = "review"
        evidence_chain_status = "closed_with_review"
        recommended_next_line = "review_trial_context_before_grounding_policy_or_integration_hardening"

    actions = _actions(decision)
    return KnowledgeProviderIntegrationClosure(
        id=CLOSURE_DECISION_ID,
        generated_at=datetime.now(UTC).isoformat(),
        decision=decision,
        evidence_chain_status=evidence_chain_status,
        recommended_next_line=recommended_next_line,
        trial_outcome_path=trial_outcome_path,
        trial_status=trial_status,
        trial_decision=trial_decision,
        provider_base_url=provider_base_url,
        summary={
            "required_check_count": len(REQUIRED_TRIAL_CHECK_IDS),
            "ready_required_check_count": len([check for check in required_checks if check["status"] == "ready"]),
            "review_required_check_count": len(review_checks),
            "blocked_required_check_count": len(blocked_checks),
            "missing_required_check_count": len(missing_checks),
            "source_binding_policy_owner": boundary["source_binding_policy_owner"],
            "runtime_promotion_status": boundary["runtime_promotion_status"],
            "default_chat_retrieval_injection": boundary["default_chat_retrieval_injection"],
            "graph_rag_promotion_status": boundary["graph_rag_promotion_status"],
            "plan_external_rag_graphrag_provider_status": "review_open",
        },
        required_checks=required_checks,
        boundary=boundary,
        actions=actions,
        notes=[
            "Phase 20 closes the readiness evidence chain for the minimal provider access path.",
            "The closure does not enable default chat retrieval injection.",
            "GraphRAG execution remains separately gated and is not promoted by RAG retrieve success.",
        ],
    )


def export_knowledge_provider_integration_closure(
    *,
    trial_outcome_path: Path = DEFAULT_TRIAL_OUTCOME_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> KnowledgeProviderIntegrationClosure:
    output_dir.mkdir(parents=True, exist_ok=True)
    closure = build_knowledge_provider_integration_closure(trial_outcome_path=trial_outcome_path)
    json_path = output_dir / OUTPUT_JSON_FILENAME
    markdown_path = output_dir / OUTPUT_MARKDOWN_FILENAME
    exported = KnowledgeProviderIntegrationClosure(
        id=closure.id,
        generated_at=closure.generated_at,
        decision=closure.decision,
        evidence_chain_status=closure.evidence_chain_status,
        recommended_next_line=closure.recommended_next_line,
        trial_outcome_path=closure.trial_outcome_path,
        trial_status=closure.trial_status,
        trial_decision=closure.trial_decision,
        provider_base_url=closure.provider_base_url,
        summary=closure.summary,
        required_checks=closure.required_checks,
        boundary=closure.boundary,
        actions=closure.actions,
        notes=closure.notes,
        json_path=json_path,
        markdown_path=markdown_path,
    )
    json_path.write_text(
        json.dumps(knowledge_provider_integration_closure_to_dict(exported), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_knowledge_provider_integration_closure_markdown(exported), encoding="utf-8")
    return exported


def knowledge_provider_integration_closure_to_dict(
    closure: KnowledgeProviderIntegrationClosure,
) -> dict[str, Any]:
    payload = asdict(closure)
    payload["trial_outcome_path"] = str(closure.trial_outcome_path)
    if closure.json_path is not None:
        payload["json_path"] = str(closure.json_path)
    if closure.markdown_path is not None:
        payload["markdown_path"] = str(closure.markdown_path)
    return payload


def render_knowledge_provider_integration_closure_markdown(
    closure: KnowledgeProviderIntegrationClosure,
) -> str:
    lines = [
        "# Phase 20 Unified Knowledge Provider Integration Closure",
        "",
        f"- Report: `{closure.id}`",
        f"- Decision: `{closure.decision}`",
        f"- Evidence Chain Status: `{closure.evidence_chain_status}`",
        f"- Recommended Next Line: `{closure.recommended_next_line}`",
        f"- Trial Status: `{closure.trial_status}`",
        f"- Trial Decision: `{closure.trial_decision}`",
        f"- Provider Base URL: `{closure.provider_base_url}`",
        f"- Generated At: `{closure.generated_at}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    for key, value in closure.summary.items():
        lines.append(f"| `{key}` | `{_format_value(value)}` |")
    lines.extend(["", "## Required Checks", "", "| Check | Status | Recommended Action |", "|---|---|---|"])
    for check in closure.required_checks:
        lines.append(f"| `{check['id']}` | `{check['status']}` | `{check['recommended_action']}` |")
    lines.extend(["", "## Boundary", "", "| Boundary | Value |", "|---|---|"])
    for key, value in closure.boundary.items():
        lines.append(f"| `{key}` | `{_format_value(value)}` |")
    lines.extend(["", "## Actions", "", "| Action | Owner | Status | Summary |", "|---|---|---|---|"])
    for action in closure.actions:
        lines.append(f"| `{action.id}` | `{action.owner}` | `{action.status}` | {action.summary} |")
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in closure.notes)
    lines.append("")
    return "\n".join(lines)


def _load_trial_outcome(path: Path) -> tuple[dict[str, Any], dict[str, str] | None]:
    if not path.exists():
        return {}, {"code": "TRIAL_OUTCOME_MISSING", "message": f"Missing trial outcome: {path}"}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        return {}, {"code": "TRIAL_OUTCOME_INVALID_JSON", "message": str(exc)}
    if not isinstance(payload, dict):
        return {}, {"code": "TRIAL_OUTCOME_INVALID_SHAPE", "message": "Trial outcome must be a JSON object."}
    return payload, None


def _blocked_closure(path: Path, error: dict[str, str]) -> KnowledgeProviderIntegrationClosure:
    return KnowledgeProviderIntegrationClosure(
        id=CLOSURE_DECISION_ID,
        generated_at=datetime.now(UTC).isoformat(),
        decision="blocked",
        evidence_chain_status="blocked",
        recommended_next_line="regenerate_phase19_trial_outcome_before_integration",
        trial_outcome_path=path,
        trial_status=None,
        trial_decision=None,
        provider_base_url=None,
        summary={
            "required_check_count": len(REQUIRED_TRIAL_CHECK_IDS),
            "ready_required_check_count": 0,
            "review_required_check_count": 0,
            "blocked_required_check_count": 1,
            "missing_required_check_count": len(REQUIRED_TRIAL_CHECK_IDS),
            "source_binding_policy_owner": "caller",
            "runtime_promotion_status": "unchanged",
            "default_chat_retrieval_injection": "disabled",
            "graph_rag_promotion_status": "not_promoted",
            "plan_external_rag_graphrag_provider_status": "review_open",
        },
        required_checks=[
            {
                "id": check_id,
                "status": "missing",
                "recommended_action": "regenerate_phase19_trial_outcome",
                "error": error,
            }
            for check_id in REQUIRED_TRIAL_CHECK_IDS
        ],
        boundary=_boundary({}),
        actions=_actions("blocked"),
        notes=["Phase 20 cannot close until Phase 19 trial outcome evidence is readable."],
    )


def _closure_check(check: dict[str, Any] | None, check_id: str) -> dict[str, Any]:
    if check is None:
        return {
            "id": check_id,
            "status": "missing",
            "recommended_action": "regenerate_phase19_trial_outcome",
            "summary": {},
            "error": {"code": "REQUIRED_CHECK_MISSING"},
        }
    status = str(check.get("status") or "missing")
    if status not in {"ready", "review", "blocked"}:
        status = "review"
    return {
        "id": check_id,
        "status": status,
        "recommended_action": check.get("recommended_action") or "review_required_check",
        "summary": check.get("summary") if isinstance(check.get("summary"), dict) else {},
        "error": check.get("error") if isinstance(check.get("error"), dict) else None,
    }


def _boundary(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    return {
        "source_binding_policy_owner": summary.get("source_binding_policy_owner") or "caller",
        "runtime_promotion_status": summary.get("runtime_promotion_status") or "unchanged",
        "default_chat_retrieval_injection": "disabled",
        "graph_rag_promotion_status": "not_promoted",
        "source_to_agent_binding_creation": "not_performed",
        "approval_or_audit_policy_change": "not_performed",
        "final_answer_composition_policy": "not_performed",
    }


def _actions(decision: str) -> list[IntegrationClosureAction]:
    if decision == "go":
        return [
            IntegrationClosureAction(
                id="close_readiness_evidence_chain",
                owner="MyPrivateAgent",
                status="ready",
                summary="Stop adding default readiness evidence phases for the minimal provider access path.",
            ),
            IntegrationClosureAction(
                id="continue_grounding_policy_contract",
                owner="MyPrivateAgent",
                status="next",
                summary="Use add-agent-grounding-policy-contract for default knowledge behavior control.",
            ),
            IntegrationClosureAction(
                id="keep_graphrag_separately_gated",
                owner="unifiedKnowledgeRAG",
                status="not_promoted",
                summary="Treat graph execution as a later provider-side gate, not a Phase 20 promotion.",
            ),
        ]
    if decision == "review":
        return [
            IntegrationClosureAction(
                id="review_trial_context",
                owner="MyPrivateAgent",
                status="review",
                summary="Review non-blocking trial context before integration hardening.",
            ),
            IntegrationClosureAction(
                id="avoid_more_readiness_evidence_by_default",
                owner="MyPrivateAgent",
                status="ready",
                summary="Do not open additional readiness phases unless a concrete blocker appears.",
            ),
        ]
    return [
        IntegrationClosureAction(
            id="resolve_trial_blockers",
            owner="MyPrivateAgent",
            status="blocked",
            summary="Fix missing or blocked Phase 19 required trial evidence before continuing.",
        )
    ]


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _format_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)
