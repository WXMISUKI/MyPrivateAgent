"""Runtime contract for the query control plane."""

from __future__ import annotations

from typing import Any, Dict


class QueryControlPlaneService:
    """Describe the canonical request lifecycle shared by runtime entry points."""

    CONTRACT_VERSION = "phase-g-query-control-plane-v1"

    def build_runtime_contract(self) -> Dict[str, Any]:
        return {
            "contract_version": self.CONTRACT_VERSION,
            "overall_status": "design_ready",
            "lifecycle_stages": [
                "input_received",
                "context_assembly",
                "planning",
                "model_stream",
                "tool_decision",
                "tool_execution",
                "observation",
                "review",
                "final_output",
            ],
            "execution_channels": [
                "main_chat",
                "embedded_sdk",
                "external_adapter",
                "subagent_lane",
            ],
            "required_trace_events": [
                "input_received",
                "context_assembly",
                "planning",
                "model_stream",
                "tool_decision",
                "tool_execution",
                "observation",
                "review",
                "final_output",
            ],
            "adapter_boundaries": {
                "context_assembler": "builds prompt context from project, memory, runtime contracts, and user input",
                "provider_adapter": "normalizes model streams into runtime events",
                "tool_runtime": "normalizes tool decisions, permission checks, execution, and results",
                "tool_runtime_observation_payload": "compact_status_summary",
                "reviewer": "normalizes quality gate decisions before final output",
                "timeline": "records lifecycle events through QueryControlTimelineService",
            },
            "governance_requirements": [
                "traceable_lifecycle_stage",
                "dedupe_key_for_replayable_events",
                "snapshot_ref_for_governance_events",
                "fail_closed_tool_policy",
                "review_before_final_output_when_configured",
            ],
            "runtime_surface_enabled": True,
        }


_query_control_plane_service: QueryControlPlaneService | None = None


def get_query_control_plane_service() -> QueryControlPlaneService:
    global _query_control_plane_service
    if _query_control_plane_service is None:
        _query_control_plane_service = QueryControlPlaneService()
    return _query_control_plane_service
