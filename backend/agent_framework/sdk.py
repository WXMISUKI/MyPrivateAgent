"""Embedded SDK boundary for vertical-agent integrations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, Mapping
from uuid import uuid4

from .artifacts import ArtifactStore
from .adapters import get_embedded_workspace_store
from .child_executor_backends import (
    build_child_executor_backend_registry_contract,
    resolve_child_executor_backend,
)
from .child_executor_dispatcher import (
    build_child_executor_dispatch_attempt_handoff_contract,
    build_child_executor_dispatcher_contract,
)
from .child_executor_sandbox_worker_backend import (
    build_child_executor_sandbox_backend_binding_contract,
    find_unsafe_sandbox_payload_keys,
)
from .continuation_registry import EmbeddedContinuationRegistry, get_embedded_continuation_registry
from .continuations import (
    CONTINUATION_RECOVERY_REASON_DESCRIPTOR_MISSING,
    CONTINUATION_RECOVERY_REASON_MISSING_REGISTERED_BINDING,
    CONTINUATION_RECOVERY_REASON_MISSING_EXECUTABLE_CONTINUATION,
    CONTINUATION_RECOVERY_REASON_ALREADY_RESOLVED,
    CONTINUATION_RECOVERY_REASON_DENIED,
    CONTINUATION_RECOVERY_REASON_DESCRIPTOR_CORRUPTED,
    CONTINUATION_RECOVERY_REASON_READY_IN_PROCESS,
    CONTINUATION_RECOVERY_REASON_READY_VIA_REGISTRY,
    CONTINUATION_RECOVERY_REASON_WORKSPACE_BACKEND_FALLBACK_ACTIVE,
    CONTINUATION_RECOVERY_REASON_WORKSPACE_BACKEND_NOT_DURABLE,
    CONTINUATION_RECOVERY_STATUS_RECOVERABLE,
    CONTINUATION_RECOVERY_STATUS_UNRECOVERABLE,
    build_continuation_recovery,
    build_loop_continuation_descriptor,
    build_tool_approval_continuation_descriptor,
)
from .durable_recovery_loader import (
    DurableRecoveryLoader,
    build_durable_recovery_loader_contract,
)
from .events import AgentEventFactory, AgentEventType
from .persistence import EmbeddedRunWorkspaceStore, build_embedded_sdk_persistence_interface
from .recovery_operations import (
    build_recovery_operation_contract,
    build_recovery_operation_record,
    build_recovery_retry_evidence,
    recovery_entrypoint_for_continuation_kind,
)
from .recovery_retry_scheduler import build_recovery_retry_scheduler_contract
from .runtime_dependencies import EmbeddedRuntimeDependencies, get_default_embedded_runtime_dependencies
from .tools import ToolRenderMode, ToolSpec
from .execution_loop import (
    ExecutionLoopController,
    ExecutionLoopStep,
    ExecutionToolResult,
    FallbackCallable,
    ReflectionCallable,
    ReviewCallable,
    ToolExecutorCallable,
    ToolPolicyCallable,
)
from .runtime import AgentRunContext, AgentRunKind, AgentState
from .worker_ownership import build_worker_ownership_explicit_auto_claim_enablement_gate_contract

try:
    from services.approval_engine_service import get_approval_engine_service
    from services.query_control_event_mapper_service import get_query_control_event_mapper_service
    from services.query_control_timeline_service import get_query_control_timeline_service
    from services.scheduler_runtime_entities import ApprovalRequestState
    from services.tool_runtime_service import get_tool_runtime_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.approval_engine_service import get_approval_engine_service
    from backend.services.query_control_event_mapper_service import get_query_control_event_mapper_service
    from backend.services.query_control_timeline_service import get_query_control_timeline_service
    from backend.services.scheduler_runtime_entities import ApprovalRequestState
    from backend.services.tool_runtime_service import get_tool_runtime_service


EMBEDDED_SDK_METHODS = [
    {
        "method": "create_run",
        "description": "Create an AgentRun through the runtime service or embedded core.",
        "required_capabilities": ["runtime.run_create"],
        "stability": "preview",
    },
    {
        "method": "stream_events",
        "description": "Stream AgentEvent records for a run.",
        "required_capabilities": ["runtime.event_stream"],
        "stability": "preview",
    },
    {
        "method": "list_continuation_bindings",
        "description": "Return a read-only catalog of registered continuation bindings.",
        "required_capabilities": ["runtime.continuation_binding_catalog"],
        "stability": "preview",
    },
    {
        "method": "probe_run_recovery",
        "description": "Probe whether persisted continuation descriptors are recoverable in the current process.",
        "required_capabilities": ["runtime.run_recovery_probe"],
        "stability": "preview",
    },
    {
        "method": "register_tool",
        "description": "Register a ToolSpec-backed tool for embedded use.",
        "required_capabilities": ["runtime.tool_register"],
        "stability": "preview",
    },
    {
        "method": "submit_approval",
        "description": "Resolve an ApprovalRequest created by governance policy.",
        "required_capabilities": ["runtime.approval_submit"],
        "stability": "preview",
    },
    {
        "method": "resume_run",
        "description": "Resume a paused or waiting AgentRun.",
        "required_capabilities": ["runtime.run_resume"],
        "stability": "preview",
    },
    {
        "method": "delegate_run",
        "description": "Create a child AgentRun under an existing parent run.",
        "required_capabilities": ["runtime.child_run_create"],
        "stability": "preview",
    },
    {
        "method": "evaluate_child_executor_preflight",
        "description": "Evaluate whether a delegated child payload is ready for a future executor binding path.",
        "required_capabilities": ["runtime.child_run_preflight"],
        "stability": "preview",
    },
    {
        "method": "evaluate_child_executor_gate",
        "description": "Run the formal execution gate for a delegated child payload without creating a child run.",
        "required_capabilities": ["runtime.child_run_gate"],
        "stability": "preview",
    },
    {
        "method": "evaluate_child_executor_routing",
        "description": "Build a no-execute routing decision for a delegated child payload after the execution gate.",
        "required_capabilities": ["runtime.child_run_route"],
        "stability": "preview",
    },
    {
        "method": "bind_child_executor_routing",
        "description": "Bind a routed child executor candidate into a record-only handoff contract without executing it.",
        "required_capabilities": ["runtime.child_run_bind"],
        "stability": "preview",
    },
    {
        "method": "execute_bound_child_executor_stub",
        "description": "Record a no-execute executor stub result from a bound child executor handoff contract.",
        "required_capabilities": ["runtime.child_run_stub"],
        "stability": "preview",
    },
    {
        "method": "execute_bound_child_executor",
        "description": "Run the minimal embedded_sdk_worker executor skeleton for a bound child executor handoff contract.",
        "required_capabilities": ["runtime.child_run_execute"],
        "stability": "preview",
    },
    {
        "method": "merge_child_executor_output",
        "description": "Merge a child executor output envelope into the parent run as a minimal merge summary.",
        "required_capabilities": ["runtime.child_run_merge"],
        "stability": "preview",
    },
    {
        "method": "list_child_executor_outputs",
        "description": "Replay child executor execution and merge records recorded on a parent run.",
        "required_capabilities": ["runtime.child_run_replay"],
        "stability": "preview",
    },
    {
        "method": "summarize_child_executor_outputs",
        "description": "Summarize replayed child executor outputs into a compact artifact summary for consumption surfaces.",
        "required_capabilities": ["runtime.child_run_summary"],
        "stability": "preview",
    },
    {
        "method": "summarize_child_executor_merged_semantics",
        "description": "Return a dedicated parent-side merged semantics read model for child executor outputs.",
        "required_capabilities": ["runtime.child_run_merged_semantics"],
        "stability": "preview",
    },
    {
        "method": "create_artifact",
        "description": "Attach an in-memory artifact reference to an AgentRun.",
        "required_capabilities": ["runtime.artifact_create"],
        "stability": "preview",
    },
    {
        "method": "list_artifacts",
        "description": "Replay artifact references attached to an AgentRun.",
        "required_capabilities": ["runtime.artifact_read"],
        "stability": "preview",
    },
    {
        "method": "execute_run",
        "description": "Drive an AgentRun through the minimal harness execution loop.",
        "required_capabilities": ["runtime.loop_execute"],
        "stability": "preview",
    },
]

CHILD_EXECUTOR_INTENT_CATALOG_VERSION = "phase-ii-child-intent-catalog-v1"
CHILD_EXECUTOR_INTENT_RISK_REVIEW = "risk_review"
CHILD_EXECUTOR_INTENT_PLANNING = "planning"
CHILD_EXECUTOR_INTENT_GENERAL_ANALYSIS = "general_analysis"
CHILD_EXECUTOR_DEFAULT_INTENT = CHILD_EXECUTOR_INTENT_GENERAL_ANALYSIS
CHILD_EXECUTOR_SUPPORTED_INTENTS = (
    CHILD_EXECUTOR_INTENT_RISK_REVIEW,
    CHILD_EXECUTOR_INTENT_PLANNING,
    CHILD_EXECUTOR_INTENT_GENERAL_ANALYSIS,
)
SDK_APPROVAL_LIFECYCLE_TRACE_STATUS_KINDS = {
    "approval_resolved",
    "approval_replayed",
    "approval_ignored",
    "recovery_failed_closed",
}

EMBEDDED_SDK_EVENT_STATUS_KINDS = [
    {
        "status_kind": "run_created",
        "event_type": "status",
        "category": "run",
        "stability": "preview",
        "required_payload": ["run"],
    },
    {
        "status_kind": "approval_created",
        "event_type": "status",
        "category": "approval",
        "stability": "preview",
        "required_payload": ["approval_request_id", "approval_request"],
    },
    {
        "status_kind": "approval_resolved",
        "event_type": "status",
        "category": "approval",
        "stability": "preview",
        "required_payload": ["approval_request_id", "approval_request", "decision"],
    },
    {
        "status_kind": "approval_replayed",
        "event_type": "status",
        "category": "approval",
        "stability": "preview",
        "required_payload": ["approval_request_id", "approval_request", "original_decision", "attempted_decision"],
    },
    {
        "status_kind": "approval_ignored",
        "event_type": "status",
        "category": "approval",
        "stability": "preview",
        "required_payload": ["approval_request_id", "approval_request", "original_decision", "attempted_decision"],
    },
    {
        "status_kind": "loop_continuation_registered",
        "event_type": "status",
        "category": "continuation",
        "stability": "preview",
        "required_payload": ["loop_continuation"],
    },
    {
        "status_kind": "loop_continuation_consumed",
        "event_type": "status",
        "category": "continuation",
        "stability": "preview",
        "required_payload": ["loop_continuation"],
    },
    {
        "status_kind": "loop_continuation_discarded",
        "event_type": "status",
        "category": "continuation",
        "stability": "preview",
        "required_payload": ["loop_continuation"],
    },
    {
        "status_kind": "recovery_probe_evaluated",
        "event_type": "status",
        "category": "recovery",
        "stability": "preview",
        "required_payload": ["recovery"],
    },
    {
        "status_kind": "recovery_failed_closed",
        "event_type": "status",
        "category": "recovery",
        "stability": "preview",
        "required_payload": ["recovery"],
    },
    {
        "status_kind": "execution_loop_step",
        "event_type": "status",
        "category": "execution_loop",
        "stability": "preview",
        "required_payload": ["loop_step", "state"],
    },
    {
        "status_kind": "execution_loop_done",
        "event_type": "done",
        "category": "execution_loop",
        "stability": "preview",
        "required_payload": ["run", "completed_steps"],
    },
    {
        "status_kind": "execution_loop_reviewed",
        "event_type": "status",
        "category": "execution_loop_review",
        "stability": "preview",
        "required_payload": ["review", "loop_step"],
    },
    {
        "status_kind": "execution_loop_review_rejected",
        "event_type": "error",
        "category": "execution_loop_review",
        "stability": "preview",
        "required_payload": ["review", "loop_step"],
    },
    {
        "status_kind": "execution_loop_fallback_applied",
        "event_type": "status",
        "category": "execution_loop_fallback",
        "stability": "preview",
        "required_payload": ["fallback", "error", "loop_step"],
    },
    {
        "status_kind": "execution_loop_failed",
        "event_type": "error",
        "category": "execution_loop_fallback",
        "stability": "preview",
        "required_payload": ["fallback", "error", "loop_step"],
    },
    {
        "status_kind": "tool_approval_continued",
        "event_type": "status",
        "category": "tool",
        "stability": "preview",
        "required_payload": ["approval_request_id", "tool_decision"],
    },
]

EMBEDDED_SDK_VOLATILE_RUNTIME_STATE = [
    "_runs",
    "_events",
    "_approvals",
    "_artifacts",
    "_tool_continuations",
    "_loop_continuations",
]

EMBEDDED_SDK_PERSISTENCE_SEAMS = [
    "run_workspace_snapshot",
    "run_event_log",
    "approval_snapshot",
    "tool_approval_continuation_descriptor",
    "loop_continuation_descriptor",
    "artifact_store_seam",
]

EMBEDDED_SDK_RECOVERY_ENTRYPOINTS = [
    {
        "method": "probe_run_recovery",
        "recovery_scope": "continuation_descriptor_recoverability_probe",
        "cross_process_ready": False,
        "requires_durable_workspace": False,
        "requires_registry_bindings": False,
    },
    {
        "method": "submit_approval",
        "mode": "approved",
        "recovery_scope": "approved_tool_continuation_resume",
        "cross_process_ready": True,
        "requires_durable_workspace": True,
        "requires_registry_bindings": True,
    },
    {
        "method": "resume_run",
        "mode": "default",
        "recovery_scope": "observing_to_generating_state_resume",
        "cross_process_ready": False,
        "requires_durable_workspace": False,
        "requires_registry_bindings": False,
    },
    {
        "method": "resume_run",
        "mode": "continue_loop",
        "recovery_scope": "observing_to_done_loop_continuation",
        "cross_process_ready": True,
        "requires_durable_workspace": True,
        "requires_registry_bindings": True,
    },
]

EMBEDDED_CHILD_EXECUTOR_PREFLIGHT_REFERENCE_SLICES = [
    {
        "source": "learn-claude-code",
        "role": "conceptual_reference",
        "slices": [
            "docs/zh/s11-error-recovery.md",
            "docs/zh/s13a-runtime-task-model.md",
            "docs/zh/s15-agent-teams.md",
            "docs/zh/team-task-lane-model.md",
        ],
    },
    {
        "source": "claude-code",
        "role": "control_plane_reference",
        "slices": [
            "src/utils/swarm/backends/InProcessBackend.ts",
            "src/utils/swarm/inProcessRunner.ts",
            "src/utils/swarm/permissionSync.ts",
            "src/utils/swarm/reconnection.ts",
            "src/utils/swarm/backends/registry.ts",
        ],
    },
]

CHILD_EXECUTOR_PREFLIGHT_REQUIREMENTS = [
    {
        "requirement": "child_run_recovery_boundary_defined",
        "description": "Child run recovery boundary is explicitly backed by a workspace persistence seam.",
    },
    {
        "requirement": "child_context_budget_defined",
        "description": "Child execution context budget is explicitly declared before promotion.",
    },
    {
        "requirement": "child_result_merge_semantics_defined",
        "description": "Child result merge semantics are explicitly declared before promotion.",
    },
    {
        "requirement": "worker_runtime_backend_selected",
        "description": "Worker runtime backend is explicitly selected before promotion.",
    },
]


def _select_first_evidence(*candidates: tuple[Any, str]) -> tuple[bool, str | None, Any | None]:
    for value, path in candidates:
        if value is None:
            continue
        if isinstance(value, str):
            normalized = value.strip()
            if normalized:
                return True, path, normalized
            continue
        if isinstance(value, (list, tuple, dict)) and len(value) == 0:
            continue
        return True, path, value
    return False, None, None


def _is_truthy_opt_in(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on", "ready", "enabled"}
    return bool(value)


def _coerce_positive_int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, float):
        return int(value) if value > 0 and value.is_integer() else None
    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return None
        try:
            parsed = int(normalized)
        except ValueError:
            return None
        return parsed if parsed > 0 else None
    return None


def _first_positive_int(mapping: Dict[str, Any], *keys: str) -> int | None:
    for key in keys:
        value = _coerce_positive_int(mapping.get(key))
        if value is not None:
            return value
    return None


def build_child_executor_context_budget_policy_contract(
    *,
    payload: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    normalized_payload = dict(payload or {})
    metadata = dict(normalized_payload.get("metadata") or {})
    payload_scheduler_policy = dict(normalized_payload.get("scheduler_policy") or {})
    metadata_scheduler_policy = dict(metadata.get("scheduler_policy") or {})

    budget_present, budget_path, raw_budget = _select_first_evidence(
        (normalized_payload.get("child_context_budget"), "payload.child_context_budget"),
        (metadata.get("child_context_budget"), "metadata.child_context_budget"),
        (normalized_payload.get("context_budget"), "payload.context_budget"),
        (metadata.get("context_budget"), "metadata.context_budget"),
        (payload_scheduler_policy.get("timeout_seconds"), "payload.scheduler_policy.timeout_seconds"),
        (metadata_scheduler_policy.get("timeout_seconds"), "metadata.scheduler_policy.timeout_seconds"),
        (payload_scheduler_policy.get("max_turns"), "payload.scheduler_policy.max_turns"),
        (metadata_scheduler_policy.get("max_turns"), "metadata.scheduler_policy.max_turns"),
    )

    max_turns = None
    timeout_seconds = None
    token_budget = None
    artifact_budget = None
    if isinstance(raw_budget, dict):
        max_turns = _first_positive_int(raw_budget, "max_turns", "turns", "max_iterations")
        timeout_seconds = _first_positive_int(raw_budget, "timeout_seconds", "timeout", "max_seconds")
        token_budget = _first_positive_int(raw_budget, "token_budget", "max_tokens", "tokens")
        artifact_budget = _first_positive_int(raw_budget, "artifact_budget", "max_artifacts", "artifacts")
    elif budget_present:
        value = _coerce_positive_int(raw_budget)
        if budget_path and budget_path.endswith("timeout_seconds"):
            timeout_seconds = value
        elif budget_path and budget_path.endswith("max_turns"):
            max_turns = value
        else:
            max_turns = value

    bounded_limit_present = any(
        item is not None
        for item in (max_turns, timeout_seconds, token_budget, artifact_budget)
    )
    missing_sections = []
    if not budget_present or not budget_path:
        missing_sections.append("budget_source")
    if not bounded_limit_present:
        missing_sections.append("bounded_budget_limit")
    ready = not missing_sections
    return {
        "contract_version": "phase-ii-child-executor-context-budget-policy-v1",
        "overall_status": "ready" if ready else "blocked",
        "ready": ready,
        "budget_source": str(budget_path or ""),
        "raw_budget_present": bool(budget_present),
        "max_turns": max_turns,
        "timeout_seconds": timeout_seconds,
        "token_budget": token_budget,
        "artifact_budget": artifact_budget,
        "missing_sections": missing_sections,
        "fail_closed_reason": "" if ready else "child_executor_context_budget_policy_incomplete",
        "next_allowed_action": (
            "continue_child_executor_prerequisite_evaluation"
            if ready
            else "declare_bounded_child_context_budget"
        ),
        "non_goals": [
            "token_accounting_enforcement",
            "scheduler_preemption",
            "worker_timeout_cancellation",
            "real_child_executor_dispatch",
        ],
    }


SUPPORTED_CHILD_RESULT_MERGE_STRATEGIES = {"append_summary", "role_sections"}


def _normalize_child_result_merge_strategy(raw_value: Any) -> str:
    if isinstance(raw_value, dict):
        return str(
            raw_value.get("strategy")
            or raw_value.get("merge_strategy")
            or raw_value.get("mode")
            or ""
        ).strip()
    return str(raw_value or "").strip()


def build_child_result_merge_handoff_contract(
    *,
    payload: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    normalized_payload = dict(payload or {})
    metadata = dict(normalized_payload.get("metadata") or {})
    merge_present, merge_path, raw_merge = _select_first_evidence(
        (normalized_payload.get("merge_strategy"), "payload.merge_strategy"),
        (metadata.get("merge_strategy"), "metadata.merge_strategy"),
        (normalized_payload.get("child_result_merge_strategy"), "payload.child_result_merge_strategy"),
        (metadata.get("child_result_merge_strategy"), "metadata.child_result_merge_strategy"),
        (normalized_payload.get("result_merge_policy"), "payload.result_merge_policy"),
        (metadata.get("result_merge_policy"), "metadata.result_merge_policy"),
    )
    merge_strategy = _normalize_child_result_merge_strategy(raw_merge)
    supported_merge_strategy = merge_strategy in SUPPORTED_CHILD_RESULT_MERGE_STRATEGIES
    intent_policy_ready = supported_merge_strategy
    artifact_envelope_required = True
    section_handoff_required = True
    parent_metadata_update_supported = True
    replay_compatible = True
    missing_sections = []
    if not merge_present or not merge_path:
        missing_sections.append("merge_source")
    if not merge_strategy:
        missing_sections.append("merge_strategy")
    elif not supported_merge_strategy:
        missing_sections.append("supported_merge_strategy")
    if not intent_policy_ready:
        missing_sections.append("intent_policy")
    ready = not missing_sections
    return {
        "contract_version": "phase-ii-child-result-merge-handoff-v1",
        "overall_status": "ready" if ready else "blocked",
        "ready": ready,
        "merge_source": str(merge_path or ""),
        "raw_merge_present": bool(merge_present),
        "merge_strategy": merge_strategy,
        "supported_merge_strategies": sorted(SUPPORTED_CHILD_RESULT_MERGE_STRATEGIES),
        "supported_merge_strategy": supported_merge_strategy,
        "intent_policy_ready": intent_policy_ready,
        "artifact_envelope_required": artifact_envelope_required,
        "section_handoff_required": section_handoff_required,
        "parent_metadata_update_supported": parent_metadata_update_supported,
        "replay_compatible": replay_compatible,
        "missing_sections": missing_sections,
        "fail_closed_reason": "" if ready else "child_result_merge_handoff_incomplete",
        "next_allowed_action": (
            "continue_child_executor_prerequisite_evaluation"
            if ready
            else "declare_supported_child_result_merge_strategy"
        ),
        "non_goals": [
            "parent_merge_execution",
            "remote_worker_result_streaming",
            "durable_merge_replay_execution",
            "real_child_executor_dispatch",
        ],
    }


def _build_child_executor_explicit_binding_evidence(
    *,
    payload: Dict[str, Any] | None = None,
    worker_runtime_backend: str = "",
) -> Dict[str, Any]:
    normalized_payload = dict(payload or {})
    metadata = dict(normalized_payload.get("metadata") or {})
    opt_in_present, source_path, raw_value = _select_first_evidence(
        (normalized_payload.get("explicit_executor_binding_opt_in"), "payload.explicit_executor_binding_opt_in"),
        (metadata.get("explicit_executor_binding_opt_in"), "metadata.explicit_executor_binding_opt_in"),
        (normalized_payload.get("executor_binding_opt_in"), "payload.executor_binding_opt_in"),
        (metadata.get("executor_binding_opt_in"), "metadata.executor_binding_opt_in"),
    )
    ready = opt_in_present and _is_truthy_opt_in(raw_value)
    selected_backend = str(
        worker_runtime_backend
        or normalized_payload.get("worker_runtime_backend")
        or metadata.get("worker_runtime_backend")
        or normalized_payload.get("execution_backend")
        or metadata.get("execution_backend")
        or ""
    ).strip()
    backend_evidence = resolve_child_executor_backend(selected_backend)
    adapter_kind = str(backend_evidence.get("adapter_kind") or "").strip()
    missing_requirements = [] if ready else ["explicit_executor_binding_opt_in"]
    return {
        "contract_version": "phase-ii-child-executor-explicit-binding-v1",
        "binding_status": "ready" if ready else "blocked",
        "ready": ready,
        "binding_source": str(source_path or ""),
        "raw_opt_in_present": opt_in_present,
        "selected_backend": selected_backend,
        "backend_id": str(backend_evidence.get("backend_id") or selected_backend),
        "adapter_kind": adapter_kind,
        "missing_requirements": missing_requirements,
        "blockers": list(missing_requirements),
        "will_execute": False,
        "will_dispatch": False,
        "non_goals": [
            "default_worker_enablement",
            "worker_process_start",
            "queue_or_sandbox_runtime_start",
            "remote_executor_invocation",
        ],
    }


def _build_child_executor_requirement_checks(
    *,
    payload: Dict[str, Any] | None = None,
    workspace_store: EmbeddedRunWorkspaceStore | None = None,
) -> list[Dict[str, Any]]:
    normalized_payload = dict(payload or {})
    metadata = dict(normalized_payload.get("metadata") or {})
    checks = []
    recovery_ok = workspace_store is not None
    checks.append({
        "requirement": "child_run_recovery_boundary_defined",
        "satisfied": recovery_ok,
        "source_path": "sdk.workspace_store" if recovery_ok else "",
        "evidence": type(workspace_store).__name__ if recovery_ok else None,
        "summary": (
            "workspace persistence seam available for child run recovery"
            if recovery_ok
            else "workspace persistence seam not configured"
        ),
    })

    budget_policy = build_child_executor_context_budget_policy_contract(payload=normalized_payload)
    budget_ok = bool(budget_policy.get("ready"))
    budget_path = str(budget_policy.get("budget_source") or "")
    checks.append({
        "requirement": "child_context_budget_defined",
        "satisfied": budget_ok,
        "source_path": budget_path,
        "evidence": budget_policy,
        "blockers": list(budget_policy.get("missing_sections") or []),
        "summary": (
            f"child context budget defined via {budget_path}"
            if budget_ok and budget_path
            else "child context budget policy is incomplete"
        ),
    })

    merge_handoff = build_child_result_merge_handoff_contract(payload=normalized_payload)
    merge_ok = bool(merge_handoff.get("ready"))
    merge_path = str(merge_handoff.get("merge_source") or "")
    checks.append({
        "requirement": "child_result_merge_semantics_defined",
        "satisfied": merge_ok,
        "source_path": merge_path,
        "evidence": merge_handoff,
        "blockers": list(merge_handoff.get("missing_sections") or []),
        "summary": (
            f"child result merge semantics defined via {merge_path}"
            if merge_ok and merge_path
            else "child result merge handoff is incomplete"
        ),
    })

    backend_ok, backend_path, backend_value = _select_first_evidence(
        (normalized_payload.get("worker_runtime_backend"), "payload.worker_runtime_backend"),
        (metadata.get("worker_runtime_backend"), "metadata.worker_runtime_backend"),
        (normalized_payload.get("execution_backend"), "payload.execution_backend"),
        (metadata.get("execution_backend"), "metadata.execution_backend"),
        (normalized_payload.get("execution_mode"), "payload.execution_mode"),
        (metadata.get("execution_mode"), "metadata.execution_mode"),
    )
    backend_registry_evidence = resolve_child_executor_backend(str(backend_value or ""))
    backend_ready = bool(backend_ok) and bool(backend_registry_evidence.get("known"))
    backend_blockers = [
        str(item).strip()
        for item in (backend_registry_evidence.get("blockers") or [])
        if str(item or "").strip()
    ] if not backend_ready else []
    checks.append({
        "requirement": "worker_runtime_backend_selected",
        "satisfied": backend_ready,
        "source_path": backend_path or "",
        "evidence": {
            "selected_backend": backend_value,
            "backend_registry": backend_registry_evidence,
        },
        "blockers": backend_blockers,
        "summary": (
            f"worker runtime backend known via {backend_path}"
            if backend_ready and backend_path
            else f"worker runtime backend unknown via {backend_path}"
            if backend_ok and backend_path
            else "worker runtime backend not selected"
        ),
    })
    explicit_binding = _build_child_executor_explicit_binding_evidence(
        payload=normalized_payload,
        worker_runtime_backend=str(backend_value or ""),
    )
    checks.append({
        "requirement": "explicit_executor_binding_opt_in",
        "satisfied": bool(explicit_binding.get("ready")),
        "source_path": str(explicit_binding.get("binding_source") or ""),
        "evidence": explicit_binding,
        "blockers": list(explicit_binding.get("blockers") or []),
        "summary": (
            f"explicit executor binding opt-in provided via {explicit_binding.get('binding_source')}"
            if explicit_binding.get("ready") and explicit_binding.get("binding_source")
            else "explicit executor binding opt-in not provided"
        ),
    })
    return checks


def build_child_executor_preflight_contract(
    *,
    payload: Dict[str, Any] | None = None,
    workspace_store: EmbeddedRunWorkspaceStore | None = None,
) -> Dict[str, Any]:
    normalized_payload = dict(payload or {})
    metadata = dict(normalized_payload.get("metadata") or {})
    input_preview = str(normalized_payload.get("input") or metadata.get("input") or "").strip()
    merge_strategy = str(
        normalized_payload.get("merge_strategy")
        or metadata.get("merge_strategy")
        or normalized_payload.get("child_result_merge_strategy")
        or metadata.get("child_result_merge_strategy")
        or ""
    ).strip()
    worker_runtime_backend = str(
        normalized_payload.get("worker_runtime_backend")
        or metadata.get("worker_runtime_backend")
        or normalized_payload.get("execution_backend")
        or metadata.get("execution_backend")
        or ""
    ).strip()
    requirement_checks = _build_child_executor_requirement_checks(
        payload=normalized_payload,
        workspace_store=workspace_store,
    )
    promotion_ready = all(bool(item.get("satisfied")) for item in requirement_checks)
    missing_requirements = [
        str(item.get("requirement") or "").strip()
        for item in requirement_checks
        if not bool(item.get("satisfied"))
    ]
    return {
        "contract_version": "phase-ii-child-executor-preflight-v1",
        "status": "promotion_candidate" if promotion_ready else "relationship_only",
        "real_child_executor_ready": False,
        "promotion_ready": promotion_ready,
        "executor_binding_status": "ready" if promotion_ready else "blocked",
        "executor_binding_blockers": list(missing_requirements),
        "recommended_next_step": "wire_executor_backend" if promotion_ready else "keep_relationship_only",
        "input_preview": input_preview,
        "agent_name": str(metadata.get("agent_name") or "").strip(),
        "merge_strategy": merge_strategy,
        "worker_runtime_backend": worker_runtime_backend,
        "current_scope": [
            "create_child_run_relationship",
            "inherit_parent_run_identity_defaults",
            "persist_child_run_snapshot",
            "emit_child_run_created_event",
        ],
        "promotion_requirements": [
            "child_run_recovery_boundary_defined",
            "child_context_budget_defined",
            "child_result_merge_semantics_defined",
            "worker_runtime_backend_selected",
            "explicit_executor_binding_opt_in",
        ],
        "non_goals": [
            "real_child_executor_dispatch",
            "multi_process_recovery",
            "parallel_worker_budget_enforcement",
        ],
        "backend_registry": build_child_executor_backend_registry_contract(),
        "child_executor_context_budget_policy": next(
            (
                dict(item.get("evidence") or {})
                for item in requirement_checks
                if str(item.get("requirement") or "").strip() == "child_context_budget_defined"
                and isinstance(item.get("evidence"), dict)
            ),
            build_child_executor_context_budget_policy_contract(payload=normalized_payload),
        ),
        "child_result_merge_handoff_contract": next(
            (
                dict(item.get("evidence") or {})
                for item in requirement_checks
                if str(item.get("requirement") or "").strip() == "child_result_merge_semantics_defined"
                and isinstance(item.get("evidence"), dict)
            ),
            build_child_result_merge_handoff_contract(payload=normalized_payload),
        ),
        "requirement_checks": requirement_checks,
        "missing_requirements": missing_requirements,
        "approved_reference_slices": [dict(item) for item in EMBEDDED_CHILD_EXECUTOR_PREFLIGHT_REFERENCE_SLICES],
    }


def build_child_executor_gate_contract(
    *,
    preflight: Dict[str, Any],
) -> Dict[str, Any]:
    normalized_preflight = dict(preflight or {})
    promotion_ready = bool(normalized_preflight.get("promotion_ready"))
    gate_status = "passed" if promotion_ready else "blocked"
    executor_path = "embedded_sdk_worker_candidate" if promotion_ready else ""
    failure_reason = "" if promotion_ready else "child_executor_preflight_blocked"
    blockers = [
        str(item).strip()
        for item in (normalized_preflight.get("executor_binding_blockers") or [])
        if str(item).strip()
    ]
    contract = {
        "contract_version": "phase-ii-child-executor-gate-v1",
        "gate_status": gate_status,
        "allowed": promotion_ready,
        "failure_reason": failure_reason,
        "executor_path": executor_path,
        "recommended_next_step": (
            "bind_embedded_sdk_worker_executor"
            if promotion_ready
            else str(normalized_preflight.get("recommended_next_step") or "keep_relationship_only").strip()
        ),
        "blockers": blockers,
        "checked_at": _utc_now(),
        "preflight": normalized_preflight,
    }
    contract["child_executor_execution_prerequisites"] = build_child_executor_execution_prerequisites_contract(
        preflight=normalized_preflight,
        gate=contract,
    )
    return contract


def build_child_executor_execution_prerequisites_contract(
    *,
    preflight: Dict[str, Any],
    gate: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    normalized_preflight = dict(preflight or {})
    normalized_gate = dict(gate or {})
    requirement_checks = [
        dict(item)
        for item in (normalized_preflight.get("requirement_checks") or [])
        if isinstance(item, dict)
    ]
    requirement_entries = []
    missing_requirements = []
    for item in requirement_checks:
        requirement = str(item.get("requirement") or "").strip()
        if not requirement:
            continue
        ready = bool(item.get("satisfied"))
        if not ready:
            missing_requirements.append(requirement)
        requirement_entries.append({
            "requirement": requirement,
            "status": "ready" if ready else "blocked",
            "evidence": item.get("evidence"),
            "source_path": str(item.get("source_path") or "").strip(),
            "summary": str(item.get("summary") or "").strip(),
            "blocker": "" if ready else requirement,
        })

    backend_check = next(
        (
            item
            for item in requirement_checks
            if str(item.get("requirement") or "").strip() == "worker_runtime_backend_selected"
        ),
        {},
    )
    backend_evidence = backend_check.get("evidence") if isinstance(backend_check, dict) else {}
    backend_registry_evidence = (
        dict(backend_evidence.get("backend_registry") or {})
        if isinstance(backend_evidence, dict)
        else {}
    )
    explicit_binding_check = next(
        (
            item
            for item in requirement_checks
            if str(item.get("requirement") or "").strip() == "explicit_executor_binding_opt_in"
        ),
        {},
    )
    explicit_binding_evidence = (
        dict(explicit_binding_check.get("evidence") or {})
        if isinstance(explicit_binding_check, dict)
        else {}
    )
    budget_check = next(
        (
            item
            for item in requirement_checks
            if str(item.get("requirement") or "").strip() == "child_context_budget_defined"
        ),
        {},
    )
    context_budget_policy = (
        dict(budget_check.get("evidence") or {})
        if isinstance(budget_check, dict)
        else {}
    )
    merge_check = next(
        (
            item
            for item in requirement_checks
            if str(item.get("requirement") or "").strip() == "child_result_merge_semantics_defined"
        ),
        {},
    )
    merge_handoff = (
        dict(merge_check.get("evidence") or {})
        if isinstance(merge_check, dict)
        else {}
    )
    backend_dispatch_ready = bool(backend_registry_evidence.get("dispatch_ready"))
    if not backend_dispatch_ready:
        missing_requirements.append("worker_backend_dispatch_ready")
    requirement_entries.append({
        "requirement": "worker_backend_dispatch_ready",
        "status": "ready" if backend_dispatch_ready else "blocked",
        "evidence": backend_registry_evidence,
        "source_path": "child_executor_backend_registry.dispatch_ready",
        "summary": (
            "worker backend is dispatch ready"
            if backend_dispatch_ready
            else "worker backend is not dispatch ready"
        ),
        "blocker": "" if backend_dispatch_ready else "worker_backend_dispatch_ready",
    })

    promotion_allowed = bool(normalized_gate.get("allowed")) if normalized_gate else bool(normalized_preflight.get("promotion_ready"))
    if not promotion_allowed:
        missing_requirements.append("promotion_gate_allowed")
    requirement_entries.append({
        "requirement": "promotion_gate_allowed",
        "status": "ready" if promotion_allowed else "blocked",
        "evidence": {
            "gate_status": str(normalized_gate.get("gate_status") or "").strip(),
            "failure_reason": str(normalized_gate.get("failure_reason") or "").strip(),
            "executor_path": str(normalized_gate.get("executor_path") or "").strip(),
        },
        "source_path": "child_executor_promotion_gate.allowed",
        "summary": "promotion gate allows executor handoff" if promotion_allowed else "promotion gate blocks executor handoff",
        "blocker": "" if promotion_allowed else "promotion_gate_allowed",
    })
    deduped_missing_requirements = list(dict.fromkeys(item for item in missing_requirements if item))
    ready = not deduped_missing_requirements and bool(requirement_entries)
    return {
        "contract_version": "phase-ii-child-executor-execution-prerequisites-v1",
        "overall_status": "ready" if ready else "blocked",
        "ready": ready,
        "relationship_seam_preserved": not ready,
        "requirements": requirement_entries,
        "requirement_count": len(requirement_entries),
        "missing_requirements": deduped_missing_requirements,
        "missing_requirement_count": len(deduped_missing_requirements),
        "recommended_next_step": (
            "bind_embedded_sdk_worker_executor"
            if ready
            else str(
                normalized_gate.get("recommended_next_step")
                or normalized_preflight.get("recommended_next_step")
                or "keep_relationship_only"
            ).strip()
        ),
        "explicit_executor_binding": explicit_binding_evidence,
        "child_executor_context_budget_policy": context_budget_policy,
        "context_budget_policy": context_budget_policy,
        "child_result_merge_handoff_contract": merge_handoff,
        "merge_handoff_contract": merge_handoff,
    }


def build_child_executor_dispatch_contract(
    *,
    gate: Dict[str, Any],
    backend_registry: Dict[str, Any] | None = None,
    dispatcher_backend_adapters: Mapping[str, Any] | None = None,
    payload: Mapping[str, Any] | None = None,
    sandbox_execution_seam: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    normalized_gate = dict(gate or {})
    normalized_preflight = dict(normalized_gate.get("preflight") or {})
    prerequisites = dict(normalized_gate.get("child_executor_execution_prerequisites") or {})
    if not prerequisites:
        prerequisites = build_child_executor_execution_prerequisites_contract(
            preflight=normalized_preflight,
            gate=normalized_gate,
        )
    registry = dict(backend_registry or normalized_preflight.get("backend_registry") or build_child_executor_backend_registry_contract())
    worker_backend_requirement = next(
        (
            dict(item)
            for item in (prerequisites.get("requirements") or [])
            if isinstance(item, dict)
            and str(item.get("requirement") or "").strip() == "worker_backend_dispatch_ready"
        ),
        {},
    )
    backend_evidence = dict(worker_backend_requirement.get("evidence") or {})
    explicit_binding_requirement = next(
        (
            dict(item)
            for item in (prerequisites.get("requirements") or [])
            if isinstance(item, dict)
            and str(item.get("requirement") or "").strip() == "explicit_executor_binding_opt_in"
        ),
        {},
    )
    explicit_binding_evidence = dict(
        explicit_binding_requirement.get("evidence")
        or prerequisites.get("explicit_executor_binding")
        or {}
    )
    explicit_binding_ready = bool(explicit_binding_evidence.get("ready"))
    backend_id = str(
        backend_evidence.get("backend_id")
        or normalized_preflight.get("worker_runtime_backend")
        or registry.get("default_backend_id")
        or ""
    ).strip()
    backend_lookup = dict((registry.get("backends_by_id") or {}).get(backend_id) or {})
    backend_status = str(backend_evidence.get("status") or backend_lookup.get("status") or "").strip()
    backend_dispatch_ready = bool(
        backend_evidence.get("dispatch_ready")
        if "dispatch_ready" in backend_evidence
        else backend_lookup.get("dispatch_ready")
    )
    backend_adapter_kind = str(
        backend_evidence.get("adapter_kind")
        or backend_lookup.get("adapter_kind")
        or ""
    ).strip()
    sandbox_backend_selected = backend_adapter_kind == "sandbox_worker"
    sandbox_adapter_ready = bool(
        backend_evidence.get("adapter_contract_ready")
        if "adapter_contract_ready" in backend_evidence
        else backend_lookup.get("adapter_contract_ready")
    )
    sandbox_guard_ready = bool(
        backend_evidence.get("sandbox_guard_ready")
        if "sandbox_guard_ready" in backend_evidence
        else backend_lookup.get("sandbox_guard_ready")
    )
    sandbox_audit_ready = bool(
        backend_evidence.get("audit_ready")
        if "audit_ready" in backend_evidence
        else backend_lookup.get("audit_ready")
    )
    sandbox_idempotency_ready = bool(
        backend_evidence.get("idempotency_ready")
        if "idempotency_ready" in backend_evidence
        else backend_lookup.get("idempotency_ready")
    )
    sandbox_backend_ready = (
        not sandbox_backend_selected
        or (
            sandbox_adapter_ready
            and sandbox_guard_ready
            and sandbox_audit_ready
            and sandbox_idempotency_ready
        )
    )
    sandbox_backend_binding = build_child_executor_sandbox_backend_binding_contract(
        backend_id=backend_id,
        backend_registry_entry=backend_evidence or backend_lookup,
        adapter_contract=dict((backend_evidence or backend_lookup).get("adapter_contract") or {}),
        dispatcher_backend_adapters=dispatcher_backend_adapters or {},
        explicit_binding=explicit_binding_evidence,
    )
    sandbox_backend_binding_ready = (
        not sandbox_backend_selected
        or bool(sandbox_backend_binding.get("ready"))
    )
    payload_dict = dict(payload or {})
    unsafe_payload_keys = find_unsafe_sandbox_payload_keys(payload_dict)
    sandbox_payload_child_run_ready = (
        not sandbox_backend_selected
        or bool(str(payload_dict.get("child_run_id") or "").strip())
    )
    sandbox_payload_idempotency_ready = (
        not sandbox_backend_selected
        or bool(str(payload_dict.get("idempotency_key") or "").strip())
    )
    sandbox_payload_unsafe = sandbox_backend_selected and bool(unsafe_payload_keys)
    sandbox_seam = dict(sandbox_execution_seam or {})
    sandbox_execution_seam_supported = (
        not sandbox_backend_selected
        or bool(sandbox_seam.get("supported"))
    )
    sandbox_dispatch_ready_opt_in = (
        sandbox_backend_selected
        and sandbox_backend_binding_ready
        and sandbox_execution_seam_supported
        and sandbox_payload_child_run_ready
        and sandbox_payload_idempotency_ready
        and not sandbox_payload_unsafe
    )
    dispatch_mode = str(
        backend_evidence.get("dispatch_mode")
        or backend_lookup.get("dispatch_mode")
        or "not_implemented"
    ).strip()
    gate_allowed = bool(normalized_gate.get("allowed"))
    prerequisites_ready = bool(prerequisites.get("ready"))
    dispatch_ready = (
        gate_allowed
        and prerequisites_ready
        and backend_dispatch_ready
        and sandbox_backend_ready
        and sandbox_backend_binding_ready
        and explicit_binding_ready
        and sandbox_execution_seam_supported
        and sandbox_payload_child_run_ready
        and sandbox_payload_idempotency_ready
        and not sandbox_payload_unsafe
    )
    blockers = []
    if not gate_allowed:
        blockers.append("promotion_gate_allowed")
    for item in (prerequisites.get("missing_requirements") or []):
        value = str(item or "").strip()
        if value:
            blockers.append(value)
    if not backend_dispatch_ready:
        blockers.append("worker_backend_dispatch_ready")
    if not explicit_binding_ready:
        blockers.append("explicit_executor_binding_opt_in")
    if sandbox_backend_selected:
        if not sandbox_adapter_ready:
            blockers.append("sandbox_adapter_contract_ready")
        if not sandbox_guard_ready:
            blockers.append("sandbox_guard_ready")
        if not sandbox_audit_ready:
            blockers.append("sandbox_audit_ready")
        if not sandbox_idempotency_ready:
            blockers.append("sandbox_idempotency_ready")
        if not sandbox_backend_binding_ready:
            blockers.append("sandbox_backend_binding_ready")
        if not sandbox_execution_seam_supported:
            blockers.append("sandbox_execution_seam_supported")
        if not sandbox_payload_child_run_ready:
            blockers.append("sandbox_payload_child_run_ready")
        if not sandbox_payload_idempotency_ready:
            blockers.append("sandbox_payload_idempotency_ready")
        if sandbox_payload_unsafe:
            blockers.append("sandbox_payload_unsafe")
        for item in (
            backend_evidence.get("missing_guard_blockers")
            or backend_lookup.get("missing_guard_blockers")
            or []
        ):
            value = str(item or "").strip()
            if value:
                blockers.append(value)
    for item in (backend_evidence.get("blockers") or backend_lookup.get("blockers") or []):
        value = str(item or "").strip()
        if value:
            blockers.append(value)
    blockers = list(dict.fromkeys(blockers))
    dispatch_contract = {
        "contract_version": "phase-ii-child-executor-dispatch-v1",
        "overall_status": "ready" if dispatch_ready else "blocked",
        "dispatch_ready": dispatch_ready,
        "will_dispatch": False,
        "dispatch_mode": dispatch_mode,
        "backend_id": backend_id,
        "backend_status": backend_status,
        "backend_dispatch_ready": backend_dispatch_ready,
        "backend_adapter_kind": backend_adapter_kind,
        "explicit_executor_binding_ready": explicit_binding_ready,
        "explicit_executor_binding_status": str(
            explicit_binding_evidence.get("binding_status") or ""
        ).strip(),
        "explicit_executor_binding_source": str(
            explicit_binding_evidence.get("binding_source") or ""
        ).strip(),
        "sandbox_backend_selected": sandbox_backend_selected,
        "sandbox_backend_ready": sandbox_backend_ready,
        "sandbox_backend_binding_ready": sandbox_backend_binding_ready,
        "sandbox_execution_seam_supported": sandbox_execution_seam_supported,
        "sandbox_payload_child_run_ready": sandbox_payload_child_run_ready,
        "sandbox_payload_idempotency_ready": sandbox_payload_idempotency_ready,
        "sandbox_payload_unsafe_keys": unsafe_payload_keys,
        "sandbox_dispatch_ready_opt_in": sandbox_dispatch_ready_opt_in,
        "sandbox_adapter_ready": sandbox_adapter_ready,
        "sandbox_guard_ready": sandbox_guard_ready,
        "sandbox_audit_ready": sandbox_audit_ready,
        "sandbox_idempotency_ready": sandbox_idempotency_ready,
        "gate_allowed": gate_allowed,
        "prerequisites_ready": prerequisites_ready,
        "relationship_seam_preserved": True,
        "blockers": blockers,
        "required_contracts": [
            "child_executor_backend_registry",
            "child_executor_promotion_gate",
            "child_executor_execution_prerequisites",
            "child_executor_sandbox_worker_backend",
            "child_executor_sandbox_backend_binding",
        ],
        "evidence": {
            "backend_registry": registry,
            "backend": backend_evidence or backend_lookup,
            "explicit_executor_binding": explicit_binding_evidence,
            "child_executor_sandbox_backend_binding": sandbox_backend_binding,
            "sandbox_execution_seam": sandbox_seam,
            "sandbox_payload": {
                "child_run_ready": sandbox_payload_child_run_ready,
                "idempotency_ready": sandbox_payload_idempotency_ready,
                "unsafe_payload_keys": unsafe_payload_keys,
            },
            "promotion_gate": {
                "gate_status": str(normalized_gate.get("gate_status") or "").strip(),
                "allowed": gate_allowed,
                "failure_reason": str(normalized_gate.get("failure_reason") or "").strip(),
                "executor_path": str(normalized_gate.get("executor_path") or "").strip(),
            },
            "execution_prerequisites": prerequisites,
        },
        "recommended_next_step": (
            "implement_child_executor_dispatcher"
            if dispatch_ready
            else (
                "implement_child_executor_backend_dispatch"
                if "worker_backend_dispatch_ready" in blockers
                else str(
                    prerequisites.get("recommended_next_step")
                    or normalized_gate.get("recommended_next_step")
                    or "keep_relationship_only"
                ).strip()
            )
        ),
        "non_goals": [
            "real_child_executor_dispatch",
            "worker_process_allocation",
            "sandbox_or_queue_execution",
        ],
    }
    dispatch_contract["child_executor_sandbox_backend_binding"] = sandbox_backend_binding
    dispatch_contract["sandbox_backend_binding"] = sandbox_backend_binding
    attempt_handoff = build_child_executor_dispatch_attempt_handoff_contract(
        dispatch_contract=dispatch_contract
    )
    dispatch_contract["child_executor_dispatch_attempt_handoff"] = attempt_handoff
    dispatch_contract["dispatch_attempt_handoff"] = attempt_handoff
    dispatch_contract["evidence"]["dispatch_attempt_handoff"] = attempt_handoff
    return dispatch_contract


def build_child_executor_routing_contract(
    *,
    gate: Dict[str, Any],
) -> Dict[str, Any]:
    normalized_gate = dict(gate or {})
    allowed = bool(normalized_gate.get("allowed"))
    executor_path = str(normalized_gate.get("executor_path") or "").strip()
    route_status = "routed" if allowed and executor_path else "blocked"
    return {
        "contract_version": "phase-ii-child-executor-routing-v1",
        "route_status": route_status,
        "will_execute": False,
        "executor_path": executor_path if route_status == "routed" else "",
        "route_reason": "" if route_status == "routed" else str(normalized_gate.get("failure_reason") or "child_executor_gate_blocked").strip(),
        "handoff_mode": "no_execute_contract_only",
        "recommended_action": (
            "bind_embedded_sdk_worker_executor"
            if route_status == "routed"
            else str(normalized_gate.get("recommended_next_step") or "keep_relationship_only").strip()
        ),
        "blockers": [
            str(item).strip()
            for item in (normalized_gate.get("blockers") or [])
            if str(item).strip()
        ],
        "gate": normalized_gate,
        "routed_at": _utc_now(),
    }


def build_child_executor_binding_contract(
    *,
    route: Dict[str, Any],
    parent_run_id: str | None = None,
) -> Dict[str, Any]:
    normalized_route = dict(route or {})
    routed = str(normalized_route.get("route_status") or "").strip() == "routed"
    normalized_parent_run_id = str(parent_run_id or "").strip()
    executor_path = str(normalized_route.get("executor_path") or "").strip()
    binding_id = (
        f"binding:{executor_path}:{normalized_parent_run_id or 'standalone'}"
        if routed and executor_path
        else ""
    )
    return {
        "contract_version": "phase-ii-child-executor-binding-v1",
        "binding_status": "bound" if routed else "blocked",
        "will_execute": False,
        "binding_id": binding_id,
        "executor_path": executor_path if routed else "",
        "handoff_mode": "record_only",
        "binding_reason": "" if routed else str(normalized_route.get("route_reason") or "child_executor_route_blocked").strip(),
        "recommended_action": (
            "prepare_embedded_sdk_worker_executor"
            if routed
            else str(normalized_route.get("recommended_action") or "keep_relationship_only").strip()
        ),
        "blockers": [
            str(item).strip()
            for item in (normalized_route.get("blockers") or [])
            if str(item).strip()
        ],
        "route": normalized_route,
        "bound_at": _utc_now(),
    }


def build_child_executor_stub_contract(
    *,
    binding: Dict[str, Any],
) -> Dict[str, Any]:
    normalized_binding = dict(binding or {})
    bound = str(normalized_binding.get("binding_status") or "").strip() == "bound"
    executor_path = str(normalized_binding.get("executor_path") or "").strip()
    binding_id = str(normalized_binding.get("binding_id") or "").strip()
    return {
        "contract_version": "phase-ii-child-executor-stub-v1",
        "stub_status": "recorded" if bound else "blocked",
        "will_execute": False,
        "executor_path": executor_path if bound else "",
        "binding_id": binding_id if bound else "",
        "execution_mode": "record_only_stub",
        "stub_reason": "" if bound else str(normalized_binding.get("binding_reason") or "child_executor_binding_blocked").strip(),
        "recommended_action": (
            "upgrade_to_real_executor"
            if bound
            else str(normalized_binding.get("recommended_action") or "keep_relationship_only").strip()
        ),
        "binding": normalized_binding,
        "recorded_at": _utc_now(),
    }


def _extract_child_executor_entities(input_preview: str) -> list[str]:
    text = str(input_preview or "").strip()
    if not text:
        return []
    keyword_groups = [
        ["交易", "账户", "资金", "订单", "风险", "欺诈", "风控", "审批", "异常", "告警"],
        ["巡检", "计划", "设备", "工单", "节点", "路线", "现场", "任务"],
        ["合并", "摘要", "上下文", "结果", "报告", "分析"],
    ]
    entities: list[str] = []
    for group in keyword_groups:
        for keyword in group:
            if keyword in text and keyword not in entities:
                entities.append(keyword)
    if not entities:
        text_compact = text.replace("，", " ").replace("。", " ").replace(",", " ").strip()
        for token in text_compact.split():
            normalized = token.strip()
            if normalized and normalized not in entities:
                entities.append(normalized)
            if len(entities) >= 3:
                break
    return entities[:5]


def _build_child_executor_semantics(
    *,
    input_preview: str,
    intent_label: str,
    risk_level: str,
    merge_strategy: str,
    agent_name: str,
    worker_runtime_backend: str,
    executor_path: str,
) -> Dict[str, Any]:
    entities = _extract_child_executor_entities(input_preview)
    backend_label = worker_runtime_backend or executor_path or "embedded_sdk_worker_candidate"
    effective_merge_strategy = merge_strategy or "append_summary"
    agent_label = agent_name or "unnamed_child_agent"
    if intent_label == CHILD_EXECUTOR_INTENT_RISK_REVIEW:
        focus_points = [
            "识别输入中的高风险对象与异常信号",
            "确认是否需要人工审批或二次复核",
            f"为父流程准备 {effective_merge_strategy} 合并结果",
        ]
        action_items = [
            f"优先复核 {entities[0] if entities else '关键风险对象'} 的上下游证据",
            "检查是否存在跨账户、跨环节或跨状态异常",
            "必要时将主流程切换到审批等待态",
        ]
        key_findings = [
            "输入命中风险/复核语义，已按风险评估路径处理",
            f"当前执行器后端为 {backend_label}",
            (
                f"识别到重点对象：{'、'.join(entities)}"
                if entities
                else "当前未识别到明确业务实体，建议补充更具体输入"
            ),
        ]
        business_result = {
            "result_type": "risk_assessment",
            "headline": f"{agent_label} 已完成风险复核",
            "risk_level": risk_level,
            "conclusion": "建议人工复核关键风险点后继续主流程",
            "entities": entities,
            "focus_points": focus_points,
            "action_items": action_items,
            "key_findings": key_findings,
            "next_actions": [
                "复核高风险证据点",
                "确认父流程是否需要等待人工审批",
            ],
        }
        output_summary = (
            f"{business_result['headline']}，当前风险等级 {risk_level}，"
            f"重点对象 {('、'.join(entities) if entities else '待补充')}"
        )
        output_text = (
            f"风险复核结论：{business_result['conclusion']}；"
            f"关键发现：{'；'.join(key_findings)}"
        )
        output_sections = [
            {
                "section_id": "risk_overview",
                "title": business_result["headline"],
                "summary": output_summary,
                "content": output_text,
                "metadata": {
                    "intent_label": intent_label,
                    "risk_level": risk_level,
                    "entity_count": len(entities),
                },
            },
            {
                "section_id": "risk_focus_points",
                "title": "复核关注点",
                "summary": "建议先处理高风险与审批相关关注点",
                "content": "\n".join(focus_points),
                "metadata": {
                    "intent_label": intent_label,
                    "risk_level": risk_level,
                    "entity_count": len(entities),
                },
            },
            {
                "section_id": "risk_actions",
                "title": "建议动作",
                "summary": "建议按风险复核路径继续推进",
                "content": "\n".join(action_items),
                "metadata": {
                    "intent_label": intent_label,
                    "risk_level": risk_level,
                    "entity_count": len(entities),
                },
            },
        ]
    elif intent_label == CHILD_EXECUTOR_INTENT_PLANNING:
        focus_points = [
            "拆分执行阶段与依赖顺序",
            "标记需要现场确认或系统配合的节点",
            f"为父流程准备 {effective_merge_strategy} 合并结果",
        ]
        action_items = [
            f"先明确 {entities[0] if entities else '核心任务'} 的执行范围",
            "补齐前置依赖、资源与时间窗口",
            "确认计划是否需要进一步拆成子步骤或工单",
        ]
        key_findings = [
            "输入命中计划/巡检语义，已按规划路径处理",
            f"当前执行器后端为 {backend_label}",
            (
                f"识别到计划对象：{'、'.join(entities)}"
                if entities
                else "当前未识别到明确计划对象，建议补充目标与范围"
            ),
        ]
        business_result = {
            "result_type": "plan_outline",
            "headline": f"{agent_label} 已生成计划提纲",
            "risk_level": risk_level,
            "conclusion": "建议将该提纲作为后续步骤拆解的输入",
            "entities": entities,
            "focus_points": focus_points,
            "action_items": action_items,
            "key_findings": key_findings,
            "next_actions": [
                "拆解成可执行步骤",
                "确认依赖与执行顺序",
            ],
        }
        output_summary = (
            f"{business_result['headline']}，已识别 "
            f"{('、'.join(entities) if entities else '核心任务')} 的计划骨架"
        )
        output_text = (
            f"计划提纲结论：{business_result['conclusion']}；"
            f"关键发现：{'；'.join(key_findings)}"
        )
        output_sections = [
            {
                "section_id": "plan_overview",
                "title": business_result["headline"],
                "summary": output_summary,
                "content": output_text,
                "metadata": {
                    "intent_label": intent_label,
                    "risk_level": risk_level,
                    "entity_count": len(entities),
                },
            },
            {
                "section_id": "plan_focus_points",
                "title": "计划关注点",
                "summary": "建议优先拆解依赖、顺序与边界",
                "content": "\n".join(focus_points),
                "metadata": {
                    "intent_label": intent_label,
                    "risk_level": risk_level,
                    "entity_count": len(entities),
                },
            },
            {
                "section_id": "plan_actions",
                "title": "后续步骤",
                "summary": "建议把提纲推进到执行步骤层",
                "content": "\n".join(action_items),
                "metadata": {
                    "intent_label": intent_label,
                    "risk_level": risk_level,
                    "entity_count": len(entities),
                },
            },
        ]
    else:
        focus_points = [
            "收口输入中的主题、目标与输出形式",
            "判断哪些内容适合直接合并到父流程",
            f"为父流程准备 {effective_merge_strategy} 合并结果",
        ]
        action_items = [
            "把当前摘要并入父 run 上下文",
            "补充更明确的任务目标或领域对象",
            "如需更强执行能力，再升级专门子执行器",
        ]
        key_findings = [
            "当前输入未命中特定业务意图，已按通用分析路径处理",
            f"当前执行器后端为 {backend_label}",
            (
                f"识别到分析主题：{'、'.join(entities)}"
                if entities
                else "当前未识别到明确主题，建议补充更具体输入"
            ),
        ]
        business_result = {
            "result_type": "analysis_summary",
            "headline": f"{agent_label} 已生成分析摘要",
            "risk_level": risk_level,
            "conclusion": "建议将该摘要作为父 run 的辅助上下文",
            "entities": entities,
            "focus_points": focus_points,
            "action_items": action_items,
            "key_findings": key_findings,
            "next_actions": [
                "将摘要并入父 run 上下文",
                "视需要补充专门子执行器",
            ],
        }
        output_summary = (
            f"{business_result['headline']}，"
            f"当前主题 {('、'.join(entities) if entities else '待补充')}"
        )
        output_text = (
            f"分析摘要结论：{business_result['conclusion']}；"
            f"关键发现：{'；'.join(key_findings)}"
        )
        output_sections = [
            {
                "section_id": "analysis_overview",
                "title": business_result["headline"],
                "summary": output_summary,
                "content": output_text,
                "metadata": {
                    "intent_label": intent_label,
                    "risk_level": risk_level,
                    "entity_count": len(entities),
                },
            },
            {
                "section_id": "analysis_actions",
                "title": "建议动作",
                "summary": "建议把当前摘要作为辅助上下文继续使用",
                "content": "\n".join(action_items),
                "metadata": {
                    "intent_label": intent_label,
                    "risk_level": risk_level,
                    "entity_count": len(entities),
                },
            },
        ]
    return {
        "entities": entities,
        "focus_points": focus_points,
        "action_items": action_items,
        "business_result": business_result,
        "output_summary": output_summary,
        "output_text": output_text,
        "output_sections": output_sections,
    }


def build_child_executor_execution_contract(
    *,
    binding: Dict[str, Any],
) -> Dict[str, Any]:
    normalized_binding = dict(binding or {})
    bound = str(normalized_binding.get("binding_status") or "").strip() == "bound"
    executor_path = str(normalized_binding.get("executor_path") or "").strip()
    binding_id = str(normalized_binding.get("binding_id") or "").strip()
    preflight = dict((((normalized_binding.get("route") or {}).get("gate") or {}).get("preflight") or {}))
    prerequisites = dict(
        (((normalized_binding.get("route") or {}).get("gate") or {}).get("child_executor_execution_prerequisites") or {})
    )
    explicit_binding = dict(prerequisites.get("explicit_executor_binding") or {})
    explicit_binding_ready = bool(explicit_binding.get("ready"))
    executable = bound and executor_path == "embedded_sdk_worker_candidate" and explicit_binding_ready
    execution_status = "executed" if executable else "blocked"
    input_preview = str(preflight.get("input_preview") or "").strip()
    agent_name = str(preflight.get("agent_name") or "").strip()
    merge_strategy = str(preflight.get("merge_strategy") or "").strip()
    worker_runtime_backend = str(preflight.get("worker_runtime_backend") or "").strip()
    normalized_input = input_preview.lower()
    if any(keyword in normalized_input for keyword in ["风险", "fraud", "review", "复核"]):
        intent_label = CHILD_EXECUTOR_INTENT_RISK_REVIEW
    elif any(keyword in normalized_input for keyword in ["计划", "plan", "巡检"]):
        intent_label = CHILD_EXECUTOR_INTENT_PLANNING
    else:
        intent_label = CHILD_EXECUTOR_INTENT_GENERAL_ANALYSIS
    if any(keyword in normalized_input for keyword in ["高", "风险", "fraud"]):
        risk_level = "medium"
    else:
        risk_level = "low"
    recommendations = [
        f"优先按 {merge_strategy or 'append_summary'} 合并该子执行结果",
        "如需升级为真实执行器，请替换 skeleton executor path",
    ]
    evidence_points = [
        f"agent={agent_name or 'unnamed_child_agent'}",
        f"backend={worker_runtime_backend or executor_path}",
        f"intent={intent_label}",
    ]
    execution_semantics = _build_child_executor_semantics(
        input_preview=input_preview,
        intent_label=intent_label,
        risk_level=risk_level,
        merge_strategy=merge_strategy,
        agent_name=agent_name,
        worker_runtime_backend=worker_runtime_backend,
        executor_path=executor_path,
    )
    entities = list(execution_semantics.get("entities") or [])
    focus_points = list(execution_semantics.get("focus_points") or [])
    action_items = list(execution_semantics.get("action_items") or [])
    business_result = dict(execution_semantics.get("business_result") or {})
    output_summary = str(execution_semantics.get("output_summary") or "").strip()
    output_text = str(execution_semantics.get("output_text") or "").strip()
    output_sections = list(execution_semantics.get("output_sections") or [])
    if entities:
        evidence_points.append(f"entities={'、'.join(entities)}")
    output_payload = (
        {
            "executor_kind": "embedded_sdk_worker_skeleton",
            "agent_name": agent_name or "unnamed_child_agent",
            "input_preview": input_preview,
            "merge_strategy": merge_strategy or "unspecified",
            "worker_runtime_backend": worker_runtime_backend or executor_path,
            "intent_label": intent_label,
            "risk_level": risk_level,
            "entities": entities,
            "focus_points": focus_points,
            "action_items": action_items,
            "recommendations": recommendations,
            "evidence_points": evidence_points,
            "business_result": business_result,
            "status": "executed",
        }
        if executable
        else {}
    )
    if not executable:
        output_summary = ""
        output_text = ""
        output_sections = []
    output_envelope = (
        {
            "artifact_ref": {
                "artifact_id": f"child-output:{binding_id}",
                "kind": "child_executor_output",
                "uri": f"embedded://child-executor-output/{binding_id}",
            },
            "summary": output_summary,
            "text": output_text,
            "merge_hint": merge_strategy or "append_summary",
            "merge_ready": True,
            "sections": output_sections,
            "payload": output_payload,
        }
        if executable and binding_id
        else {}
    )
    return {
        "contract_version": "phase-ii-child-executor-execution-v1",
        "execution_status": execution_status,
        "will_execute": executable,
        "executor_path": executor_path if executable else "",
        "binding_id": binding_id if executable else "",
        "execution_mode": "embedded_sdk_worker_skeleton" if executable else "",
        "output_summary": output_summary,
        "output_text": output_text,
        "output_payload": output_payload,
        "output_envelope": output_envelope,
        "explicit_executor_binding": explicit_binding,
        "execution_reason": (
            ""
            if executable
            else (
                "explicit_executor_binding_opt_in_missing"
                if bound and executor_path == "embedded_sdk_worker_candidate" and not explicit_binding_ready
                else str(normalized_binding.get("binding_reason") or "child_executor_binding_blocked").strip()
            )
        ),
        "recommended_action": (
            "replace_noop_worker_with_real_executor"
            if executable
            else str(normalized_binding.get("recommended_action") or "keep_relationship_only").strip()
        ),
        "binding": normalized_binding,
        "executed_at": _utc_now(),
    }


def build_child_executor_merge_contract(
    *,
    execution: Dict[str, Any],
    previous_semantics: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    normalized_execution = dict(execution or {})
    execution_status = str(normalized_execution.get("execution_status") or "").strip()
    envelope = dict(normalized_execution.get("output_envelope") or {})
    merge_ready = bool(envelope.get("merge_ready"))
    sections = list(envelope.get("sections") or [])
    merge_status = "merged" if execution_status == "executed" and merge_ready and sections else "blocked"
    summary = str(envelope.get("summary") or "").strip()
    text = str(envelope.get("text") or "").strip()
    artifact_ref = dict(envelope.get("artifact_ref") or {})
    merge_strategy = str(envelope.get("merge_hint") or "").strip() or "append_summary"
    payload = dict(normalized_execution.get("output_payload") or {})
    intent_label = _normalize_child_executor_intent_label(payload.get("intent_label"))
    merge_behavior = _build_child_executor_merge_behavior(intent_label=intent_label)
    merged_semantics = _merge_child_executor_semantics(
        previous_semantics=dict(previous_semantics or {}),
        payload=payload,
        merge_behavior=merge_behavior,
    )
    if merge_strategy == "role_sections":
        merged_output = "\n\n".join(
            section_text
            for section_text in [
                (
                    f"[{str(section.get('title') or '').strip()}]\n{str(section.get('content') or '').strip()}".strip()
                    if str(section.get("title") or "").strip()
                    else str(section.get("content") or "").strip()
                )
                for section in sections
            ]
            if section_text.strip()
        ).strip()
    else:
        merged_output = "\n\n".join(
            str(section.get("content") or "").strip()
            for section in sections
            if str(section.get("content") or "").strip()
        ).strip()
    return {
        "contract_version": "phase-ii-child-executor-merge-v1",
        "merge_status": merge_status,
        "merge_ready": merge_ready,
        "merge_reason": "" if merge_status == "merged" else "child_executor_output_not_merge_ready",
        "merge_strategy": merge_strategy,
        "intent_label": intent_label,
        "merge_behavior": dict(merge_behavior),
        "merged_semantics": dict(merged_semantics),
        "merged_summary": summary,
        "merged_output": merged_output or text,
        "artifact_ref": artifact_ref,
        "section_count": len(sections),
        "execution": normalized_execution,
        "merged_at": _utc_now(),
    }


def _build_child_executor_merge_behavior(*, intent_label: str) -> Dict[str, str]:
    normalized_intent = _normalize_child_executor_intent_label(intent_label)
    if normalized_intent == CHILD_EXECUTOR_INTENT_RISK_REVIEW:
        return {
            "entities": "append_dedup",
            "focus_points": "append_dedup",
            "action_items": "append_dedup",
            "latest_conclusion": "replace_latest",
        }
    if normalized_intent == CHILD_EXECUTOR_INTENT_PLANNING:
        return {
            "entities": "append_dedup",
            "focus_points": "replace_latest",
            "action_items": "replace_latest",
            "latest_conclusion": "replace_latest",
        }
    return {
        "entities": "append_dedup",
        "focus_points": "summary_only",
        "action_items": "summary_only",
        "latest_conclusion": "replace_latest",
    }


def _merge_child_executor_semantics(
    *,
    previous_semantics: Dict[str, Any],
    payload: Dict[str, Any],
    merge_behavior: Dict[str, str],
) -> Dict[str, Any]:
    previous = dict(previous_semantics or {})
    entities = list(payload.get("entities") or [])
    focus_points = list(payload.get("focus_points") or [])
    action_items = list(payload.get("action_items") or [])
    conclusion = str(((payload.get("business_result") or {}).get("conclusion")) or "").strip()
    intent_label = _normalize_child_executor_intent_label(payload.get("intent_label"))

    merged_entities = _apply_child_executor_merge_mode(
        previous=list(previous.get("entities") or []),
        current=entities,
        mode=str(merge_behavior.get("entities") or "append_dedup"),
    )
    merged_focus_points = _apply_child_executor_merge_mode(
        previous=list(previous.get("focus_points") or []),
        current=focus_points,
        mode=str(merge_behavior.get("focus_points") or "summary_only"),
    )
    merged_action_items = _apply_child_executor_merge_mode(
        previous=list(previous.get("action_items") or []),
        current=action_items,
        mode=str(merge_behavior.get("action_items") or "summary_only"),
    )
    latest_conclusion = conclusion or str(previous.get("latest_conclusion") or "").strip()

    return {
        "intent_label": intent_label,
        "merge_behavior": dict(merge_behavior),
        "entities": merged_entities,
        "focus_points": merged_focus_points,
        "action_items": merged_action_items,
        "latest_conclusion": latest_conclusion,
    }


def _normalize_child_executor_intent_label(value: Any) -> str:
    normalized = str(value or "").strip()
    if normalized in CHILD_EXECUTOR_SUPPORTED_INTENTS:
        return normalized
    return CHILD_EXECUTOR_DEFAULT_INTENT


def _build_child_executor_merged_sections(merged_semantics: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(merged_semantics or {})
    merge_behavior = dict(normalized.get("merge_behavior") or {})
    return {
        "merged_entities": {
            "section_id": "merged_entities",
            "section_kind": "list",
            "title": "Merged Entities",
            "merge_mode": str(merge_behavior.get("entities") or "").strip(),
            "items": list(normalized.get("entities") or []),
            "item_count": len(list(normalized.get("entities") or [])),
        },
        "merged_focus": {
            "section_id": "merged_focus",
            "section_kind": "list",
            "title": "Merged Focus",
            "merge_mode": str(merge_behavior.get("focus_points") or "").strip(),
            "items": list(normalized.get("focus_points") or []),
            "item_count": len(list(normalized.get("focus_points") or [])),
        },
        "merged_actions": {
            "section_id": "merged_actions",
            "section_kind": "list",
            "title": "Merged Actions",
            "merge_mode": str(merge_behavior.get("action_items") or "").strip(),
            "items": list(normalized.get("action_items") or []),
            "item_count": len(list(normalized.get("action_items") or [])),
        },
        "latest_conclusion": {
            "section_id": "latest_conclusion",
            "section_kind": "text",
            "title": "Latest Conclusion",
            "merge_mode": str(merge_behavior.get("latest_conclusion") or "").strip(),
            "text": str(normalized.get("latest_conclusion") or "").strip(),
            "text_length": len(str(normalized.get("latest_conclusion") or "").strip()),
        },
    }


def _build_child_executor_parent_state_surface(merged_semantics: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(merged_semantics or {})
    entities = list(normalized.get("entities") or [])
    focus_points = list(normalized.get("focus_points") or [])
    action_items = list(normalized.get("action_items") or [])
    sections = _build_child_executor_merged_sections(normalized)
    section_ids = ["merged_entities", "merged_focus", "merged_actions", "latest_conclusion"]
    return {
        "intent_label": _normalize_child_executor_intent_label(normalized.get("intent_label")),
        "entity_count": len(entities),
        "focus_count": len(focus_points),
        "action_count": len(action_items),
        "primary_entities": entities[:3],
        "latest_conclusion": str(normalized.get("latest_conclusion") or "").strip(),
        "section_source": "merged_sections",
        "section_ids": section_ids,
        "section_counts": {
            "merged_entities": int((sections.get("merged_entities") or {}).get("item_count") or 0),
            "merged_focus": int((sections.get("merged_focus") or {}).get("item_count") or 0),
            "merged_actions": int((sections.get("merged_actions") or {}).get("item_count") or 0),
            "latest_conclusion": int((sections.get("latest_conclusion") or {}).get("text_length") or 0),
        },
    }


def _apply_child_executor_merge_mode(
    *,
    previous: list[str],
    current: list[str],
    mode: str,
) -> list[str]:
    normalized_mode = str(mode or "").strip() or "summary_only"
    previous_values = [str(item).strip() for item in list(previous or []) if str(item).strip()]
    current_values = [str(item).strip() for item in list(current or []) if str(item).strip()]
    if normalized_mode == "replace_latest":
        return current_values
    if normalized_mode == "append_dedup":
        merged = []
        for item in [*previous_values, *current_values]:
            if item and item not in merged:
                merged.append(item)
        return merged
    return previous_values


def build_embedded_sdk_contract() -> Dict[str, Any]:
    delegate_preflight = build_child_executor_preflight_contract()
    delegate_gate = build_child_executor_gate_contract(preflight=delegate_preflight)
    delegate_routing = build_child_executor_routing_contract(gate=delegate_gate)
    delegate_binding = build_child_executor_binding_contract(route=delegate_routing)
    delegate_execution = build_child_executor_execution_contract(binding=delegate_binding)
    return {
        "contract_version": "phase-b-embedded-sdk-v1",
        "stability": "draft",
        "methods": [dict(item) for item in EMBEDDED_SDK_METHODS],
        "event_status_kinds": [dict(item) for item in EMBEDDED_SDK_EVENT_STATUS_KINDS],
        "volatile_runtime_state": list(EMBEDDED_SDK_VOLATILE_RUNTIME_STATE),
        "persistence_seams": list(EMBEDDED_SDK_PERSISTENCE_SEAMS),
        "recovery_entrypoints": [dict(item) for item in EMBEDDED_SDK_RECOVERY_ENTRYPOINTS],
        "recovery_operation_contract": build_recovery_operation_contract(),
        "recovery_retry_scheduler_contract": build_recovery_retry_scheduler_contract(),
        "durable_recovery_loader_contract": build_durable_recovery_loader_contract(),
        "child_executor_backend_registry": build_child_executor_backend_registry_contract(),
        "child_executor_dispatch_contract": build_child_executor_dispatch_contract(gate=delegate_gate),
        "child_executor_dispatcher_contract": build_child_executor_dispatcher_contract(),
        "delegate_preflight": delegate_preflight,
        "delegate_gate": delegate_gate,
        "delegate_routing": delegate_routing,
        "delegate_binding": delegate_binding,
        "delegate_stub": build_child_executor_stub_contract(
            binding=delegate_binding
        ),
        "delegate_execution": delegate_execution,
        "delegate_merge": build_child_executor_merge_contract(
            execution=delegate_execution
        ),
        "delegate_replay": {
            "contract_version": "phase-ii-child-executor-replay-v1",
            "record_count": 0,
            "records": [],
        },
        "delegate_artifact_summary": {
            "contract_version": "phase-ii-child-executor-artifact-summary-v1",
            "record_count": 0,
            "latest_artifact_id": "",
            "latest_merge_strategy": "",
            "latest_result_type": "",
            "latest_conclusion": "",
            "latest_merged_summary": "",
            "latest_merged_output": "",
            "latest_entities": [],
            "latest_focus_points": [],
            "latest_action_items": [],
            "artifact_ids": [],
            "merge_strategies": [],
            "result_types": [],
            "entity_sets": [],
        },
    }


def validate_embedded_sdk_event_payloads(
    events: Iterable[Dict[str, Any]],
    *,
    contract: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Validate concrete SDK events against the declared required payload fields."""

    sdk_contract = dict(contract or build_embedded_sdk_contract())
    event_contracts = {
        str(item.get("status_kind") or "").strip(): dict(item)
        for item in sdk_contract.get("event_status_kinds") or []
        if isinstance(item, dict) and str(item.get("status_kind") or "").strip()
    }
    missing_payloads = []
    checked_event_count = 0
    for index, event in enumerate(list(events or [])):
        if not isinstance(event, dict):
            continue
        status_kind = str(event.get("status_kind") or "").strip()
        event_contract = event_contracts.get(status_kind)
        if event_contract is None:
            continue
        checked_event_count += 1
        required_payload = [
            str(field_name)
            for field_name in event_contract.get("required_payload") or []
            if str(field_name).strip()
        ]
        missing_fields = [field_name for field_name in required_payload if field_name not in event]
        if missing_fields:
            missing_payloads.append({
                "index": index,
                "status_kind": status_kind,
                "missing_fields": missing_fields,
            })
    missing_payload_count = sum(len(item["missing_fields"]) for item in missing_payloads)
    return {
        "valid": missing_payload_count == 0,
        "checked_event_count": checked_event_count,
        "missing_payload_count": missing_payload_count,
        "missing_payloads": missing_payloads,
    }


