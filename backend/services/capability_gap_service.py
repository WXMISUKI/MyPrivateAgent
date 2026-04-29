"""Aggregate capability-gap signals from planner run traces."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
from typing import Any, Dict, Iterable, List, Optional

try:
    from models import PlanItemRecord
    from model_router import get_model_router
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.models import PlanItemRecord
    from backend.model_router import get_model_router


class CapabilityGapService:
    """Summarize recent capability-gap fallback signals for framework governance."""
    BENCHMARK_SCORE_THRESHOLD = 80.0
    BENCHMARK_CATALOG_COVERAGE_THRESHOLD = 0.6
    BENCHMARK_REQUIRED_PROFILES = ("travel_planning", "research_compare", "planning")
    REMEDIATION_PLAYBOOK: Dict[str, Dict[str, str]] = {
        "fix_final_synthesis_chain": {
            "title": "修复最终收尾链路",
            "description": "确保工具调用结束后进入 completion evaluator 并稳定产出 completion_finalized。",
        },
        "fix_retry_convergence_chain": {
            "title": "修复补查收敛链路",
            "description": "确保 completion_retry 之后必定收敛到 completion_finalized 或 capability_gap_fallback。",
        },
        "fix_capability_boundary_fallback": {
            "title": "修复能力边界收尾",
            "description": "能力不足时必须发出 capability_gap_fallback，并附带 missing_parts。",
        },
        "fix_hook_trace_mapping": {
            "title": "修复 Hook 治理映射",
            "description": "确保 pre_tool_use_blocked 等 hook 事件完整写入 run trace。",
        },
        "fix_subagent_trace_mapping": {
            "title": "修复 Subagent 轨迹映射",
            "description": "确保 child_completed/failed 等子执行事件回写并带角色信息。",
        },
        "fix_tool_error_classification": {
            "title": "修复工具错误分类",
            "description": "确保 tool_failed/mcp_tool_failed 事件带 error_category，供治理统计使用。",
        },
        "fix_fallback_payload_missing_parts": {
            "title": "修复缺口字段",
            "description": "保证 capability_gap_fallback payload 中 missing_parts 字段齐全。",
        },
        "reduce_tool_call_budget": {
            "title": "收紧工具预算",
            "description": "按 profile 限制工具调用次数，优先提高单次查询质量。",
        },
        "expand_profile_benchmark_samples": {
            "title": "补充基准样本覆盖",
            "description": "补充对应 profile 的真实执行样本，提升固定 benchmark 覆盖率。",
        },
        "fix_runtime_event_trace_mapping": {
            "title": "修复运行时事件映射",
            "description": "排查 runtime event 到 run trace 的映射遗漏。",
        },
    }
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

    def __init__(self, db):
        self.db = db
        self.model_router = get_model_router()

    def _build_provider_by_model(self) -> Dict[str, str]:
        mapping: Dict[str, str] = {}
        try:
            for item in self.model_router.list_available_models().values():
                model_name = str(item.get("name") or "").strip()
                provider = str(item.get("provider") or "").strip()
                if model_name and provider:
                    mapping[model_name] = provider
        except Exception:
            return {}
        return mapping

    def _load_benchmark_catalog(self) -> List[Dict[str, Any]]:
        default_cases: List[Dict[str, Any]] = [
            {
                "id": "default_travel_finalize",
                "profile": "travel_planning",
                "required_events": ["completion_finalized"],
            },
            {
                "id": "default_travel_boundary",
                "profile": "travel_planning",
                "required_events": ["capability_gap_fallback"],
            },
            {
                "id": "default_planning_finalize",
                "profile": "planning",
                "required_events": ["completion_finalized"],
            },
            {
                "id": "default_research_finalize",
                "profile": "research_compare",
                "required_events": ["completion_finalized"],
            },
        ]
        catalog_path = Path(__file__).resolve().parents[1] / "config" / "benchmark_cases.json"
        try:
            if not catalog_path.exists():
                return default_cases
            payload = json.loads(catalog_path.read_text(encoding="utf-8"))
            if not isinstance(payload, list):
                return default_cases
            normalized: List[Dict[str, Any]] = []
            for item in payload:
                if not isinstance(item, dict):
                    continue
                case_id = str(item.get("id") or "").strip()
                profile = str(item.get("profile") or "").strip()
                required_events = item.get("required_events") or []
                if not case_id or not profile or not isinstance(required_events, list):
                    continue
                item["scenario"] = str(item.get("scenario") or "general").strip() or "general"
                normalized.append(item)
            return normalized or default_cases
        except Exception:
            return default_cases

    def _normalize_day_bucket(self, timestamp: Any) -> str:
        text = str(timestamp or "").strip()
        if not text:
            return "unknown"
        if "T" in text:
            return text.split("T", 1)[0]
        if " " in text:
            return text.split(" ", 1)[0]
        if len(text) >= 10:
            return text[:10]
        return text

    def _parse_timestamp(self, timestamp: Any) -> Optional[datetime]:
        text = str(timestamp or "").strip()
        if not text:
            return None
        try:
            normalized = text.replace("Z", "+00:00")
            dt = datetime.fromisoformat(normalized)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            return None

    def get_summary(
        self,
        *,
        limit: int = 100,
        missing_part: Optional[str] = None,
        keyword: Optional[str] = None,
        profile: Optional[str] = None,
        completion_stage: Optional[str] = None,
        error_category: Optional[str] = None,
        hook_event_type: Optional[str] = None,
        subagent_role: Optional[str] = None,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        window_days: Optional[int] = None,
    ) -> Dict[str, Any]:
        items = (
            self.db.query(PlanItemRecord)
            .order_by(PlanItemRecord.updated_at.desc())
            .limit(max(1, int(limit)))
            .all()
        )

        normalized_missing_part = str(missing_part or "").strip().lower() or None
        normalized_keyword = str(keyword or "").strip().lower() or None
        normalized_profile = str(profile or "").strip() or None
        normalized_stage = str(completion_stage or "").strip() or None
        normalized_error_category = str(error_category or "").strip() or None
        normalized_hook_event_type = str(hook_event_type or "").strip() or None
        normalized_subagent_role = str(subagent_role or "").strip().lower() or None
        normalized_provider = str(provider or "").strip() or None
        normalized_model_name = str(model_name or "").strip() or None
        normalized_window_days = int(window_days or 0)
        if normalized_window_days not in {0, 7, 14, 30}:
            normalized_window_days = 0
        window_start_utc: Optional[datetime] = None
        if normalized_window_days > 0:
            window_start_utc = datetime.now(timezone.utc) - timedelta(days=normalized_window_days)
        provider_by_model = self._build_provider_by_model()
        gap_events: List[Dict[str, Any]] = []
        profile_counter: Counter[str] = Counter()
        stage_counter: Counter[str] = Counter()
        error_counter: Counter[str] = Counter()
        hook_event_counter: Counter[str] = Counter()
        subagent_role_counter: Counter[str] = Counter()
        provider_counter: Counter[str] = Counter()
        model_counter: Counter[str] = Counter()
        day_counter: Counter[str] = Counter()
        provider_model_counter: Counter[str] = Counter()
        profile_provider_model_counter: Counter[str] = Counter()
        current_window_counter: Counter[str] = Counter()
        previous_window_counter: Counter[str] = Counter()
        filtered_entries_by_item: Dict[int, List[Dict[str, Any]]] = {}
        now_utc = datetime.now(timezone.utc)
        previous_window_start_utc: Optional[datetime] = None
        if window_start_utc is not None:
            previous_window_start_utc = window_start_utc - timedelta(days=normalized_window_days)
        for item in items:
            metadata = dict(item.item_metadata or {})
            run_trace = metadata.get("run_trace") or []
            for entry in run_trace:
                if not isinstance(entry, dict):
                    continue
                event_type = str(entry.get("event_type") or "").strip()
                payload = entry.get("payload") or {}
                source = str(entry.get("source") or "").strip()
                entry_subagent_role = str(payload.get("agent_role") or "").strip().lower()
                entry_model_name = str(payload.get("model_name") or "").strip()
                entry_provider = str(payload.get("provider") or "").strip()
                entry_timestamp = entry.get("timestamp")
                if window_start_utc is not None:
                    entry_dt = self._parse_timestamp(entry_timestamp)
                    if entry_dt is None or entry_dt < window_start_utc:
                        continue
                if not entry_provider and entry_model_name:
                    entry_provider = provider_by_model.get(entry_model_name, "")

                if normalized_provider and normalized_provider != entry_provider:
                    continue
                if normalized_model_name and normalized_model_name != entry_model_name:
                    continue
                filtered_entries_by_item.setdefault(int(item.id), []).append(entry)

                if event_type == "capability_gap_fallback":
                    missing_parts = self._normalize_list(payload.get("missing_parts") or [])
                    event_profile = str(payload.get("profile") or payload.get("completion_check", {}).get("profile") or "").strip()
                    event_stage = str(payload.get("completion_stage") or payload.get("completion_check", {}).get("stage") or "").strip()
                    searchable_text = " ".join(
                        [
                            str(item.title or "").strip(),
                            str(entry.get("summary") or "").strip(),
                            str(entry.get("detail") or "").strip(),
                        ]
                    ).lower()
                    if normalized_missing_part and normalized_missing_part not in missing_parts:
                        continue
                    if normalized_keyword and normalized_keyword not in searchable_text:
                        continue
                    if normalized_profile and normalized_profile != event_profile:
                        continue
                    if normalized_stage and normalized_stage != event_stage:
                        continue
                    gap_events.append(
                        {
                            "plan_item_id": item.id,
                            "title": item.title,
                            "summary": str(entry.get("summary") or "").strip(),
                            "detail": str(entry.get("detail") or "").strip(),
                            "timestamp": entry.get("timestamp"),
                            "missing_parts": missing_parts,
                            "profile": event_profile,
                            "completion_stage": event_stage,
                            "provider": entry_provider,
                            "model_name": entry_model_name,
                        }
                    )
                    day_bucket = self._normalize_day_bucket(entry.get("timestamp"))
                    profile_counter.update([event_profile] if event_profile else [])
                    stage_counter.update([event_stage] if event_stage else [])
                    provider_counter.update([entry_provider] if entry_provider else [])
                    model_counter.update([entry_model_name] if entry_model_name else [])
                    day_counter.update([day_bucket] if day_bucket else [])
                    if entry_provider and entry_model_name:
                        provider_model_counter.update([f"{entry_provider}::{entry_model_name}"])
                    if event_profile and entry_provider and entry_model_name:
                        profile_provider_model_counter.update(
                            [f"{event_profile}::{entry_provider}::{entry_model_name}"]
                        )
                    if (
                        window_start_utc is not None
                        and previous_window_start_utc is not None
                        and entry_provider
                        and entry_model_name
                    ):
                        pair_key = f"{entry_provider}::{entry_model_name}"
                        if window_start_utc <= entry_dt <= now_utc:
                            current_window_counter.update([pair_key])
                        elif previous_window_start_utc <= entry_dt < window_start_utc:
                            previous_window_counter.update([pair_key])
                    continue

                if source == "hook":
                    if normalized_hook_event_type and normalized_hook_event_type != event_type:
                        continue
                    hook_event_counter.update([event_type] if event_type else [])
                    provider_counter.update([entry_provider] if entry_provider else [])
                    model_counter.update([entry_model_name] if entry_model_name else [])
                    continue

                if source == "subagent" and event_type in {"child_running", "child_completed", "child_failed"}:
                    if not entry_subagent_role:
                        continue
                    if normalized_subagent_role and normalized_subagent_role != entry_subagent_role:
                        continue
                    subagent_role_counter.update([entry_subagent_role])
                    provider_counter.update([entry_provider] if entry_provider else [])
                    model_counter.update([entry_model_name] if entry_model_name else [])
                    continue

                if event_type not in {"tool_failed", "mcp_tool_failed"}:
                    continue
                current_error_category = str(payload.get("error_category") or "").strip()
                if not current_error_category:
                    continue
                searchable_text = " ".join(
                    [
                        str(item.title or "").strip(),
                        str(entry.get("summary") or "").strip(),
                        str(entry.get("detail") or "").strip(),
                    ]
                ).lower()
                if normalized_keyword and normalized_keyword not in searchable_text:
                    continue
                if normalized_error_category and normalized_error_category != current_error_category:
                    continue
                error_counter.update([current_error_category])
                provider_counter.update([entry_provider] if entry_provider else [])
                model_counter.update([entry_model_name] if entry_model_name else [])

        part_counter: Counter[str] = Counter()
        for event in gap_events:
            part_counter.update(event["missing_parts"])

        top_missing_parts = [
            {"name": name, "count": count}
            for name, count in part_counter.most_common()
        ]

        suggestions = self._build_suggestions(part_counter.keys())
        recent_examples = gap_events[:5]

        benchmark_health = self._build_benchmark_health(
            items=items,
            filtered_entries_by_item=filtered_entries_by_item,
        )
        pending_actions, remediation_targets = self._build_remediation_targets(
            benchmark_health=benchmark_health
        )
        return {
            "total_gap_events": len(gap_events),
            "top_missing_parts": top_missing_parts,
            "top_profiles": [{"name": name, "count": count} for name, count in profile_counter.most_common()],
            "top_completion_stages": [{"name": name, "count": count} for name, count in stage_counter.most_common()],
            "top_error_categories": [{"name": name, "count": count} for name, count in error_counter.most_common()],
            "top_hook_event_types": [{"name": name, "count": count} for name, count in hook_event_counter.most_common()],
            "top_subagent_roles": [{"name": name, "count": count} for name, count in subagent_role_counter.most_common()],
            "top_providers": [{"name": name, "count": count} for name, count in provider_counter.most_common()],
            "top_models": [{"name": name, "count": count} for name, count in model_counter.most_common()],
            "trend_by_day": [
                {"date": day, "count": count}
                for day, count in sorted(day_counter.items(), key=lambda item: item[0])
            ],
            "provider_model_pairs": [
                {
                    "provider": pair.split("::", 1)[0],
                    "model": pair.split("::", 1)[1],
                    "count": count,
                }
                for pair, count in provider_model_counter.most_common()
            ],
            "profile_provider_model_pairs": [
                {
                    "profile": triple.split("::", 2)[0],
                    "provider": triple.split("::", 2)[1],
                    "model": triple.split("::", 2)[2],
                    "count": count,
                }
                for triple, count in profile_provider_model_counter.most_common()
            ],
            "window_comparison": self._build_window_comparison(
                total_current=len(gap_events),
                window_days=normalized_window_days,
                items=items,
            ),
            "top_regression_risk_models": self._build_regression_risk_models(
                current_window_counter=current_window_counter,
                previous_window_counter=previous_window_counter,
                window_days=normalized_window_days,
            ),
            "benchmark_health": benchmark_health,
            "pending_actions": pending_actions,
            "remediation_targets": remediation_targets,
            "suggested_investments": suggestions,
            "recent_examples": recent_examples,
            "available_missing_parts": sorted(part_counter.keys()),
            "available_profiles": sorted(profile_counter.keys()),
            "available_completion_stages": sorted(stage_counter.keys()),
            "available_error_categories": sorted(error_counter.keys()),
            "available_hook_event_types": sorted(hook_event_counter.keys()),
            "available_subagent_roles": sorted(subagent_role_counter.keys()),
            "available_providers": sorted(provider_counter.keys()),
            "available_models": sorted(model_counter.keys()),
            "applied_filters": {
                "limit": max(1, int(limit)),
                "missing_part": normalized_missing_part,
                "keyword": normalized_keyword,
                "profile": normalized_profile,
                "completion_stage": normalized_stage,
                "error_category": normalized_error_category,
                "hook_event_type": normalized_hook_event_type,
                "subagent_role": normalized_subagent_role,
                "provider": normalized_provider,
                "model_name": normalized_model_name,
                "window_days": normalized_window_days or None,
            },
        }

    def _build_remediation_targets(
        self,
        *,
        benchmark_health: Dict[str, Any],
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        unmatched = benchmark_health.get("benchmark_catalog_unmatched") or []
        action_playbook = benchmark_health.get("action_playbook") or {}
        pending_actions: List[Dict[str, Any]] = []
        for item in unmatched:
            if not isinstance(item, dict):
                continue
            action_id = str(item.get("remediation_action_id") or "").strip()
            if not action_id:
                continue
            ownership = self.ACTION_OWNERSHIP_MAP.get(action_id) or {}
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
            remediation_targets[action_id] = {
                "action_id": action_id,
                "owner": str(action.get("owner") or "").strip(),
                "module": str(action.get("module") or "").strip(),
                "playbook_title": str(action.get("playbook_title") or "").strip(),
                "files": list(action.get("files") or []),
            }
        return pending_actions, list(remediation_targets.values())

    def _build_benchmark_health(
        self,
        *,
        items: List[Any],
        filtered_entries_by_item: Dict[int, List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        benchmark_cases: List[Dict[str, Any]] = []
        for item in items:
            entries = filtered_entries_by_item.get(int(item.id), [])
            if not entries:
                continue
            benchmark_cases.append(
                {
                    "item_id": int(item.id),
                    "title": str(item.title or "").strip(),
                    "entries": entries,
                }
            )

        assertions: List[Dict[str, Any]] = []
        assertions.append(
            self._assert_final_synthesis_exists(benchmark_cases)
        )
        assertions.append(
            self._assert_boundary_has_gap_feedback(benchmark_cases)
        )
        assertions.append(
            self._assert_retry_has_converged(benchmark_cases)
        )
        assertions.append(
            self._assert_tool_call_budget(benchmark_cases)
        )

        total_assertions = len(assertions)
        passed_assertions = sum(1 for item in assertions if item.get("passed"))
        score = round((passed_assertions / total_assertions) * 100, 2) if total_assertions else 0.0
        benchmark_catalog = self._load_benchmark_catalog()
        catalog_evaluation = self._evaluate_benchmark_catalog(benchmark_cases, benchmark_catalog)
        coverage_ratio = float(catalog_evaluation.get("coverage_ratio") or 0.0)
        covered_profiles = sorted(
            {
                str((entry.get("payload") or {}).get("profile") or (entry.get("payload") or {}).get("completion_check", {}).get("profile") or "").strip()
                for case in benchmark_cases
                for entry in case.get("entries") or []
                if str((entry.get("payload") or {}).get("profile") or (entry.get("payload") or {}).get("completion_check", {}).get("profile") or "").strip()
            }
        )
        missing_profiles = [
            profile
            for profile in self.BENCHMARK_REQUIRED_PROFILES
            if profile not in covered_profiles
        ]
        gate_passed = (
            score >= self.BENCHMARK_SCORE_THRESHOLD
            and all(item.get("passed") for item in assertions)
            and coverage_ratio >= self.BENCHMARK_CATALOG_COVERAGE_THRESHOLD
        )
        return {
            "total_cases": len(benchmark_cases),
            "total_assertions": total_assertions,
            "passed_assertions": passed_assertions,
            "score": score,
            "threshold_score": self.BENCHMARK_SCORE_THRESHOLD,
            "gate_passed": gate_passed,
            "required_profiles": list(self.BENCHMARK_REQUIRED_PROFILES),
            "covered_profiles": covered_profiles,
            "missing_profiles": missing_profiles,
            "benchmark_catalog_total": catalog_evaluation.get("total_cases", 0),
            "benchmark_catalog_matched": catalog_evaluation.get("matched_cases", 0),
            "benchmark_catalog_coverage_ratio": coverage_ratio,
            "benchmark_catalog_coverage_threshold": self.BENCHMARK_CATALOG_COVERAGE_THRESHOLD,
            "benchmark_catalog_unmatched": catalog_evaluation.get("unmatched", []),
            "scenario_coverage": catalog_evaluation.get("scenario_coverage", []),
            "action_playbook": self.REMEDIATION_PLAYBOOK,
            "assertions": assertions,
        }

    def _evaluate_benchmark_catalog(
        self,
        benchmark_cases: List[Dict[str, Any]],
        benchmark_catalog: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        matched = 0
        scenario_counter: Counter[str] = Counter()
        scenario_matched_counter: Counter[str] = Counter()
        unmatched: List[Dict[str, Any]] = []
        total = len(benchmark_catalog)
        for case in benchmark_catalog:
            profile = str(case.get("profile") or "").strip()
            scenario = str(case.get("scenario") or "general").strip() or "general"
            scenario_counter.update([scenario])
            required_events = [str(item).strip() for item in (case.get("required_events") or []) if str(item).strip()]
            required_missing_parts = [str(item).strip() for item in (case.get("required_missing_parts") or []) if str(item).strip()]
            max_tool_calls = case.get("max_tool_calls")
            candidate_cases = []
            for observed in benchmark_cases:
                entries = observed.get("entries") or []
                if not entries:
                    continue
                observed_profiles = {
                    str((entry.get("payload") or {}).get("profile") or (entry.get("payload") or {}).get("completion_check", {}).get("profile") or "").strip()
                    for entry in entries
                }
                if profile not in observed_profiles:
                    continue
                candidate_cases.append(observed)

            case_matched = False
            failure_reason = "未找到匹配案例"
            for observed in candidate_cases:
                entries = observed.get("entries") or []
                event_types = [str(entry.get("event_type") or "").strip() for entry in entries]
                missing_events = [event for event in required_events if event not in event_types]
                if missing_events:
                    failure_reason = f"缺少事件: {', '.join(missing_events)}"
                    continue
                if required_missing_parts:
                    missing_union: set[str] = set()
                    for entry in entries:
                        if str(entry.get("event_type") or "").strip() != "capability_gap_fallback":
                            continue
                        payload = entry.get("payload") or {}
                        for part in payload.get("missing_parts") or []:
                            missing_union.add(str(part).strip())
                    missing_required_parts = [part for part in required_missing_parts if part not in missing_union]
                    if missing_required_parts:
                        failure_reason = f"缺少缺口字段: {', '.join(missing_required_parts)}"
                        continue
                if isinstance(max_tool_calls, int):
                    tool_calls = sum(1 for event_type in event_types if event_type in {"tool_called", "mcp_tool_called"})
                    if tool_calls > max_tool_calls:
                        failure_reason = f"工具调用超预算: {tool_calls}>{max_tool_calls}"
                        continue
                case_matched = True
                break

            if case_matched:
                matched += 1
                scenario_matched_counter.update([scenario])
            else:
                remediation_text, remediation_action_id = self._build_benchmark_remediation(
                    reason=failure_reason,
                    required_events=required_events,
                    profile=profile,
                )
                unmatched.append(
                    {
                        "id": str(case.get("id") or "").strip(),
                        "scenario": scenario,
                        "description": str(case.get("description") or "").strip(),
                        "profile": profile,
                        "required_events": required_events,
                        "reason": failure_reason,
                        "remediation": remediation_text,
                        "remediation_action_id": remediation_action_id,
                    }
                )
        coverage_ratio = round((matched / total), 4) if total > 0 else 0.0
        return {
            "total_cases": total,
            "matched_cases": matched,
            "coverage_ratio": coverage_ratio,
            "unmatched": unmatched[:10],
            "scenario_coverage": [
                {
                    "scenario": scenario,
                    "matched": scenario_matched_counter.get(scenario, 0),
                    "total": count,
                    "ratio": round((scenario_matched_counter.get(scenario, 0) / count), 4) if count > 0 else 0.0,
                }
                for scenario, count in sorted(scenario_counter.items(), key=lambda item: item[0])
            ],
        }

    def _build_benchmark_remediation(
        self,
        *,
        reason: str,
        required_events: List[str],
        profile: str,
    ) -> tuple[str, str]:
        lower_reason = str(reason or "").lower()
        if "缺少事件" in reason:
            if "completion_finalized" in reason or "completion_finalized" in required_events:
                return (
                    "检查收尾链路：确保工具结果后触发 completion evaluator，并落地 completion_finalized。",
                    "fix_final_synthesis_chain",
                )
            if "completion_retry" in reason:
                return (
                    "检查补查链路：确保首次不完整时进入 completion_retry，再收敛到 finalized/fallback。",
                    "fix_retry_convergence_chain",
                )
            if "capability_gap_fallback" in reason:
                return (
                    "检查能力边界收尾：能力不足时必须产出 capability_gap_fallback，并携带缺口字段。",
                    "fix_capability_boundary_fallback",
                )
            if "pre_tool_use_blocked" in reason:
                return (
                    "检查 Hook 治理配置：确认 pre_tool_use 策略启用且阻断事件写入 run trace。",
                    "fix_hook_trace_mapping",
                )
            if "child_completed" in reason:
                return (
                    "检查 Subagent 回传链路：确认 child_completed 事件已写入并附带 agent_role。",
                    "fix_subagent_trace_mapping",
                )
            if "tool_failed" in reason:
                return (
                    "检查错误分类链路：确保 tool_failed/mcp_tool_failed 事件保留 error_category。",
                    "fix_tool_error_classification",
                )
            return (
                "检查事件映射：确认所需事件已从 runtime event 正确映射到 run trace。",
                "fix_runtime_event_trace_mapping",
            )
        if "缺少缺口字段" in reason:
            return (
                "检查 capability_gap_fallback payload：补齐 missing_parts 并保证字段名一致。",
                "fix_fallback_payload_missing_parts",
            )
        if "超预算" in reason or "budget" in lower_reason:
            return (
                f"检查工具调用策略：收紧 `{profile}` 模板的工具预算或增强一次查询覆盖率。",
                "reduce_tool_call_budget",
            )
        if "未找到匹配案例" in reason:
            return (
                "检查样本覆盖：补充该 profile 的真实回放案例或调整 benchmark 用例定义。",
                "expand_profile_benchmark_samples",
            )
        return (
            "检查该用例的执行链路与 benchmark 定义是否一致。",
            "fix_runtime_event_trace_mapping",
        )

    def _assert_final_synthesis_exists(self, cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        checked = 0
        failed_cases: List[Dict[str, Any]] = []
        for case in cases:
            entries = case.get("entries") or []
            has_tool_activity = any(
                str(entry.get("event_type") or "").strip() in {"tool_called", "mcp_tool_called", "tool_failed", "mcp_tool_failed"}
                for entry in entries
            )
            if not has_tool_activity:
                continue
            checked += 1
            has_finalized = any(
                str(entry.get("event_type") or "").strip() == "completion_finalized"
                for entry in entries
            )
            if not has_finalized:
                failed_cases.append({"item_id": case["item_id"], "title": case["title"]})
        return {
            "id": "final_synthesis_exists",
            "label": "最终答复收尾存在",
            "checked": checked,
            "failed": len(failed_cases),
            "passed": len(failed_cases) == 0,
            "failed_cases": failed_cases[:5],
        }

    def _assert_boundary_has_gap_feedback(self, cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        checked = 0
        failed_cases: List[Dict[str, Any]] = []
        for case in cases:
            entries = case.get("entries") or []
            has_boundary = any(
                str(entry.get("event_type") or "").strip() == "capability_gap_fallback"
                for entry in entries
            )
            if not has_boundary:
                continue
            checked += 1
            has_missing_parts = False
            for entry in entries:
                if str(entry.get("event_type") or "").strip() != "capability_gap_fallback":
                    continue
                payload = entry.get("payload") or {}
                missing_parts = payload.get("missing_parts") or []
                if isinstance(missing_parts, list) and len(missing_parts) > 0:
                    has_missing_parts = True
                    break
            if not has_missing_parts:
                failed_cases.append({"item_id": case["item_id"], "title": case["title"]})
        return {
            "id": "boundary_has_gap_feedback",
            "label": "能力边界场景有缺口说明",
            "checked": checked,
            "failed": len(failed_cases),
            "passed": len(failed_cases) == 0,
            "failed_cases": failed_cases[:5],
        }

    def _assert_retry_has_converged(self, cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        checked = 0
        failed_cases: List[Dict[str, Any]] = []
        for case in cases:
            entries = case.get("entries") or []
            has_retry = any(
                str(entry.get("event_type") or "").strip() == "completion_retry"
                for entry in entries
            )
            if not has_retry:
                continue
            checked += 1
            has_converged = any(
                str(entry.get("event_type") or "").strip() in {"completion_finalized", "capability_gap_fallback"}
                for entry in entries
            )
            if not has_converged:
                failed_cases.append({"item_id": case["item_id"], "title": case["title"]})
        return {
            "id": "retry_has_converged",
            "label": "补查后有收敛结果",
            "checked": checked,
            "failed": len(failed_cases),
            "passed": len(failed_cases) == 0,
            "failed_cases": failed_cases[:5],
        }

    def _assert_tool_call_budget(self, cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        checked = 0
        failed_cases: List[Dict[str, Any]] = []
        budget_by_profile = {
            "travel_planning": 2,
            "research_compare": 3,
            "planning": 2,
        }
        for case in cases:
            entries = case.get("entries") or []
            profiles = []
            for entry in entries:
                payload = entry.get("payload") or {}
                profile = str(payload.get("profile") or payload.get("completion_check", {}).get("profile") or "").strip()
                if profile:
                    profiles.append(profile)
            if not profiles:
                continue
            profile = profiles[0]
            budget = budget_by_profile.get(profile)
            if budget is None:
                continue
            checked += 1
            tool_calls = sum(
                1
                for entry in entries
                if str(entry.get("event_type") or "").strip() in {"tool_called", "mcp_tool_called"}
            )
            if tool_calls > budget:
                failed_cases.append(
                    {
                        "item_id": case["item_id"],
                        "title": case["title"],
                        "profile": profile,
                        "tool_calls": tool_calls,
                        "budget": budget,
                    }
                )
        return {
            "id": "tool_call_budget",
            "label": "工具调用次数预算",
            "checked": checked,
            "failed": len(failed_cases),
            "passed": len(failed_cases) == 0,
            "failed_cases": failed_cases[:5],
        }

    def _build_window_comparison(
        self,
        *,
        total_current: int,
        window_days: int,
        items: List[Any],
    ) -> Dict[str, Any]:
        if window_days <= 0:
            return {
                "window_days": None,
                "current_count": total_current,
                "previous_count": None,
                "delta_count": None,
                "delta_ratio": None,
            }
        now_utc = datetime.now(timezone.utc)
        current_start = now_utc - timedelta(days=window_days)
        previous_start = current_start - timedelta(days=window_days)
        previous_count = 0
        for item in items:
            metadata = dict(item.item_metadata or {})
            run_trace = metadata.get("run_trace") or []
            for entry in run_trace:
                if not isinstance(entry, dict):
                    continue
                if str(entry.get("event_type") or "").strip() != "capability_gap_fallback":
                    continue
                entry_dt = self._parse_timestamp(entry.get("timestamp"))
                if entry_dt is None:
                    continue
                if previous_start <= entry_dt < current_start:
                    previous_count += 1
        delta = total_current - previous_count
        delta_ratio = None
        if previous_count > 0:
            delta_ratio = round(delta / previous_count, 4)
        return {
            "window_days": window_days,
            "current_count": total_current,
            "previous_count": previous_count,
            "delta_count": delta,
            "delta_ratio": delta_ratio,
        }

    def _build_regression_risk_models(
        self,
        *,
        current_window_counter: Counter[str],
        previous_window_counter: Counter[str],
        window_days: int,
    ) -> List[Dict[str, Any]]:
        if window_days <= 0:
            return []
        risk_rows: List[Dict[str, Any]] = []
        keys = set(current_window_counter.keys()) | set(previous_window_counter.keys())
        for pair in keys:
            current_count = current_window_counter.get(pair, 0)
            previous_count = previous_window_counter.get(pair, 0)
            delta = current_count - previous_count
            if current_count <= 0 and delta <= 0:
                continue
            provider, model = pair.split("::", 1)
            risk_rows.append(
                {
                    "provider": provider,
                    "model": model,
                    "current_count": current_count,
                    "previous_count": previous_count,
                    "delta_count": delta,
                    "risk_level": "high" if delta >= 2 else ("medium" if delta == 1 else "stable"),
                }
            )
        risk_rows.sort(key=lambda row: (row["delta_count"], row["current_count"]), reverse=True)
        return risk_rows[:10]

    def _normalize_list(self, values: Iterable[Any]) -> List[str]:
        normalized: List[str] = []
        for value in values or []:
            text = str(value or "").strip()
            if text and text not in normalized:
                normalized.append(text)
        return normalized

    def _build_suggestions(self, missing_parts: Iterable[str]) -> List[str]:
        suggestion_map = {
            "weather": "补充更稳定的天气/地理位置工具或天气 MCP。",
            "transport": "优先补交通路线检索工具，或接入地图 / 出行类 MCP。",
            "play": "优先补 POI / 景点检索工具，或接入旅游攻略类 MCP。",
        }
        suggestions: List[str] = []
        for part in missing_parts:
            suggestion = suggestion_map.get(part)
            if suggestion and suggestion not in suggestions:
                suggestions.append(suggestion)
        return suggestions


def get_capability_gap_service(db) -> CapabilityGapService:
    return CapabilityGapService(db)
