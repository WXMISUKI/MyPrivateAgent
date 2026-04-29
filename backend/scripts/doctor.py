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
    from services.capability_gap_service import get_capability_gap_service
    from services.remediation_status_service import get_remediation_status_service
    from services.startup_diagnostics_service import get_startup_diagnostics_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.database import SessionLocal
    from backend.services.capability_gap_service import get_capability_gap_service
    from backend.services.remediation_status_service import get_remediation_status_service
    from backend.services.startup_diagnostics_service import get_startup_diagnostics_service

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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Doctor diagnostics for startup and capability-gap governance.",
    )
    parser.add_argument(
        "--capability-gaps",
        action="store_true",
        help="Output capability-gap governance summary instead of startup diagnostics.",
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
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("status") != "fail" else 1


if __name__ == "__main__":
    raise SystemExit(main())
