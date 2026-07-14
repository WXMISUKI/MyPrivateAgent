"""Runtime Plane read-model builder for Runtime Surface."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict


class RuntimeSurfaceRuntimePlaneBuilder:
    """Build read-only Runtime Surface contracts for runtime-plane projections."""

    CONTRACT_VERSION = "runtime-surface-runtime-plane-profile-v1"
    SUPPORTED_ADAPTER_IDS = ("simple_agent", "tool_agent", "approval_agent")

    @classmethod
    def build_governance_profile(
        cls,
        projection: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        normalized_projection = dict(projection or {}) if isinstance(projection, Mapping) else {}
        latest_summary = cls._build_latest_projection_summary(normalized_projection)
        latest_available = bool(latest_summary)
        return {
            "contract_version": cls.CONTRACT_VERSION,
            "projection_contract_status": "ready",
            "projection_contract_version": "runtime-plane-governance-read-model-v1",
            "supported_adapter_ids": list(cls.SUPPORTED_ADAPTER_IDS),
            "supported_adapter_count": len(cls.SUPPORTED_ADAPTER_IDS),
            "latest_projection_available": latest_available,
            "reason": "" if latest_available else "projection_source_unavailable",
            "latest_projection": latest_summary if latest_available else None,
            "boundaries": {
                "read_model_only": True,
                "will_execute_adapter": False,
                "will_persist_projection": False,
                "will_persist_trace": False,
                "will_submit_approval": False,
                "default_chat_changed": False,
                "frontend_ui_changed": False,
            },
        }

    @classmethod
    def _build_latest_projection_summary(cls, projection: Mapping[str, Any]) -> Dict[str, Any]:
        if not projection:
            return {}
        return {
            "read_model": str(projection.get("read_model") or "").strip(),
            "contract_version": str(projection.get("contract_version") or "").strip(),
            "request_id": str(projection.get("request_id") or "").strip(),
            "run_id": str(projection.get("run_id") or "").strip(),
            "agent_id": str(projection.get("agent_id") or "").strip(),
            "runtime": str(projection.get("runtime") or "").strip(),
            "adapter_id": str(projection.get("adapter_id") or "").strip(),
            "result_status": str(projection.get("result_status") or "").strip(),
            "trace_ref": str(projection.get("trace_ref") or "").strip(),
            "event_count": cls._safe_int(projection.get("event_count")),
            "stage_counts": dict(projection.get("stage_counts") or {}),
            "tool_call_count": cls._safe_int(projection.get("tool_call_count")),
            "approval_required": bool(projection.get("approval_required")),
            "approval_status": str(projection.get("approval_status") or "").strip(),
            "approval_tool_name": str(projection.get("approval_tool_name") or "").strip() or None,
        }

    @staticmethod
    def _safe_int(value: Any) -> int:
        try:
            return max(0, int(value or 0))
        except (TypeError, ValueError):
            return 0
