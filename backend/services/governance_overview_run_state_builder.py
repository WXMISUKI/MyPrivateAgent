"""Governance overview run-state assembly for Runtime Surface."""

from __future__ import annotations

from typing import Any, Dict

try:
    from services.runtime_core_contract_builder import RuntimeCoreContractBuilder
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.runtime_core_contract_builder import RuntimeCoreContractBuilder


class GovernanceOverviewRunStateBuilder:
    """Build the governance_overview.run contract section."""

    @classmethod
    def build_run_state(cls, *, runtime_scope: Dict[str, Any] | None = None) -> Dict[str, Any]:
        scope = dict(runtime_scope or {})
        return {
            "runtime_core": True,
            "run_id": str(scope.get("run_id") or "").strip(),
            "parent_run_id": str(scope.get("parent_run_id") or "").strip(),
            "child_run_id": str(scope.get("child_run_id") or "").strip(),
            "child_display_id": str(
                scope.get("child_display_id") or scope.get("child_run_id") or ""
            ).strip(),
            "scheduler_run_id": str(scope.get("scheduler_run_id") or "").strip(),
            "run_kind": str(scope.get("run_kind") or "contract").strip() or "contract",
            "status": str(scope.get("status") or "not_started").strip() or "not_started",
            "trace_count": int(scope.get("trace_count") or 0),
            "latest_trace_event": dict(scope.get("latest_trace_event") or {}) or None,
            **RuntimeCoreContractBuilder.build_child_merge_state_contract(scope),
        }
