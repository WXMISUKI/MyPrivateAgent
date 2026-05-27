"""Runtime Core contract assembly for Runtime Surface."""

from __future__ import annotations

from typing import Any, Dict


class RuntimeCoreContractBuilder:
    """Build the Runtime Surface runtime_core contract section."""

    @classmethod
    def build_contract(cls, *, runtime_scope: Dict[str, Any] | None = None) -> Dict[str, Any]:
        contract = {
            "runtime_core": True,
            "contract_version": "phase-a-runtime-core-v1",
            "run_state_model": "AgentRunContext",
            "event_model": "AgentEvent",
            "approval_model": "ApprovalRequestState",
            "run_id": "",
            "parent_run_id": "",
            "child_run_id": "",
            "child_display_id": "",
            "scheduler_run_id": "",
            "run_kind": "contract",
            "status": "not_started",
            "trace_count": 0,
            "latest_trace_event": None,
            **cls.build_child_merge_state_contract(),
        }
        scope = dict(runtime_scope or {})
        if scope:
            contract["run_id"] = str(scope.get("run_id") or "").strip()
            contract["parent_run_id"] = str(scope.get("parent_run_id") or "").strip()
            contract["child_run_id"] = str(scope.get("child_run_id") or "").strip()
            contract["child_display_id"] = str(
                scope.get("child_display_id") or scope.get("child_run_id") or ""
            ).strip()
            contract["scheduler_run_id"] = str(scope.get("scheduler_run_id") or "").strip()
            contract["run_kind"] = str(scope.get("run_kind") or contract["run_kind"]).strip() or contract["run_kind"]
            contract["status"] = str(scope.get("status") or contract["status"]).strip() or contract["status"]
            contract["trace_count"] = int(scope.get("trace_count") or 0)
            contract["latest_trace_event"] = dict(scope.get("latest_trace_event") or {}) or None
            contract.update(cls.build_child_merge_state_contract(scope))
        return contract

    @staticmethod
    def build_child_merge_state_contract(runtime_scope: Dict[str, Any] | None = None) -> Dict[str, Any]:
        scope = dict(runtime_scope or {})
        return {
            "child_merge_intent": str(scope.get("child_merge_intent") or "").strip(),
            "child_merge_entities": list(scope.get("child_merge_entities") or []),
            "child_merge_entity_count": int(scope.get("child_merge_entity_count") or 0),
            "child_merge_focus_count": int(scope.get("child_merge_focus_count") or 0),
            "child_merge_action_count": int(scope.get("child_merge_action_count") or 0),
            "child_merge_primary_entities": list(scope.get("child_merge_primary_entities") or []),
            "child_merge_conclusion": str(scope.get("child_merge_conclusion") or "").strip(),
            "child_merge_section_source": str(scope.get("child_merge_section_source") or "").strip(),
            "child_merge_section_ids": list(scope.get("child_merge_section_ids") or []),
            "child_merge_section_counts": dict(scope.get("child_merge_section_counts") or {}),
        }
