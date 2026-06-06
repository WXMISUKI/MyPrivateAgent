"""Run a side-effect-free domain-agent integration trial pack from JSON input."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services.domain_agent_grounded_answer_composition_trial_service import (  # noqa: E402
    DomainAgentGroundedAnswerCompositionTrialService,
)
from backend.services.domain_agent_grounded_answer_package_service import (  # noqa: E402
    DomainAgentGroundedAnswerPackageService,
)
from backend.services.domain_agent_grounded_answer_trial_service import (  # noqa: E402
    DomainAgentGroundedAnswerTrialService,
)


CONTRACT_VERSION = "domain-agent-minimal-integration-trial-pack-v1"
DEFAULT_PAYLOAD_PATH = ROOT / "docs" / "examples" / "domain_agent_trial_payload.json"


def load_payload(path: str | Path) -> dict[str, Any]:
    payload_path = Path(path)
    if not payload_path.is_absolute():
        payload_path = ROOT / payload_path
    data = json.loads(payload_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Trial payload must be a JSON object")
    return data


def build_trial_pack(payload: Mapping[str, Any]) -> dict[str, Any]:
    agent_id = _clean(payload.get("agent_id")) or None
    domain = _clean(payload.get("domain")) or None
    query = _clean(payload.get("query")) or None
    graph_requested = bool(payload.get("graph_requested", False))
    evidence_pack = _mapping(payload.get("evidence_pack"))
    provider_evidence = _mapping(payload.get("provider_evidence"))
    promptops_evidence = _mapping(payload.get("promptops_evidence"))
    memoryops_evidence = _mapping(payload.get("memoryops_evidence"))
    eval_evidence = _mapping(payload.get("eval_evidence"))

    trial_service = DomainAgentGroundedAnswerTrialService()
    package_service = DomainAgentGroundedAnswerPackageService(trial_service=trial_service)
    composition_service = DomainAgentGroundedAnswerCompositionTrialService(package_service=package_service)

    trial = trial_service.run_trial(
        agent_id=agent_id,
        domain=domain,
        query=query,
        evidence_pack=evidence_pack,
        provider_evidence=provider_evidence,
        promptops_evidence=promptops_evidence,
        memoryops_evidence=memoryops_evidence,
        eval_evidence=eval_evidence,
        graph_requested=graph_requested,
    ).to_dict()
    package = package_service.build_package(
        agent_id=agent_id,
        domain=domain,
        query=query,
        trial_report=trial,
    ).to_dict()
    composition = composition_service.run_trial(
        agent_id=agent_id,
        package=package,
    ).to_dict()

    overall_status = _overall_status(trial, package, composition)
    return {
        "contract_version": CONTRACT_VERSION,
        "overall_status": overall_status,
        "recommended_next_action": _recommended_next_action(overall_status),
        "agent_id": agent_id,
        "domain": domain,
        "query": query,
        "stage_statuses": {
            "trial": trial.get("trial_status"),
            "package": package.get("package_status"),
            "composition": composition.get("composition_status"),
        },
        "citation_allowlist": list(trial.get("citation_allowlist") or []),
        "preview_available": bool(composition.get("answer_preview")),
        "answer_preview": composition.get("answer_preview"),
        "blockers": _issues(trial.get("blockers")) + _issues(package.get("blockers")) + _issues(composition.get("blockers")),
        "warnings": _issues(trial.get("warnings")) + _issues(package.get("warnings")) + _issues(composition.get("warnings")),
        "stages": {
            "trial": _stage_summary(
                trial,
                status_key="trial_status",
                extra={
                    "recommended_next_action": trial.get("recommended_next_action"),
                    "citation_allowlist": list(trial.get("citation_allowlist") or []),
                },
            ),
            "package": _stage_summary(
                package,
                status_key="package_status",
                extra={
                    "allowed_citations": list(package.get("allowed_citations") or []),
                    "prompt_binding": package.get("prompt_binding") or {},
                    "memory_boundary": package.get("memory_boundary") or {},
                },
            ),
            "composition": _stage_summary(
                composition,
                status_key="composition_status",
                extra={
                    "preview_available": bool(composition.get("answer_preview")),
                    "used_citations": list(composition.get("used_citations") or []),
                },
            ),
        },
        "boundary": {
            "provider_invocation": "not_performed",
            "model_invocation": "not_performed",
            "tool_invocation": "not_performed",
            "mcp_invocation": "not_performed",
            "chat_invocation": "not_performed",
            "default_chat_retrieval_injection": "disabled",
            "source_binding_creation": "not_performed",
            "memory_write": "not_performed",
            "audit_write": "not_performed",
            "trace_write": "not_performed",
            "prompt_rollout": "not_performed",
            "runtime_behavior_changed": False,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a domain-agent minimal integration trial pack.")
    parser.add_argument(
        "--payload",
        default=str(DEFAULT_PAYLOAD_PATH),
        help="Path to the JSON trial payload. Defaults to docs/examples/domain_agent_trial_payload.json.",
    )
    parser.add_argument("--pretty", action="store_true", help="Print indented JSON.")
    args = parser.parse_args(argv)

    try:
        report = build_trial_pack(load_payload(args.payload))
    except Exception as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1

    print(json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None))
    return 2 if report["overall_status"] == "blocked" else 0


def _overall_status(*reports: Mapping[str, Any]) -> str:
    statuses = {
        _clean(report.get("trial_status") or report.get("package_status") or report.get("composition_status")).lower()
        for report in reports
    }
    if "blocked" in statuses:
        return "blocked"
    if "review" in statuses:
        return "review"
    return "go"


def _recommended_next_action(status: str) -> str:
    if status == "go":
        return "start_caller_repo_side_grounded_answer_trial"
    if status == "review":
        return "review_trial_pack_warnings_before_repo_side_trial"
    return "resolve_trial_pack_blockers_before_repo_side_trial"


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _issues(value: Any) -> list[dict[str, Any]]:
    return [dict(item) for item in value or [] if isinstance(item, Mapping)]


def _stage_summary(
    report: Mapping[str, Any],
    *,
    status_key: str,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    summary = {
        "contract_version": report.get("contract_version"),
        "status": report.get(status_key),
        "reason_code": report.get("reason_code"),
        "blockers": _issues(report.get("blockers")),
        "warnings": _issues(report.get("warnings")),
        "boundary": report.get("boundary") if isinstance(report.get("boundary"), Mapping) else {},
    }
    summary.update(dict(extra or {}))
    return summary


def _clean(value: Any) -> str:
    return str(value or "").strip()


if __name__ == "__main__":
    raise SystemExit(main())
