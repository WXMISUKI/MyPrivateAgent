"""CLI startup diagnostics for local demo stability."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def _bootstrap_path() -> None:
    root = Path(__file__).resolve().parents[2]
    candidate = str(root)
    if candidate not in sys.path:
        sys.path.insert(0, candidate)


_bootstrap_path()

try:
    from database import SessionLocal
    from services.company_profile_explicit_api_local_smoke_service import (
        DEFAULT_AGENT_ID as DEFAULT_KNOWLEDGE_AGENT_ID,
        DEFAULT_DOMAIN as DEFAULT_KNOWLEDGE_DOMAIN,
        DEFAULT_QUERY as DEFAULT_KNOWLEDGE_QUERY,
        run_company_profile_explicit_api_local_smoke,
    )
    from services.capability_gap_service import get_capability_gap_service
    from services.framework_adapter_diagnostics_service import FrameworkAdapterDiagnosticsService
    from services.remediation_status_service import get_remediation_status_service
    from services.startup_diagnostics_service import get_startup_diagnostics_service
    from services.domain_agent_live_grounded_answer_trial_service import DEFAULT_PROVIDER_BASE_URL
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.database import SessionLocal
    from backend.services.company_profile_explicit_api_local_smoke_service import (
        DEFAULT_AGENT_ID as DEFAULT_KNOWLEDGE_AGENT_ID,
        DEFAULT_DOMAIN as DEFAULT_KNOWLEDGE_DOMAIN,
        DEFAULT_QUERY as DEFAULT_KNOWLEDGE_QUERY,
        run_company_profile_explicit_api_local_smoke,
    )
    from backend.services.capability_gap_service import get_capability_gap_service
    from backend.services.framework_adapter_diagnostics_service import FrameworkAdapterDiagnosticsService
    from backend.services.remediation_status_service import get_remediation_status_service
    from backend.services.startup_diagnostics_service import get_startup_diagnostics_service
    from backend.services.domain_agent_live_grounded_answer_trial_service import DEFAULT_PROVIDER_BASE_URL

ACTION_OWNERSHIP_MAP: Dict[str, Dict[str, Any]] = {
    "fix_final_synthesis_chain": {
        "owner": "agent-core",
        "module": "completion_synthesis",
        "files": [
            "backend/harness/agent_harness.py",
            "backend/services/chat_service.py",
            "backend/services/completion_evaluator_service.py",
        ],
    },
    "fix_retry_convergence_chain": {
        "owner": "agent-core",
        "module": "retry_convergence",
        "files": [
            "backend/harness/agent_harness.py",
            "backend/services/completion_evaluator_service.py",
        ],
    },
    "fix_capability_boundary_fallback": {
        "owner": "agent-governance",
        "module": "boundary_feedback",
        "files": [
            "backend/harness/agent_harness.py",
            "backend/services/capability_gap_service.py",
        ],
    },
    "fix_hook_trace_mapping": {
        "owner": "runtime-governance",
        "module": "hook_trace",
        "files": [
            "backend/services/agent_hook_service.py",
            "backend/services/run_trace_service.py",
        ],
    },
    "fix_subagent_trace_mapping": {
        "owner": "runtime-governance",
        "module": "subagent_trace",
        "files": [
            "backend/services/subagent_service.py",
            "backend/services/run_trace_service.py",
        ],
    },
    "fix_tool_error_classification": {
        "owner": "tooling",
        "module": "tool_error_taxonomy",
        "files": [
            "backend/harness/agent_harness.py",
            "backend/services/capability_gap_service.py",
        ],
    },
    "fix_fallback_payload_missing_parts": {
        "owner": "agent-governance",
        "module": "fallback_payload",
        "files": [
            "backend/harness/agent_harness.py",
            "backend/services/capability_gap_service.py",
        ],
    },
    "reduce_tool_call_budget": {
        "owner": "planning",
        "module": "tool_budget_policy",
        "files": [
            "backend/services/completion_evaluator_service.py",
            "backend/services/capability_gap_service.py",
        ],
    },
    "expand_profile_benchmark_samples": {
        "owner": "qa-governance",
        "module": "benchmark_dataset",
        "files": [
            "backend/config/benchmark_cases.json",
            "tests/agent_framework/test_capability_gap_service.py",
        ],
    },
    "fix_runtime_event_trace_mapping": {
        "owner": "runtime-governance",
        "module": "event_mapping",
        "files": [
            "backend/services/run_trace_service.py",
            "backend/harness/agent_harness.py",
        ],
    },
}


def _collect_latest_framework_adapter_external_error_summary() -> Dict[str, Any] | None:
    return FrameworkAdapterDiagnosticsService(
        session_factory=SessionLocal,
    ).collect_latest_external_error_summary()


def _collect_framework_adapter_external_error_counts() -> Dict[str, Any] | None:
    return FrameworkAdapterDiagnosticsService(
        session_factory=SessionLocal,
    ).collect_external_error_counts()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Doctor diagnostics for startup and capability-gap governance.",
    )
    parser.add_argument(
        "--knowledge-runtime",
        action="store_true",
        help="Output local knowledge runtime doctor report instead of startup diagnostics.",
    )
    parser.add_argument(
        "--capability-gaps",
        action="store_true",
        help="Output capability-gap governance summary instead of startup diagnostics.",
    )
    parser.add_argument(
        "--provider-base-url",
        default=DEFAULT_PROVIDER_BASE_URL,
        help="External knowledge provider base URL for --knowledge-runtime.",
    )
    parser.add_argument(
        "--provider-api-key",
        default=None,
        help="Optional provider API key for --knowledge-runtime. It is never written to output.",
    )
    parser.add_argument(
        "--agent-id",
        default=DEFAULT_KNOWLEDGE_AGENT_ID,
        help="Domain agent id for --knowledge-runtime.",
    )
    parser.add_argument(
        "--domain",
        default=DEFAULT_KNOWLEDGE_DOMAIN,
        help="Domain value for --knowledge-runtime.",
    )
    parser.add_argument(
        "--query",
        default=DEFAULT_KNOWLEDGE_QUERY,
        help="Query for --knowledge-runtime.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Top-k retrieve size for --knowledge-runtime.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=5,
        help="Provider timeout seconds for --knowledge-runtime.",
    )
    parser.add_argument(
        "--window-days",
        type=int,
        choices=[0, 7, 14, 30],
        default=0,
        help="Capability-gap window days (0/7/14/30).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Max plan items to inspect for capability-gap summary.",
    )
    parser.add_argument(
        "--max-open-actions",
        type=int,
        default=None,
        help="Fail governance gate when non-closed remediation actions exceed this value.",
    )
    parser.add_argument(
        "--max-long-blocked-actions",
        type=int,
        default=None,
        help="Fail governance gate when long-blocked remediation actions exceed this value.",
    )
    return parser


def _build_knowledge_runtime_report(
    *,
    provider_base_url: str = DEFAULT_PROVIDER_BASE_URL,
    provider_api_key: str | None = None,
    agent_id: str = DEFAULT_KNOWLEDGE_AGENT_ID,
    domain: str | None = DEFAULT_KNOWLEDGE_DOMAIN,
    query: str = DEFAULT_KNOWLEDGE_QUERY,
    top_k: int = 3,
    timeout_seconds: float = 5,
) -> Dict[str, Any]:
    try:
        smoke = run_company_profile_explicit_api_local_smoke(
            provider_base_url=provider_base_url,
            provider_api_key=provider_api_key,
            agent_id=agent_id,
            domain=domain,
            query=query,
            top_k=top_k,
            timeout_seconds=timeout_seconds,
        )
        smoke_payload = smoke.to_dict()
    except Exception as exc:  # pragma: no cover - defensive local diagnostics guard
        return _redact_secret(
            {
            "scope": "knowledge_runtime",
            "status": "fail",
            "decision": "blocked",
            "reason_code": "knowledge_runtime_doctor_failed",
            "exit_code": 1,
            "provider_base_url": provider_base_url,
            "agent_id": agent_id,
            "domain": domain,
            "query": query,
            "checks": [
                {
                    "name": "company_profile_explicit_api_local_smoke",
                    "status": "fail",
                    "reason_code": "knowledge_runtime_doctor_failed",
                }
            ],
            "blockers": [
                {
                    "component": "doctor",
                    "status": "blocked",
                    "reason_code": "knowledge_runtime_doctor_failed",
                    "message": str(exc),
                }
            ],
            "warnings": [],
            "recommended_next_action": "run_focused_doctor_tests_before_local_business_use",
            "boundary": _knowledge_runtime_boundary({}),
            "smoke": {},
            },
            provider_api_key,
        )

    decision = str(smoke_payload.get("decision") or "blocked").strip() or "blocked"
    status = _knowledge_runtime_status(decision)
    reason_code = str(smoke_payload.get("reason_code") or "").strip() or "knowledge_runtime_unknown"
    blockers = list(smoke_payload.get("blockers") or [])
    warnings = list(smoke_payload.get("warnings") or [])
    boundary = _knowledge_runtime_boundary(smoke_payload.get("boundary") or {})
    check_status = "ok" if decision == "go" else ("warn" if decision == "review" else "fail")
    return _redact_secret(
        {
        "scope": "knowledge_runtime",
        "status": status,
        "decision": decision,
        "reason_code": reason_code,
        "exit_code": _knowledge_runtime_exit_code(decision),
        "provider_base_url": str(smoke_payload.get("provider_base_url") or provider_base_url),
        "agent_id": str(smoke_payload.get("agent_id") or agent_id),
        "domain": smoke_payload.get("domain") if smoke_payload.get("domain") is not None else domain,
        "query": str(smoke_payload.get("query") or query),
        "endpoint": str(smoke_payload.get("endpoint") or ""),
        "checks": [
            {
                "name": "company_profile_explicit_api_local_smoke",
                "status": check_status,
                "decision": decision,
                "reason_code": reason_code,
                "http_status_code": smoke_payload.get("http_status_code"),
                "ok": bool(smoke_payload.get("ok")),
                "document_count": int(smoke_payload.get("document_count") or 0),
                "citation_count": len(smoke_payload.get("citations") or []),
            }
        ],
        "blockers": blockers,
        "warnings": warnings,
        "recommended_next_action": _knowledge_runtime_next_action(reason_code, decision),
        "boundary": boundary,
        "smoke": {
            "contract_version": smoke_payload.get("contract_version"),
            "decision": decision,
            "reason_code": reason_code,
            "answer_preview": smoke_payload.get("answer_preview"),
            "citations": list(smoke_payload.get("citations") or []),
            "document_count": int(smoke_payload.get("document_count") or 0),
            "api_status": smoke_payload.get("api_status"),
        },
        },
        provider_api_key,
    )


def _knowledge_runtime_status(decision: str) -> str:
    if decision == "go":
        return "ok"
    if decision == "review":
        return "warn"
    return "fail"


def _knowledge_runtime_exit_code(decision: str) -> int:
    if decision == "go":
        return 0
    if decision == "review":
        return 2
    return 1


def _knowledge_runtime_next_action(reason_code: str, decision: str) -> str:
    if decision == "go":
        return "local_knowledge_runtime_ready_for_explicit_business_trials"
    if reason_code in {"provider_unreachable", "live_provider_retrieve_failed", "explicit_api_route_failed"}:
        return "start_unifiedKnowledgeRAG_provider_and_rerun_doctor"
    if reason_code in {"explicit_api_boundary_missing", "provider_api_key_leaked"}:
        return "fix_myprivateagent_explicit_api_boundary_before_business_use"
    if "citation" in reason_code or "evidence" in reason_code or "source" in reason_code:
        return "rerun_provider_corpus_trial_and_verify_company_profile_2025_trial"
    if decision == "review":
        return "review_knowledge_runtime_warnings_before_business_use"
    return "fix_provider_or_explicit_api_before_business_use"


def _knowledge_runtime_boundary(smoke_boundary: Dict[str, Any]) -> Dict[str, Any]:
    boundary = dict(smoke_boundary or {})
    boundary.setdefault("default_chat_retrieval_injection", "disabled")
    boundary.setdefault("chat_invocation", "not_performed")
    boundary.setdefault("provider_startup", "not_performed")
    boundary.setdefault("source_binding", "not_performed")
    boundary.setdefault("memory_write", "not_performed")
    boundary.setdefault("audit_write", "not_performed")
    boundary.setdefault("trace_write", "not_performed")
    boundary.setdefault("tool_execution", "not_performed")
    boundary.setdefault("provider_data_mutation", "not_performed")
    boundary.setdefault("ocr_execution", "not_performed")
    boundary.setdefault("graphrag_execution", "not_promoted")
    boundary.setdefault("llm_answer_generation", "not_performed")
    return boundary


def _redact_secret(value: Any, secret: str | None) -> Any:
    if not secret:
        return value
    if isinstance(value, str):
        return value.replace(secret, "[REDACTED]")
    if isinstance(value, list):
        return [_redact_secret(item, secret) for item in value]
    if isinstance(value, dict):
        return {key: _redact_secret(item, secret) for key, item in value.items()}
    return value


def _build_capability_gap_report(
    *,
    limit: int,
    window_days: int,
    max_open_actions: int | None,
    max_long_blocked_actions: int | None,
) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        summary = get_capability_gap_service(db).get_summary(
            limit=max(1, int(limit)),
            window_days=window_days,
        )
        remediation_status_map = get_remediation_status_service(db).status_map()
    finally:
        db.close()

    benchmark = summary.get("benchmark_health") or {}
    remediation_progress = summary.get("remediation_progress") or {}
    unmatched = benchmark.get("benchmark_catalog_unmatched") or []
    action_playbook = benchmark.get("action_playbook") or {}
    pending_actions: List[Dict[str, Any]] = []
    for item in unmatched:
        if not isinstance(item, dict):
            continue
        action_id = str(item.get("remediation_action_id") or "").strip()
        if not action_id:
            continue
        ownership = ACTION_OWNERSHIP_MAP.get(action_id) or {}
        playbook = action_playbook.get(action_id) or {}
        pending_actions.append(
            {
                "case_id": str(item.get("id") or "").strip(),
                "action_id": action_id,
                "reason": str(item.get("reason") or "").strip(),
                "owner": str(ownership.get("owner") or "").strip(),
                "module": str(ownership.get("module") or "").strip(),
                "playbook_title": str(playbook.get("title") or "").strip(),
                "files": list(ownership.get("files") or []),
            }
        )
    remediation_targets: Dict[str, Dict[str, Any]] = {}
    for action in pending_actions:
        action_id = str(action.get("action_id") or "").strip()
        if not action_id or action_id in remediation_targets:
            continue
        status_detail = remediation_status_map.get(action_id) or {}
        remediation_targets[action_id] = {
            "action_id": action_id,
            "owner": str(action.get("owner") or "").strip(),
            "module": str(action.get("module") or "").strip(),
            "playbook_title": str(action.get("playbook_title") or "").strip(),
            "files": list(action.get("files") or []),
            "status": str(status_detail.get("status") or "open"),
            "status_detail": status_detail or None,
        }
    status_counts: Dict[str, int] = {"open": 0, "in_progress": 0, "blocked": 0, "done": 0, "verified": 0}
    for item in remediation_targets.values():
        status = str(item.get("status") or "open").strip()
        if status not in status_counts:
            status_counts[status] = 0
        status_counts[status] += 1
    non_closed_count = (
        int(status_counts.get("open", 0))
        + int(status_counts.get("in_progress", 0))
        + int(status_counts.get("blocked", 0))
    )
    threshold_breached = (
        max_open_actions is not None
        and max_open_actions >= 0
        and non_closed_count > max_open_actions
    )
    long_blocked_count = int(remediation_progress.get("long_blocked_count") or 0)
    long_blocked_threshold_breached = (
        max_long_blocked_actions is not None
        and max_long_blocked_actions >= 0
        and long_blocked_count > max_long_blocked_actions
    )
    governance_gate_passed = (
        bool(benchmark.get("gate_passed"))
        and not threshold_breached
        and not long_blocked_threshold_breached
    )
    escalation_recommendations: List[Dict[str, Any]] = []
    if threshold_breached:
        escalation_recommendations.append(
            {
                "type": "open_action_overflow",
                "severity": "high",
                "message": "未闭环整改动作超过阈值，建议冻结新增治理项并优先收敛 open/in_progress/blocked 动作。",
                "next_steps": [
                    "按 owner 分派未闭环动作并设置截止时间。",
                    "优先关闭 fix_final_synthesis_chain / fix_retry_convergence_chain 等核心链路动作。",
                ],
            }
        )
    if long_blocked_threshold_breached:
        long_blocked_items = remediation_progress.get("long_blocked") or []
        blocked_actions = [str(item.get("action_id") or "").strip() for item in long_blocked_items if isinstance(item, dict)]
        escalation_recommendations.append(
            {
                "type": "long_blocked_overflow",
                "severity": "high",
                "message": "长期阻塞整改动作超过阈值，建议立即升级处理。",
                "blocked_actions": [item for item in blocked_actions if item],
                "next_steps": [
                    "为长期阻塞动作指定明确 owner 与替补 owner。",
                    "将阻塞动作拆分为可交付子动作，降低单动作复杂度。",
                    "若依赖外部能力（工具/MCP）缺失，先落保守降级路径并补能力计划。",
                ],
            }
        )
    if not bool(benchmark.get("gate_passed")):
        missing_profiles = benchmark.get("missing_profiles") or []
        if missing_profiles:
            escalation_recommendations.append(
                {
                    "type": "benchmark_profile_gap",
                    "severity": "medium",
                    "message": "基准覆盖未达标，存在缺失 profile。",
                    "missing_profiles": missing_profiles,
                    "next_steps": [
                        "补充 benchmark_cases 对应 profile 的样本。",
                        "为缺失 profile 增加最小可复现实例与断言。",
                    ],
                }
            )

    return {
        "status": "ok" if governance_gate_passed else "warn",
        "scope": "capability_gap",
        "window_days": window_days,
        "limit": max(1, int(limit)),
        "gate_passed": governance_gate_passed,
        "benchmark_gate_passed": bool(benchmark.get("gate_passed")),
        "score": benchmark.get("score"),
        "threshold_score": benchmark.get("threshold_score"),
        "catalog_coverage_ratio": benchmark.get("benchmark_catalog_coverage_ratio"),
        "catalog_coverage_threshold": benchmark.get("benchmark_catalog_coverage_threshold"),
        "missing_profiles": benchmark.get("missing_profiles") or [],
        "pending_actions": pending_actions,
        "remediation_targets": list(remediation_targets.values()),
        "remediation_status_counts": status_counts,
        "non_closed_action_count": non_closed_count,
        "max_open_actions": max_open_actions,
        "open_action_gate_breached": threshold_breached,
        "long_blocked_action_count": long_blocked_count,
        "max_long_blocked_actions": max_long_blocked_actions,
        "long_blocked_action_gate_breached": long_blocked_threshold_breached,
        "escalation_recommendations": escalation_recommendations,
    }


def main(argv: List[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.knowledge_runtime:
        report = _build_knowledge_runtime_report(
            provider_base_url=args.provider_base_url,
            provider_api_key=args.provider_api_key,
            agent_id=args.agent_id,
            domain=args.domain,
            query=args.query,
            top_k=args.top_k,
            timeout_seconds=args.timeout_seconds,
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return int(report.get("exit_code", 1))

    if args.capability_gaps:
        report = _build_capability_gap_report(
            limit=args.limit,
            window_days=args.window_days,
            max_open_actions=args.max_open_actions,
            max_long_blocked_actions=args.max_long_blocked_actions,
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report.get("gate_passed") else 2

    report = get_startup_diagnostics_service().collect_report()
    framework_adapter_check = (report.get("checks") or {}).get("framework_adapters")
    if isinstance(framework_adapter_check, dict):
        latest_external_error = _collect_latest_framework_adapter_external_error_summary()
        if latest_external_error:
            framework_adapter_check["latest_external_pilot_failure"] = latest_external_error
        external_error_counts = _collect_framework_adapter_external_error_counts()
        if external_error_counts:
            framework_adapter_check["external_pilot_failure_counts"] = external_error_counts
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("status") != "fail" else 1


if __name__ == "__main__":
    raise SystemExit(main())