class _EmbeddedRegisteredTool:
    def __init__(
        self,
        *,
        tool_spec: ToolSpec,
        handler: Callable[[Dict[str, Any]], Any],
        parameters: Dict[str, Any] | None = None,
    ):
        self.name = tool_spec.name
        self.description = tool_spec.description
        self.permission_level = tool_spec.permission_level
        self.parameters = dict(parameters or {})
        self._handler = handler

    def invoke(self, args: Dict[str, Any]) -> Any:
        return self._handler(dict(args or {}))


class EmbeddedAgentRuntimeSDK:
    """Minimal in-process SDK for embedding the runtime core into business projects.

    This SDK intentionally keeps persistence in memory for now. It is the stable
    seam for vertical projects to exercise Runtime Core semantics without
    bypassing event and approval envelopes.
    """

    def __init__(
        self,
        *,
        runs: Dict[str, AgentRunContext] | None = None,
        events: Dict[str, list[Dict[str, Any]]] | None = None,
        approvals: Dict[str, ApprovalRequestState] | None = None,
        artifacts: Dict[str, Dict[str, Any]] | None = None,
        artifact_store: ArtifactStore | None = None,
        tool_continuations: Dict[str, Dict[str, Any]] | None = None,
        loop_continuations: Dict[str, Dict[str, Any]] | None = None,
        continuation_registry: EmbeddedContinuationRegistry | None = None,
        workspace_store: EmbeddedRunWorkspaceStore | None = None,
        runtime_dependencies: EmbeddedRuntimeDependencies | None = None,
        query_control_db: Any | None = None,
        query_control_event_mapper: Any | None = None,
        query_control_timeline_service: Any | None = None,
        approval_lifecycle_trace_recorder: Any | None = None,
        tool_runtime_service: Any | None = None,
        worker_ownership_store: Any | None = None,
        worker_ownership_auto_claim_enabled: bool = False,
        worker_ownership_auto_claim_gate_enforced: bool = False,
        worker_ownership_auto_claim_production_gate_ready: bool = False,
        worker_ownership_auto_claim_idempotency_evidence_ready: bool = False,
        worker_ownership_auto_claim_audit_evidence_ready: bool = False,
        worker_ownership_auto_claim_rollout_decision_recorded: bool = False,
        worker_ownership_auto_claim_allowed_entrypoints: list[str] | tuple[str, ...] | None = None,
        worker_ownership_worker_id: str = "embedded_runtime_recovery",
    ):
        # Current runtime state remains process-local. Phase II will introduce
        # explicit persistence seams instead of letting callers depend on these
        # in-memory maps as if they were durable storage.
        self._runs = runs if runs is not None else {}
        self._events = events if events is not None else {}
        self._approvals = approvals if approvals is not None else {}
        self._artifacts = artifacts if artifacts is not None else {}
        self._artifact_store = artifact_store
        self._tool_continuations = tool_continuations if tool_continuations is not None else {}
        self._loop_continuations = loop_continuations if loop_continuations is not None else {}
        dependencies = runtime_dependencies or get_default_embedded_runtime_dependencies()
        self._continuation_registry = (
            continuation_registry
            if continuation_registry is not None
            else dependencies.continuation_registry
        )
        self._workspace_store = workspace_store if workspace_store is not None else dependencies.workspace_store
        self._query_control_db = query_control_db
        self._query_control_event_mapper = query_control_event_mapper or get_query_control_event_mapper_service()
        self._query_control_timeline_service = query_control_timeline_service or (
            get_query_control_timeline_service() if query_control_db is not None else None
        )
        self._approval_lifecycle_trace_recorder = approval_lifecycle_trace_recorder
        self._tool_runtime_service = tool_runtime_service
        self._worker_ownership_store = (
            worker_ownership_store
            if worker_ownership_store is not None
            else getattr(dependencies, "worker_ownership_store", None)
        )
        self._worker_ownership_auto_claim_enabled = bool(worker_ownership_auto_claim_enabled)
        self._worker_ownership_auto_claim_gate_enforced = bool(
            worker_ownership_auto_claim_gate_enforced
        )
        self._worker_ownership_auto_claim_production_gate_ready = bool(
            worker_ownership_auto_claim_production_gate_ready
        )
        self._worker_ownership_auto_claim_idempotency_evidence_ready = bool(
            worker_ownership_auto_claim_idempotency_evidence_ready
        )
        self._worker_ownership_auto_claim_audit_evidence_ready = bool(
            worker_ownership_auto_claim_audit_evidence_ready
        )
        self._worker_ownership_auto_claim_rollout_decision_recorded = bool(
            worker_ownership_auto_claim_rollout_decision_recorded
        )
        self._worker_ownership_auto_claim_allowed_entrypoints = [
            str(item or "").strip()
            for item in (worker_ownership_auto_claim_allowed_entrypoints or [])
            if str(item or "").strip()
        ]
        self._worker_ownership_worker_id = str(worker_ownership_worker_id or "").strip() or "embedded_runtime_recovery"

    def build_contract(self) -> Dict[str, Any]:
        return build_embedded_sdk_contract()

    def _get_tool_runtime_service(self) -> Any:
        if self._tool_runtime_service is None:
            self._tool_runtime_service = get_tool_runtime_service()
        return self._tool_runtime_service

    def _tool_runtime_service_available(self) -> bool:
        runtime_service = self._get_tool_runtime_service()
        return callable(getattr(runtime_service, "execute_tool", None))

    def create_run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(payload or {})
        run_context = AgentRunContext(
            conversation_id=_normalize_optional_int(payload.get("conversation_id")),
            user_id=_normalize_optional_int(payload.get("user_id")),
            model_name=str(payload.get("model_name") or "unknown").strip() or "unknown",
            parent_run_id=_normalize_optional_str(payload.get("parent_run_id")),
            run_kind=_normalize_run_kind(payload.get("run_kind")),
        )
        run_context.metadata.update(dict(payload.get("metadata") or {}))
        if "input" in payload:
            run_context.metadata.setdefault("input", payload.get("input"))
        self._runs[run_context.run_id] = run_context
        self._events[run_context.run_id] = []
        self._persist_run_context(run_context)
        self._persist_run_events(run_context.run_id)

        event_factory = self._event_factory(run_context)
        self._append_event(
            run_context.run_id,
            event_factory.build(
                AgentEventType.STATUS,
                {
                    "status_kind": "run_created",
                    "summary": "Embedded SDK run created",
                    "run": run_context.snapshot(),
                },
            ).to_dict(),
        )

        approval_request = None
        approval_payload = payload.get("approval_request")
        if isinstance(approval_payload, dict):
            approval_request = self._create_pending_approval(
                run_context=run_context,
                approval_payload=approval_payload,
            )

        result = {
            "run": run_context.snapshot(),
            "events": list(self._events[run_context.run_id]),
        }
        if approval_request is not None:
            result["approval_request"] = approval_request.to_dict()
        return result

    def stream_events(self, run_id: str) -> Iterable[Dict[str, Any]]:
        normalized_run_id = _normalize_required_str(run_id, "run_id")
        if normalized_run_id not in self._runs:
            self._load_run_context_from_store(normalized_run_id)
        if normalized_run_id not in self._runs:
            raise KeyError(f"Embedded SDK run `{normalized_run_id}` is not registered.")
        for event in self._events.get(normalized_run_id, []):
            yield dict(event)

    def register_tool(
        self,
        tool_definition: ToolSpec | Dict[str, Any],
        *,
        handler: Callable[[Dict[str, Any]], Any] | None = None,
        parameters: Dict[str, Any] | None = None,
        **tool_fields: Any,
    ) -> Dict[str, Any]:
        tool_spec = _normalize_embedded_tool_spec(tool_definition, **tool_fields)
        runtime_service = self._get_tool_runtime_service()
        registry = getattr(runtime_service, "tool_registry", None)
        if registry is None:
            return {
                "status": "unavailable",
                "tool_spec": tool_spec.to_dict(),
                "handler_registered": False,
                "tool_registry_bridge": {
                    "tool_runtime_service": runtime_service is not None,
                    "tool_registry": False,
                    "tool_spec_registered": False,
                    "executable_registered": False,
                },
                "error": "tool runtime registry is unavailable",
            }

        tool_spec_registered = False
        register_tool_spec = getattr(registry, "register_tool_spec", None)
        if callable(register_tool_spec):
            register_tool_spec(tool_spec)
            tool_spec_registered = True

        executable_registered = False
        if handler is not None:
            register_tool = getattr(registry, "register", None)
            if callable(register_tool):
                register_tool(_EmbeddedRegisteredTool(tool_spec=tool_spec, handler=handler, parameters=parameters))
                executable_registered = True

        runtime_contract = {}
        build_runtime_contract = getattr(runtime_service, "build_runtime_contract", None)
        if callable(build_runtime_contract):
            runtime_contract = dict(build_runtime_contract() or {})

        return {
            "status": "registered" if tool_spec_registered or executable_registered else "metadata_not_registered",
            "tool_spec": tool_spec.to_dict(),
            "handler_registered": executable_registered,
            "tool_registry_bridge": {
                "tool_runtime_service": True,
                "tool_registry": True,
                "tool_spec_registered": tool_spec_registered,
                "executable_registered": executable_registered,
            },
            "runtime_contract": {
                "contract_version": runtime_contract.get("contract_version"),
                "tool_spec_count": runtime_contract.get("tool_spec_count", 0),
                "total_tools": runtime_contract.get("total_tools", 0),
                "tool_registry_status": runtime_contract.get("tool_registry_status", "unknown"),
            },
        }

    def list_continuation_bindings(self) -> Dict[str, Any]:
        if self._continuation_registry is None:
            return {
                "registry_type": None,
                "total_bindings": 0,
                "bindings": [],
            }
        build_catalog = getattr(self._continuation_registry, "build_catalog", None)
        if not callable(build_catalog):
            return {
                "registry_type": type(self._continuation_registry).__name__,
                "total_bindings": 0,
                "bindings": [],
            }
        return dict(build_catalog() or {})

    def probe_run_recovery(self, run_id: str) -> Dict[str, Any]:
        normalized_run_id = _normalize_required_str(run_id, "run_id")
        run_context = self._runs.get(normalized_run_id)
        if run_context is None:
            run_context = self._load_run_context_from_store(normalized_run_id)
        if run_context is None:
            raise KeyError(f"Embedded SDK run `{normalized_run_id}` is not registered.")

        probe = self._evaluate_run_recovery(run_context)
        self._persist_run_context(run_context)
        event_factory = self._event_factory(run_context)
        self._append_event(
            normalized_run_id,
            event_factory.build(
                AgentEventType.STATUS,
                {
                    "status_kind": "recovery_probe_evaluated",
                    "summary": "Embedded SDK evaluated recovery availability",
                    "recovery": dict(probe),
                },
                iteration=run_context.iteration,
            ).to_dict(),
        )
        return dict(probe)

    def submit_approval(
        self,
        approval_request_id: str,
        decision: str,
        *,
        retry_attempt: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        normalized_request_id = _normalize_required_str(approval_request_id, "approval_request_id")
        normalized_decision = _normalize_approval_decision(decision)
        approval = self._approvals.get(normalized_request_id)
        if approval is None:
            approval = self._load_approval_from_store(normalized_request_id)
        if approval is None:
            raise KeyError(f"Embedded SDK approval request `{normalized_request_id}` is not registered.")

        run_context = self._runs.get(str(approval.run_id or ""))
        if run_context is None:
            run_context = self._load_run_context_from_store(str(approval.run_id or ""))

        approval_engine = get_approval_engine_service()
        submission = approval_engine.submit_approval_decision(
            approval,
            normalized_decision,
            completed_at=_utc_now(),
        )
        submission_status = str(submission.get("status") or "").strip()
        if submission_status in {"replayed", "ignored"}:
            if run_context is not None:
                event_factory = self._event_factory(run_context)
                self._append_event(
                    run_context.run_id,
                    event_factory.build(
                        AgentEventType.STATUS,
                        {
                            "status_kind": str(submission.get("event_status_kind") or f"approval_{submission_status}"),
                            "approval_request_id": normalized_request_id,
                            "approval_request": approval.to_dict(),
                            "original_decision": str(submission.get("original_decision") or "").strip(),
                            "attempted_decision": str(submission.get("attempted_decision") or "").strip(),
                            "approval_submission": dict(submission),
                            "summary": "Embedded SDK ignored resolved approval submission"
                            if submission_status == "ignored"
                            else "Embedded SDK replayed resolved approval submission",
                        },
                        iteration=run_context.iteration,
                    ).to_dict(),
                )
                self._persist_run_context(run_context)
            return {
                "approval_request": approval.to_dict(),
                "approval_submission": submission,
                "run": run_context.snapshot() if run_context is not None else None,
            }

        if run_context is not None:
            event_factory = self._event_factory(run_context)
            self._append_event(
                run_context.run_id,
                event_factory.build(
                    AgentEventType.STATUS,
                    {
                        "status_kind": "approval_resolved",
                        "approval_request_id": normalized_request_id,
                        "decision": normalized_decision,
                        "approval_request": approval.to_dict(),
                        "summary": f"Embedded SDK approval {normalized_decision}",
                    },
                ).to_dict(),
            )
            if (
                run_context.state == AgentState.WAITING_APPROVAL
                and normalized_decision == "approved"
                and (
                    normalized_request_id in self._tool_continuations
                    or self._get_tool_continuation_descriptor(normalized_request_id)
                )
            ):
                self._resume_tool_continuation(
                    request_id=normalized_request_id,
                    run_context=run_context,
                    event_factory=event_factory,
                    retry_attempt=retry_attempt,
                )
            if normalized_decision != "approved":
                persisted_tool_descriptor = self._get_tool_continuation_descriptor(normalized_request_id)
                persisted_loop_descriptor = self._get_loop_continuation_descriptor(run_context.run_id)
                has_pending_continuation = bool(
                    normalized_request_id in self._tool_continuations
                    or persisted_tool_descriptor
                    or run_context.metadata.get("tool_approval_continuation")
                    or persisted_loop_descriptor
                    or run_context.metadata.get("loop_continuation")
                )
                if has_pending_continuation:
                    discarded = self._tool_continuations.pop(normalized_request_id, None)
                    self._loop_continuations.pop(run_context.run_id, None)
                    self._delete_tool_continuation_descriptor(normalized_request_id)
                    self._delete_loop_continuation_descriptor(run_context.run_id)
                    tool_name = (
                        ((discarded or {}).get("tool_decision") or {}).get("tool_name")
                        or (persisted_tool_descriptor or {}).get("tool_name")
                        or (run_context.metadata.get("tool_approval_continuation") or {}).get("tool_name")
                    )
                    run_context.metadata["tool_approval_continuation"] = build_tool_approval_continuation_descriptor(
                        request_id=normalized_request_id,
                        status="discarded",
                        tool_name=tool_name,
                        decision=normalized_decision,
                    )
                    previous_loop_continuation = dict(
                        run_context.metadata.get("loop_continuation")
                        or persisted_loop_descriptor
                        or {}
                    )
                    loop_continuation = {
                        **previous_loop_continuation,
                        **build_loop_continuation_descriptor(
                            request_id=normalized_request_id,
                            status="discarded",
                            decision=normalized_decision,
                        ),
                    }
                    run_context.metadata["loop_continuation"] = loop_continuation
                    self._persist_run_context(run_context)
                    self._append_event(
                        run_context.run_id,
                        event_factory.build(
                            AgentEventType.STATUS,
                            {
                                "status_kind": "loop_continuation_discarded",
                                "approval_request_id": normalized_request_id,
                                "loop_continuation": dict(loop_continuation),
                                "summary": "Embedded SDK discarded loop continuation",
                            },
                            iteration=run_context.iteration,
                        ).to_dict(),
                    )
            if run_context.state in {AgentState.WAITING_APPROVAL, AgentState.TOOL_CALLING}:
                transition = run_context.transition_to(
                    AgentState.OBSERVING,
                    stop_reason=f"approval_{normalized_decision}",
                )
                self._append_event(
                    run_context.run_id,
                    event_factory.build_state_event(
                        previous_state=transition["previous_state"],
                        state=transition["state"],
                        stop_reason=transition["stop_reason"],
                        iteration=run_context.iteration,
                    ).to_dict(),
                )
            self._persist_approval(approval)
            self._persist_run_context(run_context)

        return {
            "approval_request": approval.to_dict(),
            "approval_submission": {
                **dict(submission),
            },
            "run": run_context.snapshot() if run_context is not None else None,
        }

    def resume_run(
        self,
        run_id: str,
        *,
        continue_loop: bool = False,
        retry_attempt: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        normalized_run_id = _normalize_required_str(run_id, "run_id")
        run_context = self._runs.get(normalized_run_id)
        if run_context is None:
            run_context = self._load_run_context_from_store(normalized_run_id)
        if run_context is None:
            raise KeyError(f"Embedded SDK run `{normalized_run_id}` is not registered.")
        if run_context.state != AgentState.OBSERVING:
            raise ValueError(
                f"Embedded SDK run `{normalized_run_id}` is not ready to resume from `{run_context.state.value}`."
            )
        if continue_loop:
            return self._continue_observing_loop(
                normalized_run_id,
                run_context,
                retry_attempt=retry_attempt,
            )

        previous_state = run_context.state.value
        iteration = run_context.begin_iteration()
        run_context.stop_reason = "run_resumed"
        run_context.last_state_transition["stop_reason"] = "run_resumed"
        if run_context.state_history:
            run_context.state_history[-1]["stop_reason"] = "run_resumed"
        run_context.metadata["last_state_transition"] = dict(run_context.last_state_transition)
        run_context.metadata["state_history"] = list(run_context.state_history)

        event_factory = self._event_factory(run_context)
        self._append_event(
            normalized_run_id,
            event_factory.build(
                AgentEventType.STATUS,
                {
                    "status_kind": "run_resumed",
                    "summary": "Embedded SDK run resumed",
                    "previous_state": previous_state,
                    "state": run_context.state.value,
                    "iteration": iteration,
                    "run": run_context.snapshot(),
                },
                iteration=iteration,
            ).to_dict(),
        )
        self._append_event(
            normalized_run_id,
            event_factory.build_state_event(
                previous_state=previous_state,
                state=run_context.state.value,
                stop_reason=run_context.stop_reason,
                iteration=iteration,
            ).to_dict(),
        )
        self._persist_run_context(run_context)
        return {
            "run": run_context.snapshot(),
            "events": list(self._events.get(normalized_run_id, [])),
        }

    def schedule_recovery_retry(
        self,
        run_id: str,
        *,
        enabled: bool = False,
        production_automatic_retry: bool = False,
        audit_recorder: Any | None = None,
        user_id: int | None = None,
        conversation_id: int | None = None,
    ) -> Dict[str, Any]:
        from .recovery_retry_scheduler import RecoveryRetryScheduler

        scheduler = RecoveryRetryScheduler(
            sdk=self,
            enabled=enabled,
            production_automatic_retry=production_automatic_retry,
            audit_recorder=audit_recorder,
            user_id=user_id,
            conversation_id=conversation_id,
        )
        return scheduler.schedule_next_attempt(run_id)

    def delegate_run(self, parent_run_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        normalized_parent_run_id = _normalize_required_str(parent_run_id, "parent_run_id")
        parent_context = self._runs.get(normalized_parent_run_id)
        if parent_context is None:
            parent_context = self._load_run_context_from_store(normalized_parent_run_id)
        if parent_context is None:
            raise KeyError(f"Embedded SDK parent run `{normalized_parent_run_id}` is not registered.")

        child_payload = self._prepare_child_delegate_payload(
            parent_context=parent_context,
            payload=payload,
        )
        child_executor_preflight = self.evaluate_child_executor_preflight(
            child_payload,
            parent_run_id=normalized_parent_run_id,
        )
        child_payload["metadata"]["child_executor_preflight"] = dict(child_executor_preflight)

        child_result = self.create_run(child_payload)
        child_run = child_result["run"]
        parent_event_factory = self._event_factory(parent_context)
        self._append_event(
            normalized_parent_run_id,
            parent_event_factory.build(
                AgentEventType.STATUS,
                {
                    "status_kind": "child_run_created",
                    "summary": "Embedded SDK child run created",
                    "child_run_id": child_run["run_id"],
                    "child_run": child_run,
                    "child_executor_preflight": dict(child_executor_preflight),
                },
            ).to_dict(),
        )
        return {
            **child_result,
            "parent_run": parent_context.snapshot(),
            "child_executor_preflight": dict(child_executor_preflight),
        }

    def evaluate_child_executor_preflight(
        self,
        payload: Dict[str, Any] | None,
        *,
        parent_run_id: str | None = None,
    ) -> Dict[str, Any]:
        parent_context = None
        normalized_parent_run_id = str(parent_run_id or "").strip()
        if normalized_parent_run_id:
            parent_context = self._runs.get(normalized_parent_run_id)
            if parent_context is None:
                parent_context = self._load_run_context_from_store(normalized_parent_run_id)
            if parent_context is None:
                raise KeyError(f"Embedded SDK parent run `{normalized_parent_run_id}` is not registered.")
        prepared_payload = self._prepare_child_delegate_payload(
            parent_context=parent_context,
            payload=payload,
        )
        return build_child_executor_preflight_contract(
            payload=prepared_payload,
            workspace_store=self._workspace_store,
        )

    def evaluate_child_executor_gate(
        self,
        payload: Dict[str, Any] | None,
        *,
        parent_run_id: str | None = None,
    ) -> Dict[str, Any]:
        preflight = self.evaluate_child_executor_preflight(
            payload,
            parent_run_id=parent_run_id,
        )
        return build_child_executor_gate_contract(preflight=preflight)

    def evaluate_child_executor_routing(
        self,
        payload: Dict[str, Any] | None,
        *,
        parent_run_id: str | None = None,
    ) -> Dict[str, Any]:
        gate = self.evaluate_child_executor_gate(
            payload,
            parent_run_id=parent_run_id,
        )
        return build_child_executor_routing_contract(gate=gate)

    def bind_child_executor_routing(
        self,
        payload: Dict[str, Any] | None,
        *,
        parent_run_id: str | None = None,
    ) -> Dict[str, Any]:
        parent_context = None
        normalized_parent_run_id = str(parent_run_id or "").strip()
        if normalized_parent_run_id:
            parent_context = self._runs.get(normalized_parent_run_id)
            if parent_context is None:
                parent_context = self._load_run_context_from_store(normalized_parent_run_id)
            if parent_context is None:
                raise KeyError(f"Embedded SDK parent run `{normalized_parent_run_id}` is not registered.")
        route = self.evaluate_child_executor_routing(
            payload,
            parent_run_id=normalized_parent_run_id or None,
        )
        binding = build_child_executor_binding_contract(
            route=route,
            parent_run_id=normalized_parent_run_id or None,
        )
        if parent_context is not None:
            binding_records = list(parent_context.metadata.get("child_executor_bindings") or [])
            binding_records.append({
                "binding_id": binding["binding_id"],
                "binding_status": binding["binding_status"],
                "executor_path": binding["executor_path"],
                "recommended_action": binding["recommended_action"],
            })
            parent_context.metadata["child_executor_bindings"] = binding_records
            self._persist_run_context(parent_context)
            self._append_event(
                normalized_parent_run_id,
                self._event_factory(parent_context).build(
                    AgentEventType.STATUS,
                    {
                        "status_kind": "child_executor_binding_prepared",
                        "summary": "Embedded SDK child executor binding prepared",
                        "child_executor_binding": dict(binding),
                    },
                    iteration=parent_context.iteration,
                ).to_dict(),
            )
        return dict(binding)

    def execute_bound_child_executor_stub(
        self,
        binding: Dict[str, Any] | None,
        *,
        parent_run_id: str | None = None,
    ) -> Dict[str, Any]:
        normalized_parent_run_id = str(parent_run_id or "").strip()
        parent_context = None
        if normalized_parent_run_id:
            parent_context = self._runs.get(normalized_parent_run_id)
            if parent_context is None:
                parent_context = self._load_run_context_from_store(normalized_parent_run_id)
            if parent_context is None:
                raise KeyError(f"Embedded SDK parent run `{normalized_parent_run_id}` is not registered.")
        stub = build_child_executor_stub_contract(binding=dict(binding or {}))
        if parent_context is not None:
            stub_records = list(parent_context.metadata.get("child_executor_stub_records") or [])
            stub_records.append({
                "binding_id": stub["binding_id"],
                "stub_status": stub["stub_status"],
                "executor_path": stub["executor_path"],
                "recommended_action": stub["recommended_action"],
            })
            parent_context.metadata["child_executor_stub_records"] = stub_records
            self._persist_run_context(parent_context)
            self._append_event(
                normalized_parent_run_id,
                self._event_factory(parent_context).build(
                    AgentEventType.STATUS,
                    {
                        "status_kind": "child_executor_stub_recorded",
                        "summary": "Embedded SDK child executor stub recorded",
                        "child_executor_stub": dict(stub),
                    },
                    iteration=parent_context.iteration,
                ).to_dict(),
            )
        return dict(stub)

    def execute_bound_child_executor(
        self,
        binding: Dict[str, Any] | None,
        *,
        parent_run_id: str | None = None,
    ) -> Dict[str, Any]:
        normalized_parent_run_id = str(parent_run_id or "").strip()
        parent_context = None
        if normalized_parent_run_id:
            parent_context = self._runs.get(normalized_parent_run_id)
            if parent_context is None:
                parent_context = self._load_run_context_from_store(normalized_parent_run_id)
            if parent_context is None:
                raise KeyError(f"Embedded SDK parent run `{normalized_parent_run_id}` is not registered.")
        execution = build_child_executor_execution_contract(binding=dict(binding or {}))
        if parent_context is not None:
            execution_records = list(parent_context.metadata.get("child_executor_execution_records") or [])
            execution_records.append({
                "binding_id": execution["binding_id"],
                "execution_status": execution["execution_status"],
                "executor_path": execution["executor_path"],
                "recommended_action": execution["recommended_action"],
                "intent_label": str((execution.get("output_payload") or {}).get("intent_label") or "").strip(),
                "result_type": str((((execution.get("output_payload") or {}).get("business_result") or {}).get("result_type")) or "").strip(),
                "conclusion": str((((execution.get("output_payload") or {}).get("business_result") or {}).get("conclusion")) or "").strip(),
                "entities": list((execution.get("output_payload") or {}).get("entities") or []),
                "focus_points": list((execution.get("output_payload") or {}).get("focus_points") or []),
                "action_items": list((execution.get("output_payload") or {}).get("action_items") or []),
            })
            parent_context.metadata["child_executor_execution_records"] = execution_records
            self._persist_run_context(parent_context)
            self._append_event(
                normalized_parent_run_id,
                self._event_factory(parent_context).build(
                    AgentEventType.STATUS,
                    {
                        "status_kind": "child_executor_executed",
                        "summary": "Embedded SDK child executor skeleton executed",
                        "child_executor_execution": dict(execution),
                    },
                    iteration=parent_context.iteration,
                ).to_dict(),
            )
        return dict(execution)

    def merge_child_executor_output(
        self,
        execution: Dict[str, Any] | None,
        *,
        parent_run_id: str | None = None,
    ) -> Dict[str, Any]:
        normalized_parent_run_id = str(parent_run_id or "").strip()
        parent_context = None
        if normalized_parent_run_id:
            parent_context = self._runs.get(normalized_parent_run_id)
            if parent_context is None:
                parent_context = self._load_run_context_from_store(normalized_parent_run_id)
            if parent_context is None:
                raise KeyError(f"Embedded SDK parent run `{normalized_parent_run_id}` is not registered.")
        previous_semantics = {}
        if parent_context is not None:
            previous_semantics = dict(parent_context.metadata.get("child_executor_merged_semantics") or {})
        merge = build_child_executor_merge_contract(
            execution=dict(execution or {}),
            previous_semantics=previous_semantics,
        )
        if parent_context is not None:
            merge_records = list(parent_context.metadata.get("child_executor_merge_records") or [])
            merge_records.append({
                "binding_id": str((execution or {}).get("binding_id") or "").strip(),
                "merge_status": merge["merge_status"],
                "merge_strategy": merge["merge_strategy"],
                "intent_label": merge["intent_label"],
                "merge_behavior": dict(merge["merge_behavior"]),
                "merged_summary": merge["merged_summary"],
                "merged_semantics": dict(merge["merged_semantics"]),
                "artifact_id": str((merge.get("artifact_ref") or {}).get("artifact_id") or "").strip(),
            })
            parent_context.metadata["child_executor_merge_records"] = merge_records
            if merge["merge_status"] == "merged":
                parent_context.metadata["child_executor_merged_output"] = merge["merged_output"]
                parent_context.metadata["child_executor_merged_summary"] = merge["merged_summary"]
                parent_context.metadata["child_executor_merged_semantics"] = dict(merge["merged_semantics"])
            self._persist_run_context(parent_context)
            self._append_event(
                normalized_parent_run_id,
                self._event_factory(parent_context).build(
                    AgentEventType.STATUS,
                    {
                        "status_kind": "child_executor_output_merged",
                        "summary": "Embedded SDK child executor output merged",
                        "child_executor_merge": dict(merge),
                    },
                    iteration=parent_context.iteration,
                ).to_dict(),
            )
        return dict(merge)

    def list_child_executor_outputs(self, parent_run_id: str) -> Dict[str, Any]:
        normalized_parent_run_id = _normalize_required_str(parent_run_id, "parent_run_id")
        parent_context = self._runs.get(normalized_parent_run_id)
        if parent_context is None:
            parent_context = self._load_run_context_from_store(normalized_parent_run_id)
        if parent_context is None:
            raise KeyError(f"Embedded SDK parent run `{normalized_parent_run_id}` is not registered.")

        execution_records = list(parent_context.metadata.get("child_executor_execution_records") or [])
        merge_records = list(parent_context.metadata.get("child_executor_merge_records") or [])
        merged_output = str(parent_context.metadata.get("child_executor_merged_output") or "").strip()
        merged_summary = str(parent_context.metadata.get("child_executor_merged_summary") or "").strip()

        records = []
        max_len = max(len(execution_records), len(merge_records))
        for index in range(max_len):
            execution_record = dict(execution_records[index] or {}) if index < len(execution_records) else {}
            merge_record = dict(merge_records[index] or {}) if index < len(merge_records) else {}
            binding_id = str(
                execution_record.get("binding_id")
                or merge_record.get("binding_id")
                or ""
            ).strip()
            records.append({
                "binding_id": binding_id,
                "execution_status": str(execution_record.get("execution_status") or "").strip(),
                "executor_path": str(execution_record.get("executor_path") or "").strip(),
                "intent_label": str(execution_record.get("intent_label") or "").strip(),
                "result_type": str(execution_record.get("result_type") or "").strip(),
                "conclusion": str(execution_record.get("conclusion") or "").strip(),
                "entities": list(execution_record.get("entities") or []),
                "focus_points": list(execution_record.get("focus_points") or []),
                "action_items": list(execution_record.get("action_items") or []),
                "merge_status": str(merge_record.get("merge_status") or "").strip(),
                "merge_strategy": str(merge_record.get("merge_strategy") or "").strip(),
                "merge_behavior": dict(merge_record.get("merge_behavior") or {}),
                "merged_semantics": dict(merge_record.get("merged_semantics") or {}),
                "merged_summary": str(merge_record.get("merged_summary") or "").strip(),
                "artifact_id": str(merge_record.get("artifact_id") or "").strip(),
            })

        return {
            "contract_version": "phase-ii-child-executor-replay-v1",
            "parent_run_id": normalized_parent_run_id,
            "record_count": len(records),
            "records": records,
            "latest_merged_summary": merged_summary,
            "latest_merged_output": merged_output,
            "latest_merged_semantics": dict(parent_context.metadata.get("child_executor_merged_semantics") or {}),
        }

    def summarize_child_executor_outputs(self, parent_run_id: str) -> Dict[str, Any]:
        replay = self.list_child_executor_outputs(parent_run_id)
        records = list(replay.get("records") or [])
        artifact_ids = [
            str(record.get("artifact_id") or "").strip()
            for record in records
            if str(record.get("artifact_id") or "").strip()
        ]
        merge_strategies = [
            str(record.get("merge_strategy") or "").strip()
            for record in records
            if str(record.get("merge_strategy") or "").strip()
        ]
        result_types = [
            str(record.get("result_type") or "").strip()
            for record in records
            if str(record.get("result_type") or "").strip()
        ]
        entity_sets = [
            list(record.get("entities") or [])
            for record in records
            if list(record.get("entities") or [])
        ]
        focus_point_sets = [
            list(record.get("focus_points") or [])
            for record in records
            if list(record.get("focus_points") or [])
        ]
        action_item_sets = [
            list(record.get("action_items") or [])
            for record in records
            if list(record.get("action_items") or [])
        ]
        conclusions = [
            str(record.get("conclusion") or "").strip()
            for record in records
            if str(record.get("conclusion") or "").strip()
        ]
        latest_artifact_id = artifact_ids[-1] if artifact_ids else ""
        latest_merge_strategy = merge_strategies[-1] if merge_strategies else ""
        latest_result_type = result_types[-1] if result_types else ""
        latest_conclusion = conclusions[-1] if conclusions else ""
        latest_entities = entity_sets[-1] if entity_sets else []
        latest_focus_points = focus_point_sets[-1] if focus_point_sets else []
        latest_action_items = action_item_sets[-1] if action_item_sets else []
        latest_merged_semantics = dict(replay.get("latest_merged_semantics") or {})
        return {
            "contract_version": "phase-ii-child-executor-artifact-summary-v1",
            "parent_run_id": str(replay.get("parent_run_id") or "").strip(),
            "record_count": int(replay.get("record_count") or 0),
            "latest_artifact_id": latest_artifact_id,
            "latest_merge_strategy": latest_merge_strategy,
            "latest_result_type": latest_result_type,
            "latest_conclusion": latest_conclusion,
            "latest_merged_summary": str(replay.get("latest_merged_summary") or "").strip(),
            "latest_merged_output": str(replay.get("latest_merged_output") or "").strip(),
            "latest_merged_semantics": latest_merged_semantics,
            "latest_entities": latest_entities,
            "latest_focus_points": latest_focus_points,
            "latest_action_items": latest_action_items,
            "artifact_ids": artifact_ids,
            "merge_strategies": merge_strategies,
            "result_types": result_types,
            "entity_sets": entity_sets,
        }

    def summarize_child_executor_merged_semantics(self, parent_run_id: str) -> Dict[str, Any]:
        summary = self.summarize_child_executor_outputs(parent_run_id)
        merged_semantics = dict(summary.get("latest_merged_semantics") or {})
        intent_label = _normalize_child_executor_intent_label(merged_semantics.get("intent_label"))
        merge_behavior = dict(merged_semantics.get("merge_behavior") or {})
        normalized_semantics = {
            "intent_label": intent_label,
            "merge_behavior": dict(merge_behavior),
            "entities": list(merged_semantics.get("entities") or []),
            "focus_points": list(merged_semantics.get("focus_points") or []),
            "action_items": list(merged_semantics.get("action_items") or []),
            "latest_conclusion": str(merged_semantics.get("latest_conclusion") or "").strip(),
        }
        return {
            "contract_version": "phase-ii-child-executor-merged-semantics-v2",
            "parent_run_id": str(summary.get("parent_run_id") or "").strip(),
            "record_count": int(summary.get("record_count") or 0),
            "available": bool(merged_semantics),
            "intent_catalog_version": CHILD_EXECUTOR_INTENT_CATALOG_VERSION,
            "supported_intents": list(CHILD_EXECUTOR_SUPPORTED_INTENTS),
            "intent_label": normalized_semantics["intent_label"],
            "entities": list(normalized_semantics["entities"]),
            "focus_points": list(normalized_semantics["focus_points"]),
            "action_items": list(normalized_semantics["action_items"]),
            "merge_behavior": {
                "entities": str(merge_behavior.get("entities") or "").strip(),
                "focus_points": str(merge_behavior.get("focus_points") or "").strip(),
                "action_items": str(merge_behavior.get("action_items") or "").strip(),
            },
            "merged_sections": _build_child_executor_merged_sections(normalized_semantics),
            "parent_state_surface": _build_child_executor_parent_state_surface(normalized_semantics),
            "latest_merged_summary": str(summary.get("latest_merged_summary") or "").strip(),
            "latest_merged_output": str(summary.get("latest_merged_output") or "").strip(),
            "latest_merge_strategy": str(summary.get("latest_merge_strategy") or "").strip(),
            "latest_result_type": str(summary.get("latest_result_type") or "").strip(),
        }

    def create_artifact(self, run_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        normalized_run_id = _normalize_required_str(run_id, "run_id")
        run_context = self._runs.get(normalized_run_id)
        if run_context is None:
            run_context = self._load_run_context_from_store(normalized_run_id)
        if run_context is None:
            raise KeyError(f"Embedded SDK run `{normalized_run_id}` is not registered.")

        artifact = self._build_artifact_dict(
            run_context=run_context,
            run_id=normalized_run_id,
            payload=dict(payload or {}),
        )
        self._artifacts[str(artifact["artifact_id"])] = artifact

        artifact_refs = list(run_context.metadata.get("artifacts") or [])
        artifact_ref = {
            "artifact_id": artifact["artifact_id"],
            "kind": artifact["kind"],
            "uri": artifact["uri"],
            "metadata": dict(artifact["metadata"]),
        }
        artifact_refs.append(artifact_ref)
        run_context.metadata["artifacts"] = artifact_refs
        self._persist_run_context(run_context)

        event_factory = self._event_factory(run_context)
        self._append_event(
            normalized_run_id,
            event_factory.build(
                AgentEventType.STATUS,
                {
                    "status_kind": "artifact_created",
                    "summary": "Embedded SDK artifact created",
                    "artifact": dict(artifact),
                    "artifact_ref": artifact_ref,
                },
                iteration=run_context.iteration,
            ).to_dict(),
        )
        return {
            "artifact": dict(artifact),
            "run": run_context.snapshot(),
        }

    def list_artifacts(self, run_id: str) -> Dict[str, Any]:
        normalized_run_id = _normalize_required_str(run_id, "run_id")
        run_context = self._runs.get(normalized_run_id)
        if run_context is None:
            run_context = self._load_run_context_from_store(normalized_run_id)
        if run_context is None:
            raise KeyError(f"Embedded SDK run `{normalized_run_id}` is not registered.")

        artifacts = []
        for artifact_ref in list(run_context.metadata.get("artifacts") or []):
            artifact_id = str((artifact_ref or {}).get("artifact_id") or "").strip()
            if artifact_id and artifact_id in self._artifacts:
                artifacts.append(dict(self._artifacts[artifact_id]))
            elif isinstance(artifact_ref, dict):
                artifacts.append(dict(artifact_ref))
        return {
            "run": run_context.snapshot(),
            "artifacts": artifacts,
        }

    def execute_run(
        self,
        run_id: str,
        *,
        tool_policy: ToolPolicyCallable | None = None,
        tool_executor: ToolExecutorCallable | None = None,
        reflector: ReflectionCallable | None = None,
        reviewer: ReviewCallable | None = None,
        fallback_handler: FallbackCallable | None = None,
        max_iterations: int = 1,
    ) -> Dict[str, Any]:
        normalized_run_id = _normalize_required_str(run_id, "run_id")
        run_context = self._runs.get(normalized_run_id)
        if run_context is None:
            run_context = self._load_run_context_from_store(normalized_run_id)
        if run_context is None:
            raise KeyError(f"Embedded SDK run `{normalized_run_id}` is not registered.")

        effective_tool_policy = tool_policy
        effective_tool_executor = tool_executor
        decision_holder: Dict[str, Any] = {}
        if effective_tool_executor is None and tool_policy is not None and self._tool_runtime_service_available():
            effective_tool_policy = self._bridge_tool_runtime_policy(tool_policy)
            effective_tool_policy = self._capture_tool_policy_decision(effective_tool_policy, decision_holder)
            effective_tool_executor = self._build_tool_runtime_executor(decision_holder)

        result = ExecutionLoopController(
            tool_policy=effective_tool_policy,
            tool_executor=effective_tool_executor,
            reflector=reflector,
            reviewer=reviewer,
            fallback_handler=fallback_handler,
            max_iterations=max_iterations,
        ).run_until_stop(
            run_context,
            event_factory=self._event_factory(run_context),
            append_event=lambda event: self._append_event(normalized_run_id, event),
        )
        approval_request = self._create_loop_tool_approval_if_required(
            run_context,
            tool_executor=effective_tool_executor,
            loop_continuation={
                "reflector": reflector,
                "reviewer": reviewer,
                "fallback_handler": fallback_handler,
                "max_iterations": max_iterations,
            },
        )
        response = {
            "run": result["run"],
            "events": list(self._events.get(normalized_run_id, [])),
        }
        if approval_request is not None:
            response["run"] = run_context.snapshot()
            response["approval_request"] = approval_request.to_dict()
            response["events"] = list(self._events.get(normalized_run_id, []))
        return response

    def _build_artifact_dict(
        self,
        *,
        run_context: AgentRunContext,
        run_id: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        artifact_kind = str(payload.get("kind") or "runtime_artifact").strip() or "runtime_artifact"
        artifact_content = str(payload.get("content") or "")
        artifact_metadata = dict(payload.get("metadata") or {})
        if self._artifact_store is not None:
            stored = self._artifact_store.create_artifact(
                conversation_id=run_context.conversation_id,
                kind=artifact_kind,
                content=artifact_content,
                render_mode=_normalize_optional_str(payload.get("render_mode")),
                card_schema=_normalize_optional_str(payload.get("card_schema")),
                card=dict(payload.get("card") or {}) or None,
                metadata=artifact_metadata,
            )
            return {
                "artifact_id": stored.artifact_id,
                "run_id": run_id,
                "parent_run_id": run_context.parent_run_id,
                "conversation_id": stored.conversation_id,
                "kind": stored.kind,
                "content": stored.content,
                "uri": str(payload.get("uri") or "").strip() or f"artifact://{stored.artifact_id}",
                "created_at": _format_datetime(stored.created_at),
                "render_mode": stored.render_mode,
                "card_schema": stored.card_schema,
                "card": dict(stored.card or {}),
                "metadata": dict(stored.metadata or {}),
            }

        artifact_id = str(payload.get("artifact_id") or "").strip() or f"art_{uuid4().hex}"
        return {
            "artifact_id": artifact_id,
            "run_id": run_id,
            "parent_run_id": run_context.parent_run_id,
            "conversation_id": run_context.conversation_id,
            "kind": artifact_kind,
            "content": artifact_content,
            "uri": str(payload.get("uri") or "").strip() or f"memory://runs/{run_id}/artifacts/{artifact_id}",
            "created_at": str(payload.get("created_at") or _utc_now()),
            "render_mode": _normalize_optional_str(payload.get("render_mode")),
            "card_schema": _normalize_optional_str(payload.get("card_schema")),
            "card": dict(payload.get("card") or {}),
            "metadata": artifact_metadata,
        }

    def _create_pending_approval(
        self,
        *,
        run_context: AgentRunContext,
        approval_payload: Dict[str, Any],
    ) -> ApprovalRequestState:
        request_id = str(approval_payload.get("request_id") or "").strip() or f"apr_{uuid4().hex}"
        approval = get_approval_engine_service().create_tool_approval_request(
            request_id=request_id,
            tool_name=str(approval_payload.get("tool_name") or "").strip() or "embedded_tool",
            tool_args=dict(approval_payload.get("tool_args") or {}),
            context={
                "user_id": run_context.user_id,
                "conversation_id": run_context.conversation_id,
                "run_id": run_context.run_id,
                "parent_run_id": run_context.parent_run_id,
                "run_kind": run_context.run_kind.value,
                "source_event_type": "embedded_sdk_approval_required",
                **dict(approval_payload.get("context") or {}),
            },
            permission_level=str(approval_payload.get("permission_level") or "ask"),
            reason=str(approval_payload.get("reason") or ""),
            reason_code=_normalize_optional_str(approval_payload.get("reason_code")),
            requested_at=str(approval_payload.get("requested_at") or _utc_now()),
            request_metadata=dict(approval_payload.get("request_metadata") or {}),
        )
        self._approvals[request_id] = approval
        planning_transition = run_context.transition_to(AgentState.PLANNING)
        approval_transition = run_context.transition_to(
            AgentState.WAITING_APPROVAL,
            stop_reason="approval_required",
        )
        run_context.set_runtime_marker(approval_request_id=request_id)

        event_factory = self._event_factory(run_context)
        self._append_event(
            run_context.run_id,
            event_factory.build_state_event(
                previous_state=planning_transition["previous_state"],
                state=planning_transition["state"],
                stop_reason=planning_transition["stop_reason"],
                iteration=run_context.iteration,
            ).to_dict(),
        )
        self._append_event(
            run_context.run_id,
            event_factory.build(
                AgentEventType.STATUS,
                {
                    "status_kind": "approval_created",
                    "approval_request_id": request_id,
                    "approval_request": approval.to_dict(),
                    "summary": "Embedded SDK approval request created",
                },
                iteration=run_context.iteration,
            ).to_dict(),
        )
        self._append_event(
            run_context.run_id,
            event_factory.build_state_event(
                previous_state=approval_transition["previous_state"],
                state=approval_transition["state"],
                stop_reason=approval_transition["stop_reason"],
                iteration=run_context.iteration,
            ).to_dict(),
        )
        return approval

    def _create_loop_tool_approval_if_required(
        self,
        run_context: AgentRunContext,
        *,
        tool_executor: ToolExecutorCallable | None = None,
        loop_continuation: Dict[str, Any] | None = None,
    ) -> ApprovalRequestState | None:
        if run_context.stop_reason != "tool_approval_required":
            return None
        existing_request_id = _normalize_optional_str(run_context.metadata.get("approval_request_id"))
        if existing_request_id and existing_request_id in self._approvals:
            return self._approvals[existing_request_id]

        tool_decision = run_context.metadata.get("execution_tool_decision")
        if not isinstance(tool_decision, dict):
            return None
        if str(tool_decision.get("status") or "").strip().lower() != "approval_required":
            return None

        decision_metadata = dict(tool_decision.get("metadata") or {})
        tool_executor_binding_id = self._ensure_continuation_binding(
            tool_executor,
            binding_kind="tool_executor",
            metadata={"tool_name": str(tool_decision.get("tool_name") or "").strip()},
        )
        reflector_binding_id = self._ensure_continuation_binding(
            (loop_continuation or {}).get("reflector"),
            binding_kind="reflector",
        )
        reviewer_binding_id = self._ensure_continuation_binding(
            (loop_continuation or {}).get("reviewer"),
            binding_kind="reviewer",
        )
        fallback_handler_binding_id = self._ensure_continuation_binding(
            (loop_continuation or {}).get("fallback_handler"),
            binding_kind="fallback_handler",
        )
        request_id = (
            _normalize_optional_str(decision_metadata.get("approval_request_id"))
            or _normalize_optional_str(decision_metadata.get("request_id"))
            or f"apr_{uuid4().hex}"
        )
        approval = get_approval_engine_service().create_tool_approval_request(
            request_id=request_id,
            tool_name=str(tool_decision.get("tool_name") or "").strip() or "unknown_tool",
            tool_args=dict(tool_decision.get("tool_args") or {}),
            context={
                "user_id": run_context.user_id,
                "conversation_id": run_context.conversation_id,
                "run_id": run_context.run_id,
                "parent_run_id": run_context.parent_run_id,
                "run_kind": run_context.run_kind.value,
                "source_event_type": "tool_permission_required",
                **dict(decision_metadata.get("context") or {}),
                **{
                    key: value
                    for key, value in run_context.metadata.items()
                    if key in {
                        "agent_id",
                        "agent_role",
                        "plan_id",
                        "plan_item_id",
                        "scheduler_run_id",
                        "child_run_id",
                    }
                },
            },
            permission_level=str(decision_metadata.get("permission_level") or "ask"),
            reason=str(tool_decision.get("reason") or ""),
            reason_code=_normalize_optional_str(decision_metadata.get("reason_code")),
            requested_at=str(decision_metadata.get("requested_at") or _utc_now()),
            request_metadata=dict(decision_metadata.get("request_metadata") or {}),
        )
        self._approvals[request_id] = approval
        run_context.set_runtime_marker(approval_request_id=request_id)
        run_context.metadata["approval_request"] = approval.to_dict()
        if tool_executor is not None:
            self._tool_continuations[request_id] = {
                "kind": "tool_executor",
                "tool_executor": tool_executor,
                "tool_decision": dict(tool_decision),
                "tool_executor_binding_id": tool_executor_binding_id,
            }
            self._loop_continuations[run_context.run_id] = dict(loop_continuation or {})
            run_context.metadata["tool_approval_continuation"] = build_tool_approval_continuation_descriptor(
                request_id=request_id,
                status="pending",
                tool_name=approval.tool_name,
                tool_executor_binding_id=tool_executor_binding_id,
            )
            self._persist_tool_continuation_descriptor(
                request_id,
                dict(run_context.metadata["tool_approval_continuation"]),
            )
        run_context.metadata["loop_continuation"] = build_loop_continuation_descriptor(
            request_id=request_id,
            status="pending",
            resume_mode="observing_to_done",
            source="tool_approval_required",
            has_reflector=callable((loop_continuation or {}).get("reflector")),
            has_reviewer=callable((loop_continuation or {}).get("reviewer")),
            has_fallback_handler=callable((loop_continuation or {}).get("fallback_handler")),
            reflector_binding_id=reflector_binding_id,
            reviewer_binding_id=reviewer_binding_id,
            fallback_handler_binding_id=fallback_handler_binding_id,
            max_iterations=int((loop_continuation or {}).get("max_iterations") or 1),
        )
        self._persist_loop_continuation_descriptor(
            run_context.run_id,
            dict(run_context.metadata["loop_continuation"]),
        )
        self._persist_approval(approval)
        self._persist_run_context(run_context)

        event_factory = self._event_factory(run_context)
        self._append_event(
            run_context.run_id,
            event_factory.build(
                AgentEventType.STATUS,
                {
                    "status_kind": "approval_created",
                    "approval_request_id": request_id,
                    "approval_request": approval.to_dict(),
                    "summary": "Embedded SDK tool approval request created",
                },
                iteration=run_context.iteration,
            ).to_dict(),
        )
        self._append_event(
            run_context.run_id,
            event_factory.build(
                AgentEventType.STATUS,
                {
                    "status_kind": "loop_continuation_registered",
                    "approval_request_id": request_id,
                    "loop_continuation": dict(run_context.metadata.get("loop_continuation") or {}),
                    "summary": "Embedded SDK registered loop continuation",
                },
                iteration=run_context.iteration,
            ).to_dict(),
        )
        return approval

    def _resume_tool_continuation(
        self,
        *,
        request_id: str,
        run_context: AgentRunContext,
        event_factory: AgentEventFactory,
        retry_attempt: Dict[str, Any] | None = None,
    ) -> None:
        continuation = self._tool_continuations.pop(request_id, None)
        reattached_descriptor: Dict[str, Any] | None = None
        if not continuation:
            persisted_descriptor = self._get_tool_continuation_descriptor(request_id)
            if persisted_descriptor:
                if not self._workspace_backend_allows_cross_process_recovery():
                    recovery = self._fail_closed_recovery(
                        run_context=run_context,
                        continuation_kind="tool_approval",
                        continuation_id=request_id,
                    summary="Embedded SDK blocked tool continuation recovery",
                    retry_attempt=retry_attempt,
                )
                    raise ValueError(
                        f"Embedded SDK tool continuation `{request_id}` cannot be recovered: {recovery['recovery_reason']}."
                    )
                loader_candidate = self._load_durable_recovery_candidate(
                    run_id=run_context.run_id,
                    approval_request_id=request_id,
                )
                if str(loader_candidate.get("recovery_reason") or "").strip() == CONTINUATION_RECOVERY_REASON_DESCRIPTOR_CORRUPTED:
                    recovery = self._fail_closed_recovery(
                        run_context=run_context,
                        continuation_kind="tool_approval",
                        continuation_id=request_id,
                        summary="Embedded SDK blocked unsafe tool continuation recovery",
                        recovery_reason_override=CONTINUATION_RECOVERY_REASON_DESCRIPTOR_CORRUPTED,
                        blocked_reason_override=CONTINUATION_RECOVERY_REASON_DESCRIPTOR_CORRUPTED,
                        descriptor=dict(persisted_descriptor),
                        retry_attempt=retry_attempt,
                    )
                    raise ValueError(
                        f"Embedded SDK tool continuation `{request_id}` cannot be recovered: {recovery['recovery_reason']}."
                    )
                reattached = self._reattach_tool_continuation(
                    request_id=request_id,
                    run_context=run_context,
                    descriptor=dict(persisted_descriptor),
                )
                if reattached is not None:
                    continuation = reattached
                    reattached_descriptor = dict(persisted_descriptor)
                else:
                    recovery = self._fail_closed_recovery(
                        run_context=run_context,
                    continuation_kind="tool_approval",
                    continuation_id=request_id,
                    summary="Embedded SDK blocked tool continuation recovery",
                    retry_attempt=retry_attempt,
                )
                    raise ValueError(
                        f"Embedded SDK tool continuation `{request_id}` cannot be recovered: {recovery['recovery_reason']}."
                    )
            else:
                return
        tool_executor = continuation.get("tool_executor")
        if not callable(tool_executor):
            return
        worker_ownership: Dict[str, Any] | None = None
        if reattached_descriptor is not None:
            worker_ownership = self._validate_recovery_worker_ownership(
                run_context=run_context,
                descriptor=reattached_descriptor,
                recovery=None,
                entrypoint="submit_approval.approved",
            )
            if worker_ownership and not bool(worker_ownership.get("owned")):
                recovery = self._fail_closed_recovery(
                    run_context=run_context,
                    continuation_kind="tool_approval",
                    continuation_id=request_id,
                    summary="Embedded SDK blocked tool continuation recovery by worker ownership",
                    recovery_reason_override=str(worker_ownership.get("reason") or "worker_ownership_lost").strip(),
                    blocked_reason_override=str(worker_ownership.get("blocked_reason") or "").strip(),
                    worker_ownership=worker_ownership,
                    descriptor=reattached_descriptor,
                    retry_attempt=retry_attempt,
                )
                raise ValueError(
                    f"Embedded SDK tool continuation `{request_id}` cannot be recovered: {recovery['recovery_reason']}."
                )
            self._record_recovery_operation(
                run_context=run_context,
                entrypoint="submit_approval.approved",
                operation_status="recovered",
                recovery_reason=CONTINUATION_RECOVERY_REASON_READY_VIA_REGISTRY,
                continuation_kind="tool_approval",
                continuation_id=request_id,
                descriptor=reattached_descriptor,
                worker_ownership=worker_ownership,
                retry=self._build_recovery_retry_evidence(
                    retry_attempt=retry_attempt,
                    recovery_reason=CONTINUATION_RECOVERY_REASON_READY_VIA_REGISTRY,
                ),
            )

        iteration = run_context.iteration
        continued_event = event_factory.build(
            AgentEventType.STATUS,
            {
                "status_kind": "tool_approval_continued",
                "approval_request_id": request_id,
                "tool_decision": dict(continuation.get("tool_decision") or {}),
                "summary": "Embedded SDK resumed approved tool execution",
            },
            iteration=iteration,
        ).to_dict()
        self._append_event(run_context.run_id, continued_event)

        previous_approved_tool_execution = run_context.metadata.get("approved_tool_execution")
        run_context.metadata["approved_tool_execution"] = {
            "approval_request_id": request_id,
            "decision": "approved",
            "source": "embedded_sdk_tool_continuation",
        }
        try:
            tool_result = _normalize_tool_result(tool_executor(run_context))
        finally:
            if previous_approved_tool_execution is None:
                run_context.metadata.pop("approved_tool_execution", None)
            else:
                run_context.metadata["approved_tool_execution"] = previous_approved_tool_execution
        if tool_result is None:
            run_context.metadata["tool_approval_continuation"] = build_tool_approval_continuation_descriptor(
                request_id=request_id,
                status="consumed",
                tool_result=None,
            )
            self._persist_tool_continuation_descriptor(
                request_id,
                dict(run_context.metadata["tool_approval_continuation"]),
            )
            self._persist_run_context(run_context)
            return

        tool_transition = run_context.transition_to(AgentState.TOOL_CALLING, stop_reason="tool_calling")
        self._append_event(
            run_context.run_id,
            event_factory.build_state_event(
                previous_state=tool_transition["previous_state"],
                state=tool_transition["state"],
                stop_reason=tool_transition["stop_reason"],
                iteration=iteration,
            ).to_dict(),
        )
        tool_call_id = tool_result.get("tool_call_id") or f"tool_{run_context.iteration}_{len(run_context.tool_history) + 1}"
        tool_result["tool_call_id"] = tool_call_id
        self._append_event(
            run_context.run_id,
            event_factory.build(
                AgentEventType.TOOL_CALL_START,
                {
                    "status_kind": "tool_call_started",
                    "tool_name": tool_result["tool_name"],
                    "args": dict(tool_result["args"]),
                    "tool_call_id": tool_call_id,
                    "approval_request_id": request_id,
                },
                iteration=iteration,
            ).to_dict(),
        )
        run_context.record_tool_result(
            tool_result["tool_name"],
            dict(tool_result["args"]),
            str(tool_result["result"]),
            tool_call_id,
            execution=dict(tool_result.get("execution") or {}),
        )
        self._append_event(
            run_context.run_id,
            event_factory.build(
                AgentEventType.TOOL_RESULT,
                {
                    "status_kind": "tool_result",
                    "tool_name": tool_result["tool_name"],
                    "args": dict(tool_result["args"]),
                    "result": tool_result["result"],
                    "tool_call_id": tool_call_id,
                    "approval_request_id": request_id,
                    "execution": dict(tool_result.get("execution") or {}),
                },
                iteration=iteration,
            ).to_dict(),
        )
        run_context.metadata["tool_approval_continuation"] = build_tool_approval_continuation_descriptor(
            request_id=request_id,
            status="consumed",
            tool_name=tool_result["tool_name"],
            tool_call_id=tool_call_id,
        )
        self._persist_tool_continuation_descriptor(
            request_id,
            dict(run_context.metadata["tool_approval_continuation"]),
        )
        self._persist_run_context(run_context)

    def _continue_observing_loop(
        self,
        run_id: str,
        run_context: AgentRunContext,
        *,
        retry_attempt: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        continuation = dict(self._loop_continuations.pop(run_id, {}))
        reattached_descriptor: Dict[str, Any] | None = None
        if not continuation:
            persisted_descriptor = self._get_loop_continuation_descriptor(run_id)
            if persisted_descriptor:
                if not self._workspace_backend_allows_cross_process_recovery():
                    recovery = self._fail_closed_recovery(
                        run_context=run_context,
                        continuation_kind="loop",
                        continuation_id=run_id,
                        summary="Embedded SDK blocked loop continuation recovery",
                        retry_attempt=retry_attempt,
                    )
                    raise ValueError(
                        f"Embedded SDK loop continuation for run `{run_id}` cannot be recovered: {recovery['recovery_reason']}."
                    )
                loader_candidate = self._load_durable_recovery_candidate(run_id=run_id)
                if str(loader_candidate.get("recovery_reason") or "").strip() == CONTINUATION_RECOVERY_REASON_DESCRIPTOR_CORRUPTED:
                    recovery = self._fail_closed_recovery(
                        run_context=run_context,
                        continuation_kind="loop",
                        continuation_id=run_id,
                        summary="Embedded SDK blocked unsafe loop continuation recovery",
                        recovery_reason_override=CONTINUATION_RECOVERY_REASON_DESCRIPTOR_CORRUPTED,
                        blocked_reason_override=CONTINUATION_RECOVERY_REASON_DESCRIPTOR_CORRUPTED,
                        descriptor=dict(persisted_descriptor),
                        retry_attempt=retry_attempt,
                    )
                    raise ValueError(
                        f"Embedded SDK loop continuation for run `{run_id}` cannot be recovered: {recovery['recovery_reason']}."
                    )
                reattached = self._reattach_loop_continuation(
                    run_id=run_id,
                    descriptor=dict(persisted_descriptor),
                )
                if reattached:
                    continuation = dict(reattached)
                    reattached_descriptor = dict(persisted_descriptor)
                else:
                    recovery = self._fail_closed_recovery(
                        run_context=run_context,
                        continuation_kind="loop",
                        continuation_id=run_id,
                        summary="Embedded SDK blocked loop continuation recovery",
                        retry_attempt=retry_attempt,
                    )
                    raise ValueError(
                        f"Embedded SDK loop continuation for run `{run_id}` cannot be recovered: {recovery['recovery_reason']}."
                    )
        event_factory = self._event_factory(run_context)
        worker_ownership: Dict[str, Any] | None = None
        if reattached_descriptor is not None:
            worker_ownership = self._validate_recovery_worker_ownership(
                run_context=run_context,
                descriptor=reattached_descriptor,
                recovery=None,
                entrypoint="resume_run.continue_loop",
            )
            if worker_ownership and not bool(worker_ownership.get("owned")):
                recovery = self._fail_closed_recovery(
                    run_context=run_context,
                    continuation_kind="loop",
                    continuation_id=run_id,
                    summary="Embedded SDK blocked loop continuation recovery by worker ownership",
                    recovery_reason_override=str(worker_ownership.get("reason") or "worker_ownership_lost").strip(),
                    blocked_reason_override=str(worker_ownership.get("blocked_reason") or "").strip(),
                    worker_ownership=worker_ownership,
                    descriptor=reattached_descriptor,
                    retry_attempt=retry_attempt,
                )
                raise ValueError(
                    f"Embedded SDK loop continuation for run `{run_id}` cannot be recovered: {recovery['recovery_reason']}."
                )
        self._append_event(
            run_id,
            event_factory.build(
                AgentEventType.STATUS,
                {
                    "status_kind": "run_resumed",
                    "summary": "Embedded SDK run resumed into execution loop continuation",
                    "state": run_context.state.value,
                    "run": run_context.snapshot(),
                    "continue_loop": True,
                },
                iteration=run_context.iteration,
            ).to_dict(),
        )
        result = ExecutionLoopController(
            steps=(
                ExecutionLoopStep("observing", AgentState.OBSERVING, "Execution loop resumed observation", "loop_observed"),
                ExecutionLoopStep("finalizing", AgentState.FINALIZING, "Execution loop resumed finalization", "loop_finalizing"),
                ExecutionLoopStep("done", AgentState.DONE, "Execution loop completed after resume", "loop_completed"),
            ),
            reflector=continuation.get("reflector"),
            reviewer=continuation.get("reviewer"),
            fallback_handler=continuation.get("fallback_handler"),
            max_iterations=int(continuation.get("max_iterations") or 1),
        ).run_until_stop(
            run_context,
            event_factory=event_factory,
            append_event=lambda event: self._append_event(run_id, event),
        )
        previous_loop_continuation = dict(run_context.metadata.get("loop_continuation") or {})
        loop_continuation = {
            **previous_loop_continuation,
            **build_loop_continuation_descriptor(
                request_id=str(previous_loop_continuation.get("request_id") or ""),
                status="consumed",
                resume_mode="observing_to_done",
                completed_state=result["run"]["state"],
            ),
        }
        run_context.metadata["loop_continuation"] = loop_continuation
        self._persist_loop_continuation_descriptor(run_id, dict(loop_continuation))
        self._persist_run_context(run_context)
        done_event = None
        existing_events = self._events.get(run_id, [])
        if existing_events and existing_events[-1].get("status_kind") == "execution_loop_done":
            done_event = existing_events.pop()
        if reattached_descriptor is not None:
            self._record_recovery_operation(
                run_context=run_context,
                entrypoint="resume_run.continue_loop",
                operation_status="recovered",
                recovery_reason=CONTINUATION_RECOVERY_REASON_READY_VIA_REGISTRY,
                continuation_kind="loop",
                continuation_id=run_id,
                descriptor=reattached_descriptor,
                worker_ownership=worker_ownership,
                retry=self._build_recovery_retry_evidence(
                    retry_attempt=retry_attempt,
                    recovery_reason=CONTINUATION_RECOVERY_REASON_READY_VIA_REGISTRY,
                ),
            )
        result["run"] = run_context.snapshot()
        self._append_event(
            run_id,
            event_factory.build(
                AgentEventType.STATUS,
                {
                    "status_kind": "loop_continuation_consumed",
                    "loop_continuation": dict(loop_continuation),
                    "summary": "Embedded SDK consumed loop continuation",
                },
                iteration=run_context.iteration,
            ).to_dict(),
        )
        if done_event is not None:
            self._append_event(run_id, done_event)
        return {
            "run": result["run"],
            "events": list(self._events.get(run_id, [])),
        }

    def _evaluate_run_recovery(self, run_context: AgentRunContext) -> Dict[str, Any]:
        loop_descriptor = dict(self._get_loop_continuation_descriptor(run_context.run_id) or {})
        loop_recovery = self._build_recovery_record(
            continuation_kind="loop",
            continuation_id=run_context.run_id,
            descriptor=loop_descriptor,
            executable_available=bool(self._loop_continuations.get(run_context.run_id)),
        )
        if loop_descriptor:
            run_context.metadata["loop_continuation"] = {
                **loop_descriptor,
                **loop_recovery,
            }
            self._persist_loop_continuation_descriptor(
                run_context.run_id,
                dict(run_context.metadata["loop_continuation"]),
            )
        else:
            run_context.metadata["loop_continuation_recovery"] = dict(loop_recovery)

        request_id = str(
            loop_descriptor.get("request_id")
            or (run_context.metadata.get("approval_request") or {}).get("request_id")
            or run_context.metadata.get("approval_request_id")
            or ""
        ).strip()
        approval = None
        if request_id:
            approval = self._approvals.get(request_id)
            if approval is None:
                approval = self._load_approval_from_store(request_id)
            if approval is not None:
                run_context.metadata["approval_request"] = approval.to_dict()
        tool_recovery = None
        if request_id:
            tool_descriptor = dict(self._get_tool_continuation_descriptor(request_id) or {})
            tool_recovery = self._build_recovery_record(
                continuation_kind="tool_approval",
                continuation_id=request_id,
                descriptor=tool_descriptor,
                executable_available=bool(self._tool_continuations.get(request_id)),
            )
            if tool_descriptor:
                run_context.metadata["tool_approval_continuation"] = {
                    **tool_descriptor,
                    **tool_recovery,
                }
                self._persist_tool_continuation_descriptor(
                    request_id,
                    dict(run_context.metadata["tool_approval_continuation"]),
                )
            else:
                run_context.metadata["tool_approval_continuation_recovery"] = dict(tool_recovery)

        recoveries = [loop_recovery]
        if isinstance(tool_recovery, dict):
            recoveries.append(tool_recovery)
        present_recoveries = [
            item for item in recoveries if item.get("descriptor_present")
        ]
        recoverable = bool(present_recoveries) and all(
            item.get("recovery_status") == CONTINUATION_RECOVERY_STATUS_RECOVERABLE
            for item in present_recoveries
        )
        probe = {
            "run_id": run_context.run_id,
            "run_state": run_context.state.value,
            "recoverable": bool(recoverable),
            "persistence_interface": self._build_persistence_interface(),
            "recovery_operation_boundary": build_recovery_operation_contract(),
            "latest_recovery_operation": dict(run_context.metadata.get("latest_recovery_operation") or {}),
            "recovery_operations": [
                dict(item)
                for item in list(run_context.metadata.get("recovery_operations") or [])
                if isinstance(item, dict)
            ][-20:],
            "loop_continuation": dict(loop_recovery),
        }
        if isinstance(tool_recovery, dict):
            probe["tool_continuation"] = dict(tool_recovery)
        if approval is not None:
            probe["approval_request"] = approval.to_dict()
        probe["durable_recovery_loader"] = self._load_durable_recovery_candidate(
            run_id=run_context.run_id,
            approval_request_id=request_id,
        )
        probe["recovery_entrypoints"] = self._build_recovery_entrypoints_probe(
            run_context=run_context,
            tool_recovery=tool_recovery,
            loop_recovery=loop_recovery,
            approval=approval,
        )
        probe["checkpoint"] = self._build_runtime_checkpoint_probe(
            run_context=run_context,
            tool_recovery=tool_recovery,
            loop_recovery=loop_recovery,
            approval=approval,
            recovery_entrypoints=list(probe["recovery_entrypoints"]),
        )
        probe["resume_cursor"] = self._build_runtime_resume_cursor_probe(
            run_context=run_context,
            checkpoint=dict(probe["checkpoint"]),
            approval=approval,
            recovery_entrypoints=list(probe["recovery_entrypoints"]),
        )
        run_context.metadata["recovery_probe"] = dict(probe)
        return probe

    def _load_durable_recovery_candidate(
        self,
        *,
        run_id: str,
        approval_request_id: str | None = None,
    ) -> Dict[str, Any]:
        loader = DurableRecoveryLoader(
            workspace_store=self._workspace_store,
            continuation_registry=self._continuation_registry,
        )
        return loader.load(
            run_id=run_id,
            approval_request_id=approval_request_id,
        )

    def _build_recovery_entrypoints_probe(
        self,
        *,
        run_context: AgentRunContext,
        tool_recovery: Dict[str, Any] | None,
        loop_recovery: Dict[str, Any],
        approval: ApprovalRequestState | None = None,
    ) -> list[Dict[str, Any]]:
        run_state = run_context.state.value
        tool_recovery_dict = dict(tool_recovery or {})
        loop_recovery_dict = dict(loop_recovery or {})
        approval_status = str((approval.status if approval is not None else "") or "").strip().lower()
        entrypoints: list[Dict[str, Any]] = []
        for entry in EMBEDDED_SDK_RECOVERY_ENTRYPOINTS:
            normalized_entry = dict(entry)
            method = str(normalized_entry.get("method") or "").strip()
            mode = str(normalized_entry.get("mode") or "").strip()
            available = False
            blocked_reason = ""
            recovery_reason = ""
            if method == "probe_run_recovery":
                available = True
            elif method == "submit_approval" and mode == "approved":
                if approval_status in {"approved", "denied"}:
                    blocked_reason = "approval_already_resolved"
                    recovery_reason = CONTINUATION_RECOVERY_REASON_ALREADY_RESOLVED
                elif run_context.state != AgentState.WAITING_APPROVAL:
                    blocked_reason = "run_not_waiting_approval"
                elif not tool_recovery_dict.get("descriptor_present"):
                    blocked_reason = CONTINUATION_RECOVERY_REASON_DESCRIPTOR_MISSING
                elif tool_recovery_dict.get("recovery_status") == CONTINUATION_RECOVERY_STATUS_RECOVERABLE:
                    available = True
                    recovery_reason = str(tool_recovery_dict.get("recovery_reason") or "").strip()
                else:
                    blocked_reason = str(tool_recovery_dict.get("recovery_reason") or "") or CONTINUATION_RECOVERY_REASON_MISSING_EXECUTABLE_CONTINUATION
            elif method == "resume_run" and mode == "default":
                if run_context.state == AgentState.OBSERVING:
                    available = True
                else:
                    blocked_reason = "run_not_observing"
            elif method == "resume_run" and mode == "continue_loop":
                if run_context.state != AgentState.OBSERVING:
                    blocked_reason = "run_not_observing"
                elif not loop_recovery_dict.get("descriptor_present"):
                    blocked_reason = CONTINUATION_RECOVERY_REASON_DESCRIPTOR_MISSING
                elif loop_recovery_dict.get("recovery_status") == CONTINUATION_RECOVERY_STATUS_RECOVERABLE:
                    available = True
                    recovery_reason = str(loop_recovery_dict.get("recovery_reason") or "").strip()
                else:
                    blocked_reason = str(loop_recovery_dict.get("recovery_reason") or "") or CONTINUATION_RECOVERY_REASON_MISSING_EXECUTABLE_CONTINUATION
            normalized_entry["available"] = bool(available)
            normalized_entry["run_state"] = run_state
            normalized_entry["blocked_reason"] = blocked_reason
            normalized_entry["recovery_reason"] = recovery_reason
            if approval_status:
                normalized_entry["approval_status"] = approval_status
            entrypoints.append(normalized_entry)
        return entrypoints

    def _build_runtime_checkpoint_probe(
        self,
        *,
        run_context: AgentRunContext,
        tool_recovery: Dict[str, Any] | None,
        loop_recovery: Dict[str, Any],
        approval: ApprovalRequestState | None,
        recovery_entrypoints: list[Dict[str, Any]],
    ) -> Dict[str, Any]:
        tool_recovery_dict = dict(tool_recovery or {})
        loop_recovery_dict = dict(loop_recovery or {})
        approval_status = str((approval.status if approval is not None else "") or "").strip().lower()
        request_id = str(
            (approval.request_id if approval is not None else "")
            or tool_recovery_dict.get("request_id")
            or loop_recovery_dict.get("request_id")
            or ""
        ).strip()
        descriptor_ref = self._select_checkpoint_descriptor_ref(
            tool_recovery=tool_recovery_dict,
            loop_recovery=loop_recovery_dict,
        )
        workspace_backend = dict(
            tool_recovery_dict.get("workspace_backend")
            or loop_recovery_dict.get("workspace_backend")
            or self._describe_workspace_backend()
        )
        descriptor_present = bool(tool_recovery_dict.get("descriptor_present") or loop_recovery_dict.get("descriptor_present"))
        status = "missing"
        recovery_reason = CONTINUATION_RECOVERY_REASON_DESCRIPTOR_MISSING
        checkpoint_kind = "unavailable"
        if approval_status == "denied":
            status = "stale"
            recovery_reason = CONTINUATION_RECOVERY_REASON_DENIED
            checkpoint_kind = "approval_resolved"
        elif approval_status == "approved":
            status = "stale"
            recovery_reason = CONTINUATION_RECOVERY_REASON_ALREADY_RESOLVED
            checkpoint_kind = "approval_resolved"
        elif descriptor_present:
            checkpoint_kind = "approval_waiting" if approval is not None else "continuation_waiting"
            if bool(workspace_backend.get("fallback_active")):
                status = "blocked"
                recovery_reason = CONTINUATION_RECOVERY_REASON_WORKSPACE_BACKEND_FALLBACK_ACTIVE
            elif not bool(workspace_backend.get("durable")):
                status = "blocked"
                recovery_reason = CONTINUATION_RECOVERY_REASON_WORKSPACE_BACKEND_NOT_DURABLE
            else:
                relevant_reasons = {
                    str(tool_recovery_dict.get("recovery_reason") or "").strip(),
                    str(loop_recovery_dict.get("recovery_reason") or "").strip(),
                }
                if CONTINUATION_RECOVERY_REASON_MISSING_REGISTERED_BINDING in relevant_reasons:
                    status = "blocked"
                    recovery_reason = CONTINUATION_RECOVERY_REASON_MISSING_REGISTERED_BINDING
                elif any(item.get("available") for item in recovery_entrypoints if isinstance(item, dict)):
                    status = "ready"
                    recovery_reason = CONTINUATION_RECOVERY_REASON_READY_VIA_REGISTRY
                    if CONTINUATION_RECOVERY_REASON_READY_IN_PROCESS in relevant_reasons:
                        recovery_reason = CONTINUATION_RECOVERY_REASON_READY_IN_PROCESS
                else:
                    status = "blocked"
                    recovery_reason = (
                        str(tool_recovery_dict.get("recovery_reason") or "").strip()
                        or str(loop_recovery_dict.get("recovery_reason") or "").strip()
                        or CONTINUATION_RECOVERY_REASON_MISSING_EXECUTABLE_CONTINUATION
                    )
        events = list(self._events.get(run_context.run_id) or [])
        last_event = dict(events[-1]) if events else {}
        checkpoint = {
            "contract_version": "phase-ii-durable-runtime-checkpoint-v1",
            "checkpoint_id": f"checkpoint:{run_context.run_id}:{request_id or run_context.run_id}",
            "run_id": run_context.run_id,
            "checkpoint_kind": checkpoint_kind,
            "status": status,
            "recovery_reason": recovery_reason,
            "run_state": run_context.state.value,
            "event_cursor": {
                "last_event_id": str(last_event.get("event_id") or "").strip(),
                "last_sequence": len(events),
            },
            "approval_ref": {
                "approval_id": request_id,
                "status": approval_status,
            },
            "continuation_descriptor_ref": descriptor_ref,
            "workspace_backend": workspace_backend,
        }
        return checkpoint

    @staticmethod
    def _select_checkpoint_descriptor_ref(
        *,
        tool_recovery: Dict[str, Any],
        loop_recovery: Dict[str, Any],
    ) -> Dict[str, Any]:
        if tool_recovery.get("descriptor_present"):
            binding_ids = dict(tool_recovery.get("binding_ids") or {})
            return {
                "descriptor_kind": "tool_approval_continuation",
                "descriptor_status": str(tool_recovery.get("recovery_status") or "").strip(),
                "binding_id": str(binding_ids.get("tool_executor_binding_id") or "").strip(),
            }
        if loop_recovery.get("descriptor_present"):
            binding_ids = dict(loop_recovery.get("binding_ids") or {})
            return {
                "descriptor_kind": "loop_continuation",
                "descriptor_status": str(loop_recovery.get("recovery_status") or "").strip(),
                "binding_id": str(
                    binding_ids.get("reviewer_binding_id")
                    or binding_ids.get("reflector_binding_id")
                    or binding_ids.get("fallback_handler_binding_id")
                    or ""
                ).strip(),
            }
        return {
            "descriptor_kind": "",
            "descriptor_status": "",
            "binding_id": "",
        }

    def _build_runtime_resume_cursor_probe(
        self,
        *,
        run_context: AgentRunContext,
        checkpoint: Dict[str, Any],
        approval: ApprovalRequestState | None,
        recovery_entrypoints: list[Dict[str, Any]],
    ) -> Dict[str, Any]:
        approval_status = str((approval.status if approval is not None else "") or "").strip().lower()
        approval_entry = next(
            (
                dict(item)
                for item in recovery_entrypoints
                if str(item.get("method") or "").strip() == "submit_approval"
                and str(item.get("mode") or "").strip() == "approved"
            ),
            {},
        )
        cursor_status = "missing"
        recovery_reason = "resume_cursor_missing"
        blocked_reason = ""
        entrypoint = ""
        if approval_status == "denied":
            cursor_status = "stale"
            recovery_reason = CONTINUATION_RECOVERY_REASON_DENIED
            blocked_reason = CONTINUATION_RECOVERY_REASON_DENIED
            entrypoint = "submit_approval.approved"
        elif approval_status == "approved":
            cursor_status = "stale"
            recovery_reason = CONTINUATION_RECOVERY_REASON_ALREADY_RESOLVED
            blocked_reason = CONTINUATION_RECOVERY_REASON_ALREADY_RESOLVED
            entrypoint = "submit_approval.approved"
        elif checkpoint.get("status") == "missing":
            recovery_reason = "checkpoint_missing"
            blocked_reason = "checkpoint_missing"
        elif approval_entry:
            entrypoint = "submit_approval.approved"
            if bool(approval_entry.get("available")):
                cursor_status = "ready"
                recovery_reason = str(approval_entry.get("recovery_reason") or "").strip()
            else:
                cursor_status = "blocked"
                recovery_reason = (
                    str(approval_entry.get("recovery_reason") or "").strip()
                    or str(approval_entry.get("blocked_reason") or "").strip()
                    or str(checkpoint.get("recovery_reason") or "").strip()
                    or "resume_cursor_missing"
                )
                blocked_reason = str(approval_entry.get("blocked_reason") or "").strip() or recovery_reason
        return {
            "contract_version": "phase-ii-runtime-resume-cursor-v1",
            "cursor_id": f"cursor:{run_context.run_id}:{entrypoint or 'none'}",
            "run_id": run_context.run_id,
            "checkpoint_id": str(checkpoint.get("checkpoint_id") or "").strip(),
            "entrypoint": entrypoint,
            "cursor_status": cursor_status,
            "recovery_reason": recovery_reason,
            "blocked_reason": blocked_reason,
            "requires_registry_binding": recovery_reason == CONTINUATION_RECOVERY_REASON_READY_VIA_REGISTRY,
            "requires_durable_workspace": recovery_reason == CONTINUATION_RECOVERY_REASON_READY_VIA_REGISTRY,
        }

    def _build_recovery_record(
        self,
        *,
        continuation_kind: str,
        continuation_id: str,
        descriptor: Dict[str, Any] | None,
        executable_available: bool,
    ) -> Dict[str, Any]:
        descriptor_dict = dict(descriptor or {})
        descriptor_present = bool(descriptor_dict)
        attempted_at = _utc_now()
        status = CONTINUATION_RECOVERY_STATUS_UNRECOVERABLE
        reason = CONTINUATION_RECOVERY_REASON_DESCRIPTOR_MISSING
        binding_ids = self._extract_binding_ids(continuation_kind=continuation_kind, descriptor=descriptor_dict)
        missing_binding_ids: list[str] = []
        in_process_available = bool(executable_available)
        registry_recoverable = False
        workspace_backend = self._describe_workspace_backend()
        workspace_backend_durable = bool(workspace_backend.get("durable"))
        workspace_backend_fallback_active = bool(workspace_backend.get("fallback_active"))
        if descriptor_present:
            if not executable_available:
                if workspace_backend_fallback_active:
                    registry_recoverable = False
                elif not workspace_backend_durable:
                    registry_recoverable = False
                else:
                    registry_recoverable, missing_binding_ids = self._can_reattach_via_registry(
                        continuation_kind=continuation_kind,
                        descriptor=descriptor_dict,
                    )
                    executable_available = registry_recoverable
            status = CONTINUATION_RECOVERY_STATUS_RECOVERABLE if executable_available else CONTINUATION_RECOVERY_STATUS_UNRECOVERABLE
            if executable_available:
                reason = (
                    CONTINUATION_RECOVERY_REASON_READY_IN_PROCESS
                    if in_process_available or not registry_recoverable
                    else CONTINUATION_RECOVERY_REASON_READY_VIA_REGISTRY
                )
            else:
                reason = (
                    CONTINUATION_RECOVERY_REASON_WORKSPACE_BACKEND_FALLBACK_ACTIVE
                    if workspace_backend_fallback_active
                    else (
                        CONTINUATION_RECOVERY_REASON_WORKSPACE_BACKEND_NOT_DURABLE
                        if not workspace_backend_durable and not in_process_available
                        else (
                            CONTINUATION_RECOVERY_REASON_MISSING_REGISTERED_BINDING
                            if binding_ids and missing_binding_ids
                            else CONTINUATION_RECOVERY_REASON_MISSING_EXECUTABLE_CONTINUATION
                        )
                    )
                )
        request_id = str(descriptor_dict.get("request_id") or continuation_id or "").strip() or None
        recovery = build_continuation_recovery(
            continuation_kind=continuation_kind,
            status=status,
            reason=reason,
            descriptor_present=descriptor_present,
            executable_available=executable_available,
            attempted_at=attempted_at,
            request_id=request_id,
            resume_mode=str(descriptor_dict.get("resume_mode") or "").strip() or None,
            binding_ids=binding_ids,
            missing_binding_ids=missing_binding_ids,
        )
        recovery["workspace_backend"] = workspace_backend
        recovery["persistence_interface"] = build_embedded_sdk_persistence_interface(workspace_backend)
        return recovery

    def _fail_closed_recovery(
        self,
        *,
        run_context: AgentRunContext,
        continuation_kind: str,
        continuation_id: str,
        summary: str,
        recovery_reason_override: str = "",
        blocked_reason_override: str = "",
        worker_ownership: Dict[str, Any] | None = None,
        descriptor: Dict[str, Any] | None = None,
        retry_attempt: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        probe = self._evaluate_run_recovery(run_context)
        recovery_key = "tool_continuation" if continuation_kind == "tool_approval" else "loop_continuation"
        recovery = dict(probe.get(recovery_key) or {})
        if not recovery:
            recovery = self._build_recovery_record(
                continuation_kind=continuation_kind,
                continuation_id=continuation_id,
                descriptor={},
                executable_available=False,
            )
        if descriptor:
            recovery["descriptor"] = dict(descriptor)
            recovery["descriptor_present"] = True
        if recovery_reason_override:
            recovery["recovery_reason"] = str(recovery_reason_override or "").strip()
        if blocked_reason_override:
            recovery["blocked_reason"] = str(blocked_reason_override or "").strip()
        if worker_ownership:
            recovery["worker_ownership"] = dict(worker_ownership)
        retry_evidence = self._build_recovery_retry_evidence(
            retry_attempt=retry_attempt,
            recovery_reason=str(recovery.get("recovery_reason") or "").strip(),
        )
        recovery_operation = self._record_recovery_operation(
            run_context=run_context,
            entrypoint=recovery_entrypoint_for_continuation_kind(continuation_kind),
            operation_status="blocked",
            recovery_reason=str(recovery.get("recovery_reason") or "").strip(),
            blocked_reason=str(recovery.get("blocked_reason") or recovery.get("recovery_reason") or "").strip(),
            continuation_kind=continuation_kind,
            continuation_id=continuation_id,
            descriptor=dict(recovery.get("descriptor") or {}),
            recovery=recovery,
            worker_ownership=worker_ownership,
            retry=retry_evidence,
        )
        event_factory = self._event_factory(run_context)
        self._append_event(
            run_context.run_id,
            event_factory.build(
                AgentEventType.STATUS,
                {
                    "status_kind": "recovery_failed_closed",
                    "summary": summary,
                    "recovery": dict(recovery),
                    "recovery_operation": dict(recovery_operation),
                },
                iteration=run_context.iteration,
            ).to_dict(),
        )
        self._persist_run_context(run_context)
        return recovery

    def _record_recovery_operation(
        self,
        *,
        run_context: AgentRunContext,
        entrypoint: str,
        operation_status: str,
        recovery_reason: str,
        continuation_kind: str,
        continuation_id: str,
        blocked_reason: str = "",
        descriptor: Dict[str, Any] | None = None,
        recovery: Dict[str, Any] | None = None,
        worker_ownership: Dict[str, Any] | None = None,
        retry: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        operation = self._build_recovery_operation_record(
            run_context=run_context,
            entrypoint=entrypoint,
            operation_status=operation_status,
            recovery_reason=recovery_reason,
            blocked_reason=blocked_reason,
            continuation_kind=continuation_kind,
            continuation_id=continuation_id,
            descriptor=descriptor,
            recovery=recovery,
            worker_ownership=worker_ownership,
            retry=retry,
        )
        history = list(run_context.metadata.get("recovery_operations") or [])
        history.append(dict(operation))
        run_context.metadata["latest_recovery_operation"] = dict(operation)
        run_context.metadata["recovery_operations"] = history[-20:]
        self._persist_run_context(run_context)
        return operation

    def _build_recovery_operation_record(
        self,
        *,
        run_context: AgentRunContext,
        entrypoint: str,
        operation_status: str,
        recovery_reason: str,
        continuation_kind: str,
        continuation_id: str,
        blocked_reason: str = "",
        descriptor: Dict[str, Any] | None = None,
        recovery: Dict[str, Any] | None = None,
        worker_ownership: Dict[str, Any] | None = None,
        retry: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        descriptor_dict = dict(descriptor or {})
        recovery_dict = dict(recovery or {})
        binding_ids = dict(recovery_dict.get("binding_ids") or {})
        if not binding_ids and descriptor_dict:
            binding_ids = self._extract_binding_ids(
                continuation_kind=continuation_kind,
                descriptor=descriptor_dict,
            )
        workspace_backend = dict(recovery_dict.get("workspace_backend") or self._describe_workspace_backend())
        persistence_interface = dict(
            recovery_dict.get("persistence_interface")
            or build_embedded_sdk_persistence_interface(workspace_backend)
        )
        return build_recovery_operation_record(
            run_id=run_context.run_id,
            entrypoint=entrypoint,
            operation_status=operation_status,
            recovery_reason=recovery_reason,
            blocked_reason=blocked_reason,
            continuation_kind=continuation_kind,
            continuation_id=continuation_id,
            binding_ids=binding_ids,
            descriptor_present=bool(
                recovery_dict.get("descriptor_present")
                if "descriptor_present" in recovery_dict
                else descriptor_dict
            ),
            missing_binding_ids=list(recovery_dict.get("missing_binding_ids") or []),
            workspace_backend=workspace_backend,
            persistence_interface=persistence_interface,
            worker_ownership=worker_ownership or dict(recovery_dict.get("worker_ownership") or {}),
            retry=retry,
            recorded_at=_utc_now(),
        )

    def _build_recovery_retry_evidence(
        self,
        *,
        retry_attempt: Dict[str, Any] | None,
        recovery_reason: str,
    ) -> Dict[str, Any] | None:
        if not retry_attempt:
            return None

        retry_dict = dict(retry_attempt or {})
        previous_operation_id = str(retry_dict.get("previous_operation_id") or "").strip()
        idempotency_key = str(retry_dict.get("idempotency_key") or "").strip()
        if not previous_operation_id or not idempotency_key:
            return None
        evidence_recovery_reason = str(retry_dict.get("recovery_reason") or recovery_reason or "").strip()

        return build_recovery_retry_evidence(
            attempt_number=int(retry_dict.get("attempt_number") or 1),
            previous_operation_id=previous_operation_id,
            idempotency_key=idempotency_key,
            recovery_reason=evidence_recovery_reason,
            max_attempts=int(retry_dict.get("max_attempts") or 0) or 3,
        )

    def _validate_recovery_worker_ownership(
        self,
        *,
        run_context: AgentRunContext,
        descriptor: Dict[str, Any] | None = None,
        recovery: Dict[str, Any] | None = None,
        entrypoint: str = "",
    ) -> Dict[str, Any] | None:
        if self._worker_ownership_store is None:
            return None
        descriptor_dict = dict(descriptor or {})
        recovery_dict = dict(recovery or {})
        ownership = dict(
            recovery_dict.get("worker_ownership")
            or descriptor_dict.get("worker_ownership")
            or {}
        )
        if not ownership:
            if not self._worker_ownership_auto_claim_enabled:
                return None
            claim_run = getattr(self._worker_ownership_store, "claim_run", None)
            if not callable(claim_run):
                return {
                    "implemented": True,
                    "owned": False,
                    "lease_status": "blocked",
                    "reason": "worker_ownership_lost",
                    "blocked_reason": "worker_ownership_store_unavailable",
                }
            if self._worker_ownership_auto_claim_gate_enforced:
                gate = self._build_worker_ownership_auto_claim_enablement_gate(
                    requested_entrypoint=entrypoint,
                )
                if not bool(gate.get("will_auto_claim")):
                    return {
                        "implemented": True,
                        "owned": False,
                        "lease_status": "blocked",
                        "reason": "worker_ownership_lost",
                        "blocked_reason": "auto_claim_enablement_gate_blocked",
                        "auto_claim_enablement_gate": gate,
                    }
            return dict(claim_run(run_context.run_id, self._worker_ownership_worker_id))
        validate_ownership = getattr(self._worker_ownership_store, "validate_ownership", None)
        if not callable(validate_ownership):
            return {
                **ownership,
                "implemented": True,
                "owned": False,
                "lease_status": "blocked",
                "reason": "worker_ownership_lost",
                "blocked_reason": "worker_ownership_store_unavailable",
            }
        return dict(validate_ownership(
            str(ownership.get("run_id") or run_context.run_id),
            str(ownership.get("worker_id") or ""),
            str(ownership.get("lease_id") or ""),
            int(ownership.get("fencing_token") or 0),
        ))

    def _build_worker_ownership_auto_claim_enablement_gate(
        self,
        *,
        requested_entrypoint: str,
    ) -> Dict[str, Any]:
        ownership_contract: Dict[str, Any] = {}
        build_contract = getattr(self._worker_ownership_store, "build_contract", None)
        if callable(build_contract):
            ownership_contract = dict(build_contract() or {})
        durable_ownership_ready = bool(ownership_contract.get("durable"))
        allowed_entrypoints = self._worker_ownership_auto_claim_allowed_entrypoints or None
        return build_worker_ownership_explicit_auto_claim_enablement_gate_contract(
            explicit_runtime_configuration=self._worker_ownership_auto_claim_enabled,
            production_gate_ready=self._worker_ownership_auto_claim_production_gate_ready,
            durable_ownership_ready=durable_ownership_ready,
            descriptor_evidence_fallback=True,
            idempotency_evidence_ready=(
                self._worker_ownership_auto_claim_idempotency_evidence_ready
            ),
            audit_evidence_ready=self._worker_ownership_auto_claim_audit_evidence_ready,
            lease_validation_ready=callable(
                getattr(self._worker_ownership_store, "validate_ownership", None)
            ),
            rollout_auto_claim_decision_recorded=(
                self._worker_ownership_auto_claim_rollout_decision_recorded
            ),
            requested_entrypoint=requested_entrypoint,
            allowed_entrypoints=allowed_entrypoints,
        )

    def _identify_continuation_binding(self, handler: Any) -> str | None:
        if self._continuation_registry is None or handler is None:
            return None
        identify = getattr(self._continuation_registry, "identify", None)
        if not callable(identify):
            return None
        binding_id = identify(handler)
        normalized_binding_id = str(binding_id or "").strip()
        return normalized_binding_id or None

    def _ensure_continuation_binding(
        self,
        handler: Any,
        *,
        binding_kind: str,
        metadata: Dict[str, Any] | None = None,
    ) -> str | None:
        normalized_binding_kind = str(binding_kind or "").strip() or "generic"
        binding_id = self._identify_continuation_binding(handler)
        if binding_id:
            return binding_id
        if self._continuation_registry is None or handler is None:
            return None
        register = getattr(self._continuation_registry, "register", None)
        if not callable(register):
            return None
        handler_name = str(getattr(handler, "__name__", None) or handler.__class__.__name__).strip() or "handler"
        module_name = str(getattr(handler, "__module__", None) or "").strip().replace(".", "_")
        normalized_handler_name = handler_name.replace(".", "_")
        generated_binding_id = (
            f"{normalized_binding_kind}.{module_name}.{normalized_handler_name}"
            if module_name
            else f"{normalized_binding_kind}.{normalized_handler_name}"
        )
        register(
            generated_binding_id,
            handler,
            binding_kind=normalized_binding_kind,
            metadata=dict(metadata or {}),
        )
        return self._identify_continuation_binding(handler)

    def _resolve_continuation_binding(self, binding_id: str) -> Any | None:
        normalized_binding_id = str(binding_id or "").strip()
        if self._continuation_registry is None or not normalized_binding_id:
            return None
        resolve = getattr(self._continuation_registry, "resolve", None)
        if not callable(resolve):
            return None
        return resolve(normalized_binding_id)

    def _extract_binding_ids(
        self,
        *,
        continuation_kind: str,
        descriptor: Dict[str, Any],
    ) -> Dict[str, str]:
        binding_fields = (
            ["tool_executor_binding_id"]
            if continuation_kind == "tool_approval"
            else ["reflector_binding_id", "reviewer_binding_id", "fallback_handler_binding_id"]
        )
        return {
            field_name: str(descriptor.get(field_name) or "").strip()
            for field_name in binding_fields
            if str(descriptor.get(field_name) or "").strip()
        }

    def _can_reattach_via_registry(
        self,
        *,
        continuation_kind: str,
        descriptor: Dict[str, Any],
    ) -> tuple[bool, list[str]]:
        binding_ids = self._extract_binding_ids(continuation_kind=continuation_kind, descriptor=descriptor)
        if not binding_ids:
            return False, []
        missing_binding_ids = [
            binding_id
            for binding_id in binding_ids.values()
            if not callable(self._resolve_continuation_binding(binding_id))
        ]
        return len(missing_binding_ids) == 0, missing_binding_ids

    def _describe_workspace_backend(self) -> Dict[str, Any]:
        describe_backend = getattr(self._workspace_store, "describe_backend", None)
        if not callable(describe_backend):
            return {
                "backend_kind": "",
                "durable": False,
                "fallback_active": False,
                "fallback_reason": "",
                "last_error": "",
            }
        description = dict(describe_backend() or {})
        return {
            "backend_kind": str(description.get("backend_kind") or "").strip(),
            "backend_mode": str(description.get("backend_mode") or "").strip(),
            "durable": bool(description.get("durable")),
            "fallback_active": bool(description.get("fallback_active")),
            "fallback_reason": str(description.get("fallback_reason") or "").strip(),
            "last_error": str(description.get("last_error") or "").strip(),
            "state_contract": dict(description.get("state_contract") or {}),
        }

    def _build_persistence_interface(self) -> Dict[str, Any]:
        return build_embedded_sdk_persistence_interface(self._describe_workspace_backend())

    def _workspace_backend_allows_cross_process_recovery(self) -> bool:
        description = self._describe_workspace_backend()
        return bool(description.get("durable")) and not bool(description.get("fallback_active"))

    def _reattach_tool_continuation(
        self,
        *,
        request_id: str,
        run_context: AgentRunContext,
        descriptor: Dict[str, Any],
    ) -> Dict[str, Any] | None:
        tool_executor_binding_id = str(descriptor.get("tool_executor_binding_id") or "").strip()
        tool_executor = self._resolve_continuation_binding(tool_executor_binding_id)
        if not callable(tool_executor):
            return None
        continuation = {
            "kind": "tool_executor",
            "tool_executor": tool_executor,
            "tool_decision": dict(run_context.metadata.get("execution_tool_decision") or {}),
            "tool_executor_binding_id": tool_executor_binding_id,
        }
        self._tool_continuations[request_id] = continuation
        return continuation

    def _reattach_loop_continuation(
        self,
        *,
        run_id: str,
        descriptor: Dict[str, Any],
    ) -> Dict[str, Any] | None:
        has_reflector = bool(descriptor.get("has_reflector"))
        has_reviewer = bool(descriptor.get("has_reviewer"))
        has_fallback_handler = bool(descriptor.get("has_fallback_handler"))
        reflector_binding_id = str(descriptor.get("reflector_binding_id") or "").strip()
        reviewer_binding_id = str(descriptor.get("reviewer_binding_id") or "").strip()
        fallback_handler_binding_id = str(descriptor.get("fallback_handler_binding_id") or "").strip()
        if not any([reflector_binding_id, reviewer_binding_id, fallback_handler_binding_id]):
            return None

        reflector = self._resolve_continuation_binding(reflector_binding_id) if reflector_binding_id else None
        reviewer = self._resolve_continuation_binding(reviewer_binding_id) if reviewer_binding_id else None
        fallback_handler = (
            self._resolve_continuation_binding(fallback_handler_binding_id) if fallback_handler_binding_id else None
        )

        if has_reflector and not callable(reflector):
            return None
        if has_reviewer and not callable(reviewer):
            return None
        if has_fallback_handler and not callable(fallback_handler):
            return None

        continuation = {
            "reflector": reflector,
            "reviewer": reviewer,
            "fallback_handler": fallback_handler,
            "max_iterations": int(descriptor.get("max_iterations") or 1),
        }
        self._loop_continuations[run_id] = dict(continuation)
        return continuation

    def _event_factory(self, run_context: AgentRunContext) -> AgentEventFactory:
        return AgentEventFactory(
            run_context.run_id,
            conversation_id=run_context.conversation_id,
            parent_run_id=run_context.parent_run_id,
        )

    def _prepare_child_delegate_payload(
        self,
        *,
        parent_context: AgentRunContext | None,
        payload: Dict[str, Any] | None,
    ) -> Dict[str, Any]:
        child_payload = dict(payload or {})
        if parent_context is not None:
            child_payload["parent_run_id"] = parent_context.run_id
            child_payload.setdefault("conversation_id", parent_context.conversation_id)
            child_payload.setdefault("user_id", parent_context.user_id)
            child_payload.setdefault("model_name", parent_context.model_name)
        child_payload.setdefault("run_kind", AgentRunKind.CHILD.value)

        metadata = dict(child_payload.get("metadata") or {})
        if parent_context is not None:
            metadata.setdefault("parent_run_id", parent_context.run_id)
            metadata.setdefault("parent_agent_name", parent_context.metadata.get("agent_name"))
        child_payload["metadata"] = metadata
        return child_payload

    def _append_event(self, run_id: str, event: Dict[str, Any]) -> None:
        event_copy = dict(event)
        self._events.setdefault(run_id, []).append(event_copy)
        self._persist_run_events(run_id)
        self._record_query_control_event(run_id, event_copy)
        self._record_approval_lifecycle_trace_event(run_id, event_copy)

    def _record_query_control_event(self, run_id: str, event: Dict[str, Any]) -> None:
        if self._query_control_db is None or self._query_control_timeline_service is None:
            return
        run_context = self._runs.get(run_id)
        if run_context is None:
            return
        mapping = self._query_control_event_mapper.map_embedded_sdk_event(event)
        if mapping is None:
            mapping = self._query_control_event_mapper.map_subagent_event(event)
        if mapping is None:
            return
        payload = self._query_control_event_mapper.build_record_payload(event)
        try:
            self._query_control_timeline_service.record_stage(
                db=self._query_control_db,
                conversation_id=run_context.conversation_id,
                channel=mapping["channel"],
                stage=mapping["stage"],
                query_id=run_context.run_id,
                summary=str(event.get("summary") or f"Embedded SDK {mapping['stage']}"),
                detail=str(event.get("detail") or ""),
                severity=str(event.get("severity") or "info"),
                payload=payload,
            )
        except Exception as exc:  # pragma: no cover - exact recorder failure belongs to integration.
            failures = list(run_context.metadata.get("query_control_recording_failures") or [])
            failures.append({
                "stage": mapping["stage"],
                "status_kind": event.get("status_kind"),
                "error": str(exc),
            })
            run_context.metadata["query_control_recording_failures"] = failures
            self._persist_run_context(run_context)

    def _record_approval_lifecycle_trace_event(self, run_id: str, event: Dict[str, Any]) -> None:
        recorder = self._approval_lifecycle_trace_recorder
        if recorder is None:
            return
        status_kind = str(event.get("status_kind") or "").strip()
        if status_kind not in SDK_APPROVAL_LIFECYCLE_TRACE_STATUS_KINDS:
            return
        run_context = self._runs.get(run_id)
        if run_context is None:
            return
        record_event = getattr(recorder, "record_event", None)
        if not callable(record_event):
            return
        try:
            result = record_event(run_context=run_context, event=dict(event))
        except Exception as exc:  # pragma: no cover - exact recorder failure belongs to integration.
            failures = list(run_context.metadata.get("approval_lifecycle_trace_failures") or [])
            failures.append({
                "status_kind": event.get("status_kind"),
                "error": str(exc),
            })
            run_context.metadata["approval_lifecycle_trace_failures"] = failures
            self._persist_run_context(run_context)
            return
        if isinstance(result, dict) and result:
            records = list(run_context.metadata.get("approval_lifecycle_trace_records") or [])
            records.append({
                "status_kind": result.get("status_kind") or event.get("status_kind"),
                "trace_written": bool(result.get("trace_written")),
                "dedupe_key": str(result.get("dedupe_key") or "").strip(),
                "dedupe_source": str(result.get("dedupe_source") or "").strip(),
            })
            run_context.metadata["approval_lifecycle_trace_records"] = records[-20:]
            self._persist_run_context(run_context)

    def _persist_run_context(self, run_context: AgentRunContext) -> None:
        if self._workspace_store is None:
            return
        self._workspace_store.save_run_snapshot(run_context.snapshot())

    def _persist_run_events(self, run_id: str) -> None:
        if self._workspace_store is None:
            return
        self._workspace_store.save_events(run_id, list(self._events.get(run_id, [])))

    def _persist_approval(self, approval: ApprovalRequestState) -> None:
        if self._workspace_store is None:
            return
        self._workspace_store.save_approval_snapshot(approval.to_dict())

    def _persist_tool_continuation_descriptor(self, request_id: str, descriptor: Dict[str, Any]) -> None:
        if self._workspace_store is None:
            return
        self._workspace_store.save_tool_continuation_descriptor(request_id, descriptor)

    def _persist_loop_continuation_descriptor(self, run_id: str, descriptor: Dict[str, Any]) -> None:
        if self._workspace_store is None:
            return
        self._workspace_store.save_loop_continuation_descriptor(run_id, descriptor)

    def _delete_tool_continuation_descriptor(self, request_id: str) -> None:
        if self._workspace_store is None:
            return
        self._workspace_store.delete_tool_continuation_descriptor(request_id)

    def _delete_loop_continuation_descriptor(self, run_id: str) -> None:
        if self._workspace_store is None:
            return
        self._workspace_store.delete_loop_continuation_descriptor(run_id)

    def _get_tool_continuation_descriptor(self, request_id: str) -> Dict[str, Any] | None:
        if self._workspace_store is None:
            return None
        return self._workspace_store.get_tool_continuation_descriptor(request_id)

    def _get_loop_continuation_descriptor(self, run_id: str) -> Dict[str, Any] | None:
        if self._workspace_store is None:
            return None
        return self._workspace_store.get_loop_continuation_descriptor(run_id)

    def _load_run_context_from_store(self, run_id: str) -> AgentRunContext | None:
        if self._workspace_store is None:
            return None
        snapshot = self._workspace_store.get_run_snapshot(run_id)
        if snapshot is None:
            return None
        run_context = AgentRunContext.from_snapshot(snapshot)
        self._runs[run_id] = run_context
        self._events.setdefault(run_id, self._workspace_store.get_events(run_id))
        return run_context

    def _load_approval_from_store(self, request_id: str) -> ApprovalRequestState | None:
        if self._workspace_store is None:
            return None
        snapshot = self._workspace_store.get_approval_snapshot(request_id)
        if snapshot is None:
            return None
        approval = ApprovalRequestState.from_dict(snapshot)
        self._approvals[request_id] = approval
        return approval

    def _capture_tool_policy_decision(
        self,
        tool_policy: ToolPolicyCallable,
        decision_holder: Dict[str, Any],
    ) -> ToolPolicyCallable:
        def _wrapped(run_context: AgentRunContext) -> Any:
            raw_decision = tool_policy(run_context)
            decision = _coerce_tool_decision_dict(raw_decision)
            if decision:
                decision_holder.clear()
                decision_holder.update(decision)
            return raw_decision

        return _wrapped

    def _bridge_tool_runtime_policy(self, tool_policy: ToolPolicyCallable) -> ToolPolicyCallable:
        def _wrapped(run_context: AgentRunContext) -> Any:
            raw_decision = tool_policy(run_context)
            decision = _coerce_tool_decision_dict(raw_decision)
            if not decision:
                return raw_decision
            if str(decision.get("status") or "allowed").strip().lower() != "allowed":
                return raw_decision
            tool_name = str(decision.get("tool_name") or "").strip()
            if not tool_name:
                return raw_decision
            runtime_decision = self._probe_tool_runtime_policy(tool_name)
            runtime_status = str(runtime_decision.get("status") or "").strip().lower()
            if runtime_status not in {"approval_required", "denied"}:
                return raw_decision
            metadata = dict(decision.get("metadata") or {})
            metadata.update({
                "policy": runtime_decision.get("policy"),
                "permission_level": runtime_decision.get("permission_level"),
                "reason_code": runtime_decision.get("reason_code"),
                "tool_runtime_policy_decision": dict(runtime_decision),
            })
            return {
                "status": runtime_status,
                "tool_name": tool_name,
                "tool_args": dict(decision.get("tool_args") or {}),
                "reason": str(runtime_decision.get("reason") or decision.get("reason") or ""),
                "metadata": metadata,
            }

        return _wrapped

    def _probe_tool_runtime_policy(self, tool_name: str) -> Dict[str, Any]:
        evaluate_tool_policy = getattr(self._get_tool_runtime_service(), "evaluate_tool_policy", None)
        if callable(evaluate_tool_policy):
            return dict(evaluate_tool_policy(tool_name) or {})
        return {}

    def _build_tool_runtime_executor(self, decision_holder: Dict[str, Any]) -> ToolExecutorCallable:
        def _execute(run_context: AgentRunContext) -> Dict[str, Any] | None:
            decision = dict(decision_holder or {})
            tool_name = str(decision.get("tool_name") or "").strip()
            tool_args = dict(decision.get("tool_args") or {})
            if not tool_name:
                return None
            execute_tool = getattr(self._get_tool_runtime_service(), "execute_tool", None)
            if not callable(execute_tool):
                return None
            result = dict(
                execute_tool(
                    tool_name,
                    tool_args,
                    execution_options=_build_tool_runtime_execution_options(run_context),
                )
                or {}
            )
            if not result:
                return None
            return {
                "tool_name": str(result.get("tool_name") or tool_name),
                "args": dict(result.get("args") or tool_args),
                "result": str(result.get("result_text") or ""),
                "tool_call_id": str(result.get("tool_call_id") or ""),
                "execution": dict(result.get("execution") or {}),
            }

        return _execute


def _normalize_optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    normalized = int(value)
    return normalized if normalized >= 0 else None


def _normalize_optional_str(value: Any) -> str | None:
    normalized = str(value or "").strip()
    return normalized or None


def _normalize_required_str(value: Any, field_name: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{field_name} is required.")
    return normalized


def _normalize_run_kind(value: Any) -> AgentRunKind:
    normalized = str(value or AgentRunKind.CHAT.value).strip() or AgentRunKind.CHAT.value
    try:
        return AgentRunKind(normalized)
    except ValueError:
        return AgentRunKind.CHAT


def _normalize_approval_decision(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    alias_map = {
        "approve": "approved",
        "approved": "approved",
        "allow": "approved",
        "deny": "denied",
        "denied": "denied",
        "reject": "denied",
        "rejected": "denied",
    }
    if normalized not in alias_map:
        raise ValueError("approval decision must be approved or denied.")
    return alias_map[normalized]


def _normalize_embedded_tool_spec(
    tool_definition: ToolSpec | Dict[str, Any],
    **tool_fields: Any,
) -> ToolSpec:
    if isinstance(tool_definition, ToolSpec):
        if not tool_fields:
            return tool_definition
        data = tool_definition.to_dict()
    else:
        data = dict(tool_definition or {})
    data.update({key: value for key, value in tool_fields.items() if value is not None})
    name = str(data.get("name") or "").strip()
    description = str(data.get("description") or "").strip()
    if not name:
        raise ValueError("tool name is required.")
    if not description:
        raise ValueError("tool description is required.")
    render_mode = data.get("render_mode") or ToolRenderMode.PLAIN_TEXT
    if not isinstance(render_mode, ToolRenderMode):
        render_mode = ToolRenderMode(str(render_mode or ToolRenderMode.PLAIN_TEXT.value))
    return ToolSpec(
        name=name,
        description=description,
        permission_level=str(data.get("permission_level") or "auto"),
        deterministic=bool(data.get("deterministic", False)),
        safe_to_rephrase=bool(data.get("safe_to_rephrase", True)),
        render_mode=render_mode,
        supports_cache=bool(data.get("supports_cache", False)),
        cache_ttl_seconds=data.get("cache_ttl_seconds"),
        timeout_seconds=data.get("timeout_seconds"),
        passthrough_strategy=str(data.get("passthrough_strategy") or "never"),
        card_schema=data.get("card_schema"),
        supported_card_schemas=tuple(data.get("supported_card_schemas") or ()),
        tags=tuple(data.get("tags") or ()),
    )


def _coerce_tool_decision_dict(raw_decision: Any) -> Dict[str, Any]:
    if isinstance(raw_decision, dict):
        decision = dict(raw_decision)
    else:
        to_dict = getattr(raw_decision, "to_dict", None)
        decision = dict(to_dict() or {}) if callable(to_dict) else {}
    if not decision:
        return {}
    return {
        "status": str(decision.get("status") or "allowed"),
        "tool_name": str(decision.get("tool_name") or "").strip(),
        "tool_args": dict(decision.get("tool_args") or {}),
        "reason": str(decision.get("reason") or "").strip(),
        "metadata": dict(decision.get("metadata") or {}),
    }


def _build_tool_runtime_execution_options(run_context: AgentRunContext | None = None) -> Dict[str, Any]:
    metadata = dict(getattr(run_context, "metadata", {}) or {})
    approved = dict(metadata.get("approved_tool_execution") or {})
    if str(approved.get("decision") or "").strip().lower() != "approved":
        return {}
    return {
        "policy_override": {
            "status": "approved",
            "approval_request_id": str(approved.get("approval_request_id") or "").strip(),
            "source": str(approved.get("source") or "embedded_sdk_tool_continuation").strip(),
        }
    }


def _normalize_tool_result(raw_result: Any) -> Dict[str, Any] | None:
    if raw_result is None:
        return None
    if isinstance(raw_result, ExecutionToolResult):
        return raw_result.to_dict()
    if isinstance(raw_result, dict):
        return ExecutionToolResult(
            tool_name=str(raw_result.get("tool_name") or "unknown_tool"),
            args=dict(raw_result.get("args") or {}),
            result=str(raw_result.get("result") or ""),
            tool_call_id=str(raw_result.get("tool_call_id") or ""),
            execution=dict(raw_result.get("execution") or {}),
        ).to_dict()
    return None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _format_datetime(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value or _utc_now())
