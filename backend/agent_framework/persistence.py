"""Embedded SDK persistence seam for run snapshots and continuation descriptors."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from .continuation_lifecycle import build_continuation_descriptor_lifecycle_contract
from .loader_handoff import build_durable_loader_execution_handoff_policy_contract
from .production_recovery_policy import build_production_recovery_registry_checkpoint_policy_contract
from .recovery_audit_readiness import build_recovery_audit_production_readiness_contract


EMBEDDED_WORKSPACE_STATE_CONTRACT_VERSION = "phase-ii-durable-workspace-state-contract-v1"
EMBEDDED_WORKSPACE_DURABLE_STATE_KINDS = [
    "run_snapshot",
    "event_log",
    "approval_snapshot",
    "tool_continuation_descriptor",
    "loop_continuation_descriptor",
    "artifact_ref",
    "child_executor_output",
]
EMBEDDED_WORKSPACE_RUNTIME_ONLY_STATE_KINDS = [
    "executable_continuation_callable",
    "python_function_binding",
    "temporary_stream_cursor",
    "in_process_event_iterator",
]

EMBEDDED_SDK_PERSISTENCE_INTERFACE_VERSION = "phase-ii-embedded-sdk-persistence-interface-v1"
EMBEDDED_SDK_PRODUCTION_RECOVERY_GATE_VERSION = "phase-ii-durable-workspace-production-recovery-gate-v1"
EMBEDDED_SDK_PERSISTENCE_POSTURE_MEMORY_PREVIEW = "memory_preview"
EMBEDDED_SDK_PERSISTENCE_POSTURE_DURABLE_READY = "durable_ready"
EMBEDDED_SDK_PERSISTENCE_POSTURE_DURABLE_DEGRADED = "durable_degraded"


def build_embedded_workspace_state_contract() -> Dict[str, Any]:
    return {
        "contract_version": EMBEDDED_WORKSPACE_STATE_CONTRACT_VERSION,
        "durable_state_kinds": list(EMBEDDED_WORKSPACE_DURABLE_STATE_KINDS),
        "runtime_only_state_kinds": list(EMBEDDED_WORKSPACE_RUNTIME_ONLY_STATE_KINDS),
    }


def _build_production_recovery_gate_section(
    *,
    name: str,
    ready: bool,
    evidence: Dict[str, Any] | None = None,
    missing_reason: str = "",
) -> Dict[str, Any]:
    return {
        "name": name,
        "status": "ready" if ready else "blocked",
        "ready": bool(ready),
        "missing_reason": "" if ready else str(missing_reason or "").strip(),
        "evidence": dict(evidence or {}),
    }


def build_durable_workspace_production_recovery_gate_contract(
    *,
    backend_description: Dict[str, Any] | None = None,
    descriptor_lifecycle_governed: bool = False,
    registry_binding_policy_ready: bool = False,
    checkpoint_resume_cursor_gate_ready: bool = False,
    worker_ownership_gate_ready: bool = False,
    worker_ownership_production_gate: Dict[str, Any] | None = None,
    recovery_audit_ready: bool = False,
    rollout_checklist_ready: bool = False,
    loader_execution_handoff_policy_ready: bool = False,
    production_default_enabled: bool = False,
) -> Dict[str, Any]:
    description = dict(backend_description or {})
    durable = bool(description.get("durable"))
    fallback_active = bool(description.get("fallback_active"))
    state_contract = dict(description.get("state_contract") or {})
    durable_state_kinds = list(state_contract.get("durable_state_kinds") or [])
    registry_checkpoint_policy = build_production_recovery_registry_checkpoint_policy_contract()
    ownership_gate = dict(worker_ownership_production_gate or {})
    ownership_gate_status = str(ownership_gate.get("overall_status") or "").strip()
    ownership_gate_default_enabled = bool(ownership_gate.get("production_default_enabled"))
    ownership_gate_missing_sections = (
        ownership_gate.get("missing_sections")
        if isinstance(ownership_gate.get("missing_sections"), list)
        else []
    )
    linked_worker_ownership_ready = (
        bool(worker_ownership_gate_ready)
        and ownership_gate_status == "ready"
        and ownership_gate_default_enabled
    )
    required_state = [
        "run_snapshot",
        "event_log",
        "approval_snapshot",
        "tool_continuation_descriptor",
        "loop_continuation_descriptor",
    ]
    required_state_ready = all(item in durable_state_kinds for item in required_state)
    sections = [
        _build_production_recovery_gate_section(
            name="durable_workspace_backend",
            ready=durable and not fallback_active,
            evidence={
                "backend_kind": str(description.get("backend_kind") or "").strip(),
                "backend_mode": str(description.get("backend_mode") or "").strip(),
                "durable": durable,
                "fallback_active": fallback_active,
            },
            missing_reason="durable_workspace_backend_missing_or_degraded",
        ),
        _build_production_recovery_gate_section(
            name="durable_backend_migration_rollout",
            ready=durable and not fallback_active and required_state_ready and rollout_checklist_ready,
            evidence={
                "required_state": required_state,
                "required_state_ready": required_state_ready,
                "rollout_checklist_ready": rollout_checklist_ready,
            },
            missing_reason="durable_backend_migration_rollout_incomplete",
        ),
        _build_production_recovery_gate_section(
            name="descriptor_lifecycle_governance",
            ready=descriptor_lifecycle_governed,
            evidence={
                "required_states": ["created", "bound", "ready", "stale", "resolved", "unsafe"],
                "unsafe_payloads_fail_closed": True,
                "lifecycle_contract": build_continuation_descriptor_lifecycle_contract(),
            },
            missing_reason="descriptor_lifecycle_governance_missing",
        ),
        _build_production_recovery_gate_section(
            name="registry_binding_resolution",
            ready=registry_binding_policy_ready,
            evidence={
                "requires_binding_identity": True,
                "callable_deserialization_allowed": False,
                "policy_readiness": registry_checkpoint_policy,
            },
            missing_reason="registry_binding_resolution_policy_missing",
        ),
        _build_production_recovery_gate_section(
            name="checkpoint_resume_cursor_gate",
            ready=checkpoint_resume_cursor_gate_ready,
            evidence={
                "checkpoint_required": True,
                "resume_cursor_required": True,
                "policy_readiness": registry_checkpoint_policy,
            },
            missing_reason="checkpoint_resume_cursor_gate_missing",
        ),
        _build_production_recovery_gate_section(
            name="worker_ownership_production_gate",
            ready=linked_worker_ownership_ready,
            evidence={
                "requires_worker_ownership_gate": True,
                "worker_ownership_gate_contract_version": str(
                    ownership_gate.get("contract_version") or ""
                ).strip(),
                "worker_ownership_gate_status": ownership_gate_status,
                "worker_ownership_production_default_enabled": ownership_gate_default_enabled,
                "worker_ownership_missing_sections": list(ownership_gate_missing_sections),
                "worker_ownership_next_allowed_action": str(
                    ownership_gate.get("next_allowed_action") or ""
                ).strip(),
            },
            missing_reason="worker_ownership_production_gate_missing",
        ),
        _build_production_recovery_gate_section(
            name="recovery_audit_operation_history",
            ready=recovery_audit_ready,
            evidence={
                "requires_recovery_operation_history": True,
                "audit_payload_compact": True,
                "audit_readiness": build_recovery_audit_production_readiness_contract(),
            },
            missing_reason="recovery_audit_operation_history_missing",
        ),
        _build_production_recovery_gate_section(
            name="loader_execution_handoff_policy",
            ready=loader_execution_handoff_policy_ready,
            evidence={
                "durable_loader_executes_recovery": False,
                "explicit_handoff_required": True,
                "handoff_policy": build_durable_loader_execution_handoff_policy_contract(),
            },
            missing_reason="loader_execution_handoff_policy_missing",
        ),
        _build_production_recovery_gate_section(
            name="fail_closed_default_decision",
            ready=True,
            evidence={
                "production_default_enabled": False,
                "durable_ready_is_not_run_authorization": True,
            },
        ),
    ]
    missing_sections = [
        str(section.get("name") or "").strip()
        for section in sections
        if not bool(section.get("ready"))
    ]
    overall_status = "ready" if not missing_sections else "blocked"
    return {
        "contract_version": EMBEDDED_SDK_PRODUCTION_RECOVERY_GATE_VERSION,
        "overall_status": overall_status,
        "ready": overall_status == "ready",
        "production_default_enabled": bool(production_default_enabled) and overall_status == "ready",
        "sections": sections,
        "missing_sections": missing_sections,
        "next_allowed_action": (
            "consider_explicit_production_recovery_enablement"
            if overall_status == "ready"
            else "implement_descriptor_lifecycle_ownership_audit_and_loader_handoff_policy"
        ),
        "non_goals": [
            "no_cross_process_recovery_executor",
            "no_callable_deserialization",
            "no_default_loader_execution",
            "no_durable_ready_as_run_authorization",
        ],
    }


def build_embedded_sdk_persistence_interface(
    backend_description: Dict[str, Any] | None,
    *,
    worker_ownership_production_gate: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    description = dict(backend_description or {})
    durable = bool(description.get("durable"))
    fallback_active = bool(description.get("fallback_active"))
    if durable and fallback_active:
        persistence_posture = EMBEDDED_SDK_PERSISTENCE_POSTURE_DURABLE_DEGRADED
    elif durable:
        persistence_posture = EMBEDDED_SDK_PERSISTENCE_POSTURE_DURABLE_READY
    else:
        persistence_posture = EMBEDDED_SDK_PERSISTENCE_POSTURE_MEMORY_PREVIEW
    cross_process_candidate = persistence_posture == EMBEDDED_SDK_PERSISTENCE_POSTURE_DURABLE_READY
    cross_process_block_reason = ""
    if persistence_posture == EMBEDDED_SDK_PERSISTENCE_POSTURE_MEMORY_PREVIEW:
        cross_process_block_reason = "workspace_backend_not_durable"
    elif persistence_posture == EMBEDDED_SDK_PERSISTENCE_POSTURE_DURABLE_DEGRADED:
        cross_process_block_reason = "workspace_backend_fallback_active"
    production_recovery_gate = build_durable_workspace_production_recovery_gate_contract(
        backend_description=description,
        descriptor_lifecycle_governed=True,
        registry_binding_policy_ready=True,
        checkpoint_resume_cursor_gate_ready=True,
        worker_ownership_gate_ready=False,
        worker_ownership_production_gate=worker_ownership_production_gate,
        recovery_audit_ready=True,
        rollout_checklist_ready=False,
        loader_execution_handoff_policy_ready=True,
        production_default_enabled=False,
    )
    return {
        "contract_version": EMBEDDED_SDK_PERSISTENCE_INTERFACE_VERSION,
        "persistence_posture": persistence_posture,
        "workspace_backend_kind": str(description.get("backend_kind") or "").strip(),
        "workspace_backend_mode": str(description.get("backend_mode") or "").strip(),
        "durable": durable,
        "fallback_active": fallback_active,
        "fallback_reason": str(description.get("fallback_reason") or "").strip(),
        "last_error": str(description.get("last_error") or "").strip(),
        "cross_process_candidate": cross_process_candidate,
        "cross_process_block_reason": cross_process_block_reason,
        "state_contract": dict(description.get("state_contract") or {}),
        "production_recovery_gate": production_recovery_gate,
    }


@runtime_checkable
class EmbeddedRunWorkspaceStore(Protocol):
    def save_run_snapshot(self, run_snapshot: Dict[str, Any]) -> None: ...
    def get_run_snapshot(self, run_id: str) -> Optional[Dict[str, Any]]: ...
    def save_events(self, run_id: str, events: List[Dict[str, Any]]) -> None: ...
    def get_events(self, run_id: str) -> List[Dict[str, Any]]: ...
    def save_approval_snapshot(self, approval_snapshot: Dict[str, Any]) -> None: ...
    def get_approval_snapshot(self, request_id: str) -> Optional[Dict[str, Any]]: ...
    def save_tool_continuation_descriptor(self, request_id: str, descriptor: Dict[str, Any]) -> None: ...
    def get_tool_continuation_descriptor(self, request_id: str) -> Optional[Dict[str, Any]]: ...
    def delete_tool_continuation_descriptor(self, request_id: str) -> None: ...
    def save_loop_continuation_descriptor(self, run_id: str, descriptor: Dict[str, Any]) -> None: ...
    def get_loop_continuation_descriptor(self, run_id: str) -> Optional[Dict[str, Any]]: ...
    def delete_loop_continuation_descriptor(self, run_id: str) -> None: ...
    def describe_backend(self) -> Dict[str, Any]: ...


class InMemoryEmbeddedRunWorkspaceStore:
    """Default persistence seam used until a durable store is introduced."""

    def __init__(self) -> None:
        self._runs: Dict[str, Dict[str, Any]] = {}
        self._events: Dict[str, List[Dict[str, Any]]] = {}
        self._approvals: Dict[str, Dict[str, Any]] = {}
        self._tool_continuations: Dict[str, Dict[str, Any]] = {}
        self._loop_continuations: Dict[str, Dict[str, Any]] = {}

    def save_run_snapshot(self, run_snapshot: Dict[str, Any]) -> None:
        self._runs[str(run_snapshot.get("run_id") or "").strip()] = dict(run_snapshot or {})

    def get_run_snapshot(self, run_id: str) -> Optional[Dict[str, Any]]:
        snapshot = self._runs.get(str(run_id or "").strip())
        return dict(snapshot) if snapshot is not None else None

    def save_events(self, run_id: str, events: List[Dict[str, Any]]) -> None:
        self._events[str(run_id or "").strip()] = [dict(event or {}) for event in list(events or [])]

    def get_events(self, run_id: str) -> List[Dict[str, Any]]:
        return [dict(event or {}) for event in list(self._events.get(str(run_id or "").strip(), []))]

    def save_approval_snapshot(self, approval_snapshot: Dict[str, Any]) -> None:
        self._approvals[str(approval_snapshot.get("request_id") or "").strip()] = dict(approval_snapshot or {})

    def get_approval_snapshot(self, request_id: str) -> Optional[Dict[str, Any]]:
        snapshot = self._approvals.get(str(request_id or "").strip())
        return dict(snapshot) if snapshot is not None else None

    def save_tool_continuation_descriptor(self, request_id: str, descriptor: Dict[str, Any]) -> None:
        self._tool_continuations[str(request_id or "").strip()] = dict(descriptor or {})

    def get_tool_continuation_descriptor(self, request_id: str) -> Optional[Dict[str, Any]]:
        descriptor = self._tool_continuations.get(str(request_id or "").strip())
        return dict(descriptor) if descriptor is not None else None

    def delete_tool_continuation_descriptor(self, request_id: str) -> None:
        self._tool_continuations.pop(str(request_id or "").strip(), None)

    def save_loop_continuation_descriptor(self, run_id: str, descriptor: Dict[str, Any]) -> None:
        self._loop_continuations[str(run_id or "").strip()] = dict(descriptor or {})

    def get_loop_continuation_descriptor(self, run_id: str) -> Optional[Dict[str, Any]]:
        descriptor = self._loop_continuations.get(str(run_id or "").strip())
        return dict(descriptor) if descriptor is not None else None

    def delete_loop_continuation_descriptor(self, run_id: str) -> None:
        self._loop_continuations.pop(str(run_id or "").strip(), None)

    def describe_backend(self) -> Dict[str, Any]:
        return {
            "backend_kind": "in_memory",
            "durable": False,
            "backend_mode": "memory_only",
            "operation_fallback_allowed": False,
            "fallback_active": False,
            "fallback_reason": "",
            "last_error": "",
            "state_contract": build_embedded_workspace_state_contract(),
        }
