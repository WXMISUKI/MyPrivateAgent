"""Versioned runtime contract snapshot guard for Phase C."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Sequence


@dataclass(frozen=True)
class ContractSnapshotSpec:
    contract_name: str
    required_fields: Sequence[str]
    required_status_kinds: Mapping[str, Sequence[str]] | None = None
    required_event_payloads: Mapping[str, Mapping[str, Sequence[str]]] | None = None


class RuntimeContractSnapshotService:
    """Build stable fingerprints for runtime contracts exposed by RuntimeSurfaceService."""

    SNAPSHOT_CONTRACT_VERSION = "phase-c-runtime-contract-snapshot-v1"

    REQUIRED_CONTRACTS: Sequence[ContractSnapshotSpec] = (
        ContractSnapshotSpec(
            contract_name="tool_runtime",
            required_fields=(
                "contract_version",
                "total_tools",
                "base_tool_count",
                "langchain_tool_count",
                "tool_spec_count",
                "doubao_definition_count",
                "mcp_capability_count",
                "high_risk_tool_count",
                "tools",
            ),
        ),
        ContractSnapshotSpec(
            contract_name="mcp_runtime",
            required_fields=(
                "contract_version",
                "overall_status",
                "capability_count",
                "components",
            ),
        ),
        ContractSnapshotSpec(
            contract_name="skill_contract",
            required_fields=(
                "contract_version",
                "total_definitions",
                "definitions",
            ),
        ),
        ContractSnapshotSpec(
            contract_name="memory_contract",
            required_fields=(
                "contract_version",
                "active",
                "loaded_layers",
                "missing_layers",
                "memory_entries",
                "layer_order",
            ),
        ),
        ContractSnapshotSpec(
            contract_name="command_contract",
            required_fields=(
                "contract_version",
                "total_commands",
                "command_definitions",
                "embedded_sdk",
                "embedded_sdk.volatile_runtime_state",
                "embedded_sdk.persistence_seams",
                "embedded_sdk.recovery_entrypoints",
                "embedded_sdk.delegate_preflight",
                "embedded_sdk.delegate_preflight.status",
                "embedded_sdk.delegate_preflight.promotion_requirements",
                "embedded_sdk.event_status_kinds",
                "agent_harness_facade",
                "agent_harness_facade.delegate_preflight",
                "agent_harness_facade.delegate_preflight.status",
            ),
            required_status_kinds={
                "embedded_sdk.event_status_kinds": (
                    "approval_created",
                    "approval_resolved",
                    "approval_replayed",
                    "approval_ignored",
                    "execution_loop_done",
                    "loop_continuation_registered",
                    "loop_continuation_consumed",
                    "loop_continuation_discarded",
                ),
            },
            required_event_payloads={
                "embedded_sdk.event_status_kinds": {
                    "approval_created": ("approval_request_id", "approval_request"),
                    "approval_resolved": ("approval_request_id", "approval_request", "decision"),
                    "approval_replayed": (
                        "approval_request_id",
                        "approval_request",
                        "original_decision",
                        "attempted_decision",
                    ),
                    "approval_ignored": (
                        "approval_request_id",
                        "approval_request",
                        "original_decision",
                        "attempted_decision",
                    ),
                    "execution_loop_done": ("run", "completed_steps"),
                    "loop_continuation_registered": ("loop_continuation",),
                    "loop_continuation_consumed": ("loop_continuation",),
                    "loop_continuation_discarded": ("loop_continuation",),
                },
            },
        ),
        ContractSnapshotSpec(
            contract_name="adapter_health",
            required_fields=(
                "contract_version",
                "overall_status",
                "adapter_count",
                "unavailable_count",
                "adapters",
            ),
        ),
        ContractSnapshotSpec(
            contract_name="runtime_contract_gate",
            required_fields=(
                "contract_version",
                "available",
                "overall_status",
                "check_count",
                "failed_check_count",
                "runtime_contract_summary",
                "runtime_contract_summary.overall_status",
                "runtime_contract_summary.check_count",
                "runtime_contract_summary.failed_check_count",
                "runtime_contract_summary.missing_payload_count",
                "runtime_contract_summary.approval_replay_coverage",
                "runtime_contract_summary.approval_lifecycle_recovery_coverage",
                "runtime_contract_summary.approval_lifecycle_recovery_coverage.alignment_smoke",
                "runtime_contract_summary.approved_tool_execution_coverage",
                "runtime_contract_summary.sdk_tool_runtime_execution_coverage",
                "runtime_contract_summary.sdk_tool_runtime_execution_coverage.bridge_smoke",
                "runtime_contract_summary.tool_runtime_timeout_retry_coverage",
                "runtime_contract_summary.tool_runtime_timeout_retry_coverage.timeout_retry_smoke",
                "runtime_contract_summary.checkpoint_resume_cursor_coverage",
                "runtime_contract_summary.checkpoint_resume_cursor_coverage.cursor_smoke",
                "runtime_contract_summary.embedded_sdk_persistence_coverage",
                "runtime_contract_summary.embedded_sdk_persistence_coverage.persistence_smoke",
                "runtime_contract_summary.embedded_sdk_persistence_coverage.production_recovery_worker_ownership_gate_status",
                "runtime_contract_summary.embedded_sdk_persistence_coverage.production_recovery_worker_ownership_missing_sections",
                "runtime_contract_summary.worker_ownership_store_mode_coverage",
                "runtime_contract_summary.worker_ownership_store_mode_coverage.mode_smoke",
                "runtime_contract_summary.worker_ownership_store_mode_coverage.enablement_config_factory_binding_smoke",
                "runtime_contract_summary.recovery_retry_evidence_coverage",
                "runtime_contract_summary.recovery_retry_evidence_coverage.retry_smoke",
                "runtime_contract_summary.recovery_retry_scheduler_coverage",
                "runtime_contract_summary.recovery_retry_scheduler_coverage.scheduler_smoke",
                "runtime_contract_summary.durable_recovery_loader_coverage",
                "runtime_contract_summary.durable_recovery_loader_coverage.loader_smoke",
                "runtime_contract_summary.continuation_descriptor_lifecycle_coverage",
                "runtime_contract_summary.continuation_descriptor_lifecycle_coverage.lifecycle_smoke",
                "runtime_contract_summary.loader_execution_handoff_coverage",
                "runtime_contract_summary.loader_execution_handoff_coverage.handoff_smoke",
                "runtime_contract_summary.recovery_audit_operation_history_coverage",
                "runtime_contract_summary.recovery_audit_operation_history_coverage.audit_smoke",
                "runtime_contract_summary.production_recovery_registry_checkpoint_policy_coverage",
                "runtime_contract_summary.production_recovery_registry_checkpoint_policy_coverage.policy_smoke",
                "runtime_contract_summary.child_executor_promotion_gate_coverage",
                "runtime_contract_summary.child_executor_promotion_gate_coverage.gate_smoke",
                "runtime_contract_summary.child_executor_execution_prerequisites_coverage",
                "runtime_contract_summary.child_executor_execution_prerequisites_coverage.prerequisites_smoke",
                "runtime_contract_summary.child_executor_execution_prerequisites_coverage.context_budget_policy_status",
                "runtime_contract_summary.child_executor_execution_prerequisites_coverage.context_budget_policy_missing_sections",
                "runtime_contract_summary.child_executor_execution_prerequisites_coverage.opt_in_context_budget_policy_ready",
                "runtime_contract_summary.child_executor_execution_prerequisites_coverage.merge_handoff_status",
                "runtime_contract_summary.child_executor_execution_prerequisites_coverage.merge_handoff_missing_sections",
                "runtime_contract_summary.child_executor_execution_prerequisites_coverage.opt_in_merge_handoff_ready",
                "runtime_contract_summary.child_executor_dispatch_coverage",
                "runtime_contract_summary.child_executor_dispatch_coverage.dispatch_smoke",
                "runtime_contract_summary.child_executor_dispatch_coverage.dispatch_attempt_handoff_status",
                "runtime_contract_summary.child_executor_dispatch_coverage.opt_in_dispatch_attempt_handoff_ready",
                "runtime_contract_summary.child_executor_dispatch_coverage.opt_in_attempt_validation_ready",
                "runtime_contract_summary.child_executor_dispatcher_coverage",
                "runtime_contract_summary.child_executor_dispatcher_coverage.dispatcher_smoke",
                "runtime_contract_summary.child_executor_dispatch_result_handoff_coverage",
                "runtime_contract_summary.child_executor_dispatch_result_handoff_coverage.result_handoff_smoke",
                "runtime_contract_summary.child_executor_dispatch_result_handoff_coverage.ready_handoff_status",
                "runtime_contract_summary.child_executor_dispatch_result_handoff_coverage.malformed_handoff_status",
                "runtime_contract_summary.child_executor_dispatch_result_retry_audit_coverage",
                "runtime_contract_summary.child_executor_dispatch_result_retry_audit_coverage.retry_audit_smoke",
                "runtime_contract_summary.child_executor_dispatch_result_retry_audit_coverage.retryable_retry_policy_status",
                "runtime_contract_summary.child_executor_dispatch_result_retry_audit_coverage.missing_idempotency_status",
                "runtime_contract_summary.child_executor_sandbox_backend_coverage",
                "runtime_contract_summary.child_executor_sandbox_backend_coverage.sandbox_backend_smoke",
                "runtime_contract_summary.subagent_lane_query_detail_coverage",
                "runtime_contract_summary.subagent_lane_query_detail_coverage.detail_smoke",
                "runtime_contract_artifact_schema",
                "runtime_contract_artifact_schema.contract_version",
                "runtime_contract_artifact_schema.overall_status",
                "runtime_contract_artifact_schema.summary_required_fields",
                "runtime_contract_artifact_schema.summary_missing_fields",
                "checks",
            ),
        ),
        ContractSnapshotSpec(
            contract_name="child_executor_dispatch_contract",
            required_fields=(
                "contract_version",
                "overall_status",
                "dispatch_ready",
                "will_dispatch",
                "dispatch_mode",
                "backend_id",
                "backend_dispatch_ready",
                "gate_allowed",
                "prerequisites_ready",
                "relationship_seam_preserved",
                "blockers",
                "required_contracts",
                "child_executor_dispatch_attempt_handoff",
                "child_executor_dispatch_attempt_handoff.contract_version",
                "child_executor_dispatch_attempt_handoff.overall_status",
                "child_executor_dispatch_attempt_handoff.ready",
                "child_executor_dispatch_attempt_handoff.will_dispatch",
                "recommended_next_step",
            ),
        ),
        ContractSnapshotSpec(
            contract_name="main_chat_query_detail",
            required_fields=(
                "contract_version",
                "connected",
                "read_model_layer",
                "source_channel",
                "identity_kind",
                "query_id",
                "recording_state",
                "stage_chain",
                "dedupe_keys",
                "dedupe_key_count",
                "recent_events",
                "recent_event_count",
                "latest_snapshot_id",
                "latest_warning_summary",
                "latest_stage",
                "latest_summary",
                "stage_count",
                "warning_count",
                "event_count",
                "reason",
            ),
        ),
        ContractSnapshotSpec(
            contract_name="external_adapter_recent_summary",
            required_fields=(
                "contract_version",
                "connected",
                "recording_state",
                "items",
                "latest_query_id",
                "latest_stage",
                "latest_summary",
                "latest_timestamp",
                "total_items",
                "reason",
            ),
        ),
        ContractSnapshotSpec(
            contract_name="channel_promotion_gate",
            required_fields=(
                "contract_version",
                "overall_status",
                "layer_order",
                "channels",
                "channels_by_id",
                "channels_by_id.main_chat",
                "channels_by_id.subagent_lane",
                "channels_by_id.external_adapter",
                "over_promotion_guard",
                "over_promotion_guard.blocked_channels",
                "over_promotion_guard.blocked_layers",
                "over_promotion_guard.reason",
            ),
        ),
        ContractSnapshotSpec(
            contract_name="self_improvement_ledger",
            required_fields=(
                "contract_version",
                "overall_status",
                "record_types",
                "tracked_sources",
                "promotion_targets",
                "governance_states",
                "quality_controls",
                "runtime_surface_enabled",
                "health_summary",
            ),
        ),
        ContractSnapshotSpec(
            contract_name="query_control_plane",
            required_fields=(
                "contract_version",
                "overall_status",
                "lifecycle_stages",
                "execution_channels",
                "required_trace_events",
                "adapter_boundaries",
                "governance_requirements",
                "runtime_surface_enabled",
            ),
        ),
    )

    def build_snapshot(self, runtime_profile: Mapping[str, Any]) -> Dict[str, Any]:
        profile = dict(runtime_profile or {})
        contracts = [self._build_contract_snapshot(profile, spec) for spec in self.REQUIRED_CONTRACTS]
        missing_contract_count = len([item for item in contracts if item["status"] == "missing"])
        missing_field_count = sum(len(item["missing_fields"]) for item in contracts if item["status"] != "missing")
        missing_status_kind_count = sum(
            item.get("missing_status_kind_count", 0)
            for item in contracts
            if item["status"] != "missing"
        )
        missing_event_payload_count = sum(
            item.get("missing_event_payload_count", 0)
            for item in contracts
            if item["status"] != "missing"
        )
        overall_status = (
            "degraded"
            if missing_contract_count or missing_field_count or missing_status_kind_count or missing_event_payload_count
            else "healthy"
        )
        fingerprint_payload = [
            {
                "contract_name": item["contract_name"],
                "version": item["version"],
                "stable_fields": item["stable_fields"],
                "missing_fields": item["missing_fields"],
                "missing_status_kinds": item.get("missing_status_kinds", {}),
                "missing_event_payloads": item.get("missing_event_payloads", {}),
            }
            for item in contracts
        ]
        return {
            "contract_version": self.SNAPSHOT_CONTRACT_VERSION,
            "overall_status": overall_status,
            "contract_count": len(contracts),
            "missing_contract_count": missing_contract_count,
            "missing_field_count": missing_field_count,
            "missing_status_kind_count": missing_status_kind_count,
            "missing_event_payload_count": missing_event_payload_count,
            "fingerprint": self._fingerprint(fingerprint_payload),
            "contracts": contracts,
        }

    def _build_contract_snapshot(self, profile: Mapping[str, Any], spec: ContractSnapshotSpec) -> Dict[str, Any]:
        raw_contract = profile.get(spec.contract_name)
        if not isinstance(raw_contract, Mapping):
            return {
                "contract_name": spec.contract_name,
                "version": "",
                "status": "missing",
                "stable_fields": [],
                "missing_fields": list(spec.required_fields),
                "missing_status_kinds": {},
                "missing_status_kind_count": 0,
                "missing_event_payloads": {},
                "missing_event_payload_count": 0,
                "field_count": 0,
                "fingerprint": self._fingerprint({"contract_name": spec.contract_name, "missing": True}),
            }

        contract = dict(raw_contract)
        present_fields = [field_name for field_name in spec.required_fields if self._has_path(contract, field_name)]
        missing_fields = [field_name for field_name in spec.required_fields if not self._has_path(contract, field_name)]
        missing_status_kinds = self._find_missing_status_kinds(contract, spec.required_status_kinds or {})
        missing_status_kind_count = sum(len(items) for items in missing_status_kinds.values())
        missing_event_payloads = self._find_missing_event_payloads(contract, spec.required_event_payloads or {})
        missing_event_payload_count = sum(
            len(fields)
            for events in missing_event_payloads.values()
            for fields in events.values()
        )
        stable_payload = {field_name: self._shape_of(self._get_path(contract, field_name)) for field_name in present_fields}
        version = str(contract.get("contract_version") or "")
        return {
            "contract_name": spec.contract_name,
            "version": version,
            "status": "degraded" if missing_fields or missing_status_kind_count or missing_event_payload_count else "healthy",
            "stable_fields": present_fields,
            "missing_fields": missing_fields,
            "missing_status_kinds": missing_status_kinds,
            "missing_status_kind_count": missing_status_kind_count,
            "missing_event_payloads": missing_event_payloads,
            "missing_event_payload_count": missing_event_payload_count,
            "field_count": len(present_fields),
            "fingerprint": self._fingerprint({
                "contract_name": spec.contract_name,
                "version": version,
                "stable_payload": stable_payload,
                "missing_fields": missing_fields,
                "missing_status_kinds": missing_status_kinds,
                "missing_event_payloads": missing_event_payloads,
            }),
        }

    def _shape_of(self, value: Any) -> Any:
        if isinstance(value, Mapping):
            return {
                "type": "object",
                "fields": sorted(str(key) for key in value.keys()),
            }
        if isinstance(value, list):
            return {
                "type": "array",
                "length": len(value),
                "item_shape": self._shape_of(value[0]) if value else None,
            }
        if isinstance(value, tuple):
            return {
                "type": "array",
                "length": len(value),
                "item_shape": self._shape_of(value[0]) if value else None,
            }
        if isinstance(value, bool):
            return {"type": "boolean"}
        if isinstance(value, int) or isinstance(value, float):
            return {"type": "number"}
        if value is None:
            return {"type": "null"}
        return {"type": "string"}

    def _has_path(self, value: Mapping[str, Any], path: str) -> bool:
        sentinel = object()
        return self._get_path(value, path, default=sentinel) is not sentinel

    def _get_path(self, value: Mapping[str, Any], path: str, default: Any = None) -> Any:
        current: Any = value
        for part in str(path or "").split("."):
            if not isinstance(current, Mapping) or part not in current:
                return default
            current = current[part]
        return current

    def _find_missing_status_kinds(
        self,
        contract: Mapping[str, Any],
        requirements: Mapping[str, Sequence[str]],
    ) -> Dict[str, List[str]]:
        missing: Dict[str, List[str]] = {}
        for path, required_status_kinds in requirements.items():
            raw_status_kinds = self._get_path(contract, path, default=[])
            available = self._extract_status_kinds(raw_status_kinds)
            missing_for_path = [
                str(status_kind)
                for status_kind in required_status_kinds
                if str(status_kind) not in available
            ]
            if missing_for_path:
                missing[str(path)] = missing_for_path
        return missing

    def _extract_status_kinds(self, value: Any) -> set[str]:
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
            return set()
        status_kinds: set[str] = set()
        for item in value:
            if isinstance(item, Mapping):
                status_kind = str(item.get("status_kind") or "").strip()
                if status_kind:
                    status_kinds.add(status_kind)
            else:
                status_kind = str(item or "").strip()
                if status_kind:
                    status_kinds.add(status_kind)
        return status_kinds

    def _find_missing_event_payloads(
        self,
        contract: Mapping[str, Any],
        requirements: Mapping[str, Mapping[str, Sequence[str]]],
    ) -> Dict[str, Dict[str, List[str]]]:
        missing: Dict[str, Dict[str, List[str]]] = {}
        for path, required_payloads_by_status_kind in requirements.items():
            raw_status_kinds = self._get_path(contract, path, default=[])
            event_definitions = self._index_event_status_kinds(raw_status_kinds)
            missing_for_path: Dict[str, List[str]] = {}
            for status_kind, required_payload in required_payloads_by_status_kind.items():
                event_definition = event_definitions.get(str(status_kind))
                if event_definition is None:
                    continue
                available_payload = self._extract_required_payload_fields(event_definition.get("required_payload"))
                missing_fields = [
                    str(field_name)
                    for field_name in required_payload
                    if str(field_name) not in available_payload
                ]
                if missing_fields:
                    missing_for_path[str(status_kind)] = missing_fields
            if missing_for_path:
                missing[str(path)] = missing_for_path
        return missing

    def _index_event_status_kinds(self, value: Any) -> Dict[str, Mapping[str, Any]]:
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
            return {}
        indexed: Dict[str, Mapping[str, Any]] = {}
        for item in value:
            if not isinstance(item, Mapping):
                continue
            status_kind = str(item.get("status_kind") or "").strip()
            if status_kind:
                indexed[status_kind] = item
        return indexed

    def _extract_required_payload_fields(self, value: Any) -> set[str]:
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
            return set()
        return {str(item).strip() for item in value if str(item).strip()}

    def _fingerprint(self, value: Any) -> str:
        payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


_runtime_contract_snapshot_service: RuntimeContractSnapshotService | None = None


def get_runtime_contract_snapshot_service() -> RuntimeContractSnapshotService:
    global _runtime_contract_snapshot_service
    if _runtime_contract_snapshot_service is None:
        _runtime_contract_snapshot_service = RuntimeContractSnapshotService()
    return _runtime_contract_snapshot_service
