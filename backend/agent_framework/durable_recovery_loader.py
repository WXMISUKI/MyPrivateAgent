"""Durable recovery loader for registry-backed SDK recovery candidates."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from .continuation_lifecycle import (
    build_continuation_descriptor_lifecycle_contract,
    build_continuation_descriptor_lifecycle_evidence,
    classify_descriptor_state,
)
from .continuations import (
    CONTINUATION_RECOVERY_REASON_ALREADY_RESOLVED,
    CONTINUATION_RECOVERY_REASON_DENIED,
    CONTINUATION_RECOVERY_REASON_DESCRIPTOR_CORRUPTED,
    CONTINUATION_RECOVERY_REASON_DESCRIPTOR_MISSING,
    CONTINUATION_RECOVERY_REASON_MISSING_REGISTERED_BINDING,
    CONTINUATION_RECOVERY_REASON_READY_VIA_REGISTRY,
    CONTINUATION_RECOVERY_REASON_WORKSPACE_BACKEND_FALLBACK_ACTIVE,
    CONTINUATION_RECOVERY_REASON_WORKSPACE_BACKEND_NOT_DURABLE,
)
from .loader_handoff import (
    build_durable_loader_execution_handoff_decision,
    build_durable_loader_execution_handoff_policy_contract,
)
from .persistence import EmbeddedRunWorkspaceStore, build_embedded_sdk_persistence_interface


DURABLE_RECOVERY_LOADER_CONTRACT_VERSION = "phase-ii-durable-recovery-loader-v1"
DURABLE_RECOVERY_LOADER_READY = "ready"
DURABLE_RECOVERY_LOADER_BLOCKED = "blocked"

UNSAFE_DESCRIPTOR_KEYS = {
    "callable",
    "handler",
    "function",
    "provider_client",
    "active_stream_iterator",
    "executable_continuation_callable",
    "python_function_binding",
    "temporary_stream_cursor",
    "in_process_event_iterator",
    "tool_executor",
    "reflector",
    "reviewer",
    "fallback_handler",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _describe_workspace_backend(workspace_store: EmbeddedRunWorkspaceStore | None) -> Dict[str, Any]:
    describe_backend = getattr(workspace_store, "describe_backend", None)
    if not callable(describe_backend):
        return {
            "backend_kind": "",
            "backend_mode": "",
            "durable": False,
            "fallback_active": False,
            "fallback_reason": "",
            "last_error": "",
            "state_contract": {},
        }
    description = dict(describe_backend() or {})
    return {
        "backend_kind": _normalize_text(description.get("backend_kind")),
        "backend_mode": _normalize_text(description.get("backend_mode")),
        "durable": bool(description.get("durable")),
        "fallback_active": bool(description.get("fallback_active")),
        "fallback_reason": _normalize_text(description.get("fallback_reason")),
        "last_error": _normalize_text(description.get("last_error")),
        "state_contract": dict(description.get("state_contract") or {}),
    }


def build_durable_recovery_loader_contract() -> Dict[str, Any]:
    return {
        "contract_version": DURABLE_RECOVERY_LOADER_CONTRACT_VERSION,
        "loader_kind": "durable_workspace_registry_loader",
        "executes_recovery": False,
        "deserializes_callables": False,
        "required_state": [
            "run_snapshot",
            "event_log",
            "approval_snapshot",
            "tool_continuation_descriptor",
            "loop_continuation_descriptor",
        ],
        "required_gates": [
            "durable_workspace_backend",
            "checkpoint_resume_cursor",
            "continuation_descriptor_lifecycle",
            "continuation_registry_binding",
            "approval_state_gate",
            "worker_ownership_gate",
            "loader_execution_handoff_policy",
        ],
        "descriptor_lifecycle_contract": build_continuation_descriptor_lifecycle_contract(),
        "loader_execution_handoff_policy": build_durable_loader_execution_handoff_policy_contract(),
        "fail_closed_reasons": [
            CONTINUATION_RECOVERY_REASON_WORKSPACE_BACKEND_NOT_DURABLE,
            CONTINUATION_RECOVERY_REASON_WORKSPACE_BACKEND_FALLBACK_ACTIVE,
            "run_snapshot_missing",
            CONTINUATION_RECOVERY_REASON_DESCRIPTOR_MISSING,
            CONTINUATION_RECOVERY_REASON_DESCRIPTOR_CORRUPTED,
            CONTINUATION_RECOVERY_REASON_MISSING_REGISTERED_BINDING,
            CONTINUATION_RECOVERY_REASON_ALREADY_RESOLVED,
            CONTINUATION_RECOVERY_REASON_DENIED,
        ],
    }


class DurableRecoveryLoader:
    """Rebuild a recovery candidate from persisted state without executing it."""

    def __init__(
        self,
        *,
        workspace_store: EmbeddedRunWorkspaceStore,
        continuation_registry: Any | None = None,
    ) -> None:
        self._workspace_store = workspace_store
        self._continuation_registry = continuation_registry

    def load(
        self,
        *,
        run_id: str,
        approval_request_id: str | None = None,
    ) -> Dict[str, Any]:
        normalized_run_id = _normalize_text(run_id)
        backend = _describe_workspace_backend(self._workspace_store)
        candidate = self._base_candidate(normalized_run_id, backend)
        if not bool(backend.get("durable")):
            return self._block(candidate, CONTINUATION_RECOVERY_REASON_WORKSPACE_BACKEND_NOT_DURABLE)
        if bool(backend.get("fallback_active")):
            return self._block(candidate, CONTINUATION_RECOVERY_REASON_WORKSPACE_BACKEND_FALLBACK_ACTIVE)

        run_snapshot = self._workspace_store.get_run_snapshot(normalized_run_id)
        if not run_snapshot:
            return self._block(candidate, "run_snapshot_missing")
        run_snapshot = dict(run_snapshot)
        candidate["run_snapshot"] = self._compact_run_snapshot(run_snapshot)
        candidate["event_log"] = self._load_event_log(normalized_run_id)
        candidate["recovery_operations"] = self._load_recovery_operations(run_snapshot)

        request_id = _normalize_text(
            approval_request_id
            or (run_snapshot.get("metadata") or {}).get("approval_request_id")
            or ((run_snapshot.get("metadata") or {}).get("approval_request") or {}).get("request_id")
        )
        candidate["approval_request_id"] = request_id
        approval = self._workspace_store.get_approval_snapshot(request_id) if request_id else None
        approval_status = ""
        if approval:
            approval_snapshot = dict(approval)
            candidate["approval_snapshot"] = self._compact_approval_snapshot(approval_snapshot)
            approval_status = _normalize_text(approval_snapshot.get("status")).lower()

        tool_descriptor = (
            self._workspace_store.get_tool_continuation_descriptor(request_id)
            if request_id
            else None
        )
        loop_descriptor = self._workspace_store.get_loop_continuation_descriptor(normalized_run_id)
        unsafe_keys = self._find_unsafe_descriptor_keys([tool_descriptor, loop_descriptor])
        stale_reason = ""
        if approval_status == "approved":
            stale_reason = CONTINUATION_RECOVERY_REASON_ALREADY_RESOLVED
        elif approval_status == "denied":
            stale_reason = CONTINUATION_RECOVERY_REASON_DENIED
        binding_evidence = self._resolve_bindings(tool_descriptor, loop_descriptor)
        descriptors = self._build_descriptor_evidence(
            tool_descriptor,
            loop_descriptor,
            binding_evidence=binding_evidence,
            unsafe_keys=unsafe_keys,
            stale=bool(stale_reason),
        )
        candidate["continuation_descriptors"] = descriptors
        if unsafe_keys:
            candidate["unsafe_descriptor_keys"] = unsafe_keys
            candidate["descriptor_lifecycle"] = build_continuation_descriptor_lifecycle_evidence(
                descriptors=descriptors,
                fail_closed_reason=CONTINUATION_RECOVERY_REASON_DESCRIPTOR_CORRUPTED,
                unsafe_descriptor_keys=unsafe_keys,
            )
            return self._block(candidate, CONTINUATION_RECOVERY_REASON_DESCRIPTOR_CORRUPTED)
        if stale_reason:
            candidate["descriptor_lifecycle"] = build_continuation_descriptor_lifecycle_evidence(
                descriptors=descriptors,
                fail_closed_reason=stale_reason,
                unsafe_descriptor_keys=unsafe_keys,
            )
            return self._block(candidate, stale_reason)
        if not descriptors:
            candidate["descriptor_lifecycle"] = build_continuation_descriptor_lifecycle_evidence(
                descriptors=[],
                fail_closed_reason=CONTINUATION_RECOVERY_REASON_DESCRIPTOR_MISSING,
            )
            return self._block(candidate, CONTINUATION_RECOVERY_REASON_DESCRIPTOR_MISSING)

        candidate["binding_evidence"] = binding_evidence
        if binding_evidence["missing_binding_ids"]:
            candidate["missing_binding_ids"] = list(binding_evidence["missing_binding_ids"])
            candidate["descriptor_lifecycle"] = build_continuation_descriptor_lifecycle_evidence(
                descriptors=descriptors,
                fail_closed_reason=CONTINUATION_RECOVERY_REASON_MISSING_REGISTERED_BINDING,
            )
            return self._block(candidate, CONTINUATION_RECOVERY_REASON_MISSING_REGISTERED_BINDING)
        if not binding_evidence["binding_ids"]:
            candidate["descriptor_lifecycle"] = build_continuation_descriptor_lifecycle_evidence(
                descriptors=descriptors,
                fail_closed_reason=CONTINUATION_RECOVERY_REASON_MISSING_REGISTERED_BINDING,
            )
            return self._block(candidate, CONTINUATION_RECOVERY_REASON_MISSING_REGISTERED_BINDING)
        candidate["descriptor_lifecycle"] = build_continuation_descriptor_lifecycle_evidence(
            descriptors=descriptors,
        )
        candidate["status"] = DURABLE_RECOVERY_LOADER_READY
        candidate["recovery_reason"] = CONTINUATION_RECOVERY_REASON_READY_VIA_REGISTRY
        candidate["ready"] = True
        candidate["loader_execution_handoff"] = build_durable_loader_execution_handoff_decision(
            loader_candidate=candidate,
            explicit_handoff_requested=False,
            recovery_executor_bound=False,
        )
        return candidate

    def _base_candidate(self, run_id: str, backend: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "contract_version": DURABLE_RECOVERY_LOADER_CONTRACT_VERSION,
            "status": DURABLE_RECOVERY_LOADER_BLOCKED,
            "ready": False,
            "run_id": run_id,
            "recovery_reason": "",
            "loaded_at": _utc_now(),
            "executes_recovery": False,
            "deserializes_callables": False,
            "workspace_backend": dict(backend),
            "persistence_interface": build_embedded_sdk_persistence_interface(backend),
            "loader_execution_handoff": build_durable_loader_execution_handoff_decision(
                loader_candidate={"status": DURABLE_RECOVERY_LOADER_BLOCKED, "ready": False},
                explicit_handoff_requested=False,
                recovery_executor_bound=False,
            ),
        }

    @staticmethod
    def _block(candidate: Dict[str, Any], reason: str) -> Dict[str, Any]:
        candidate["status"] = DURABLE_RECOVERY_LOADER_BLOCKED
        candidate["ready"] = False
        candidate["recovery_reason"] = _normalize_text(reason)
        return candidate

    @staticmethod
    def _compact_run_snapshot(snapshot: Dict[str, Any]) -> Dict[str, Any]:
        metadata = dict(snapshot.get("metadata") or {})
        return {
            "run_id": _normalize_text(snapshot.get("run_id")),
            "state": _normalize_text(snapshot.get("state")),
            "stop_reason": _normalize_text(snapshot.get("stop_reason")),
            "approval_request_id": _normalize_text(
                metadata.get("approval_request_id")
                or (metadata.get("approval_request") or {}).get("request_id")
            ),
            "latest_recovery_operation": dict(metadata.get("latest_recovery_operation") or {}),
        }

    @staticmethod
    def _compact_approval_snapshot(snapshot: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "request_id": _normalize_text(snapshot.get("request_id")),
            "run_id": _normalize_text(snapshot.get("run_id")),
            "status": _normalize_text(snapshot.get("status")),
            "tool_name": _normalize_text(snapshot.get("tool_name")),
        }

    def _load_event_log(self, run_id: str) -> Dict[str, Any]:
        events = self._workspace_store.get_events(run_id)
        last_event = dict(events[-1]) if events else {}
        return {
            "event_count": len(events),
            "last_event_id": _normalize_text(last_event.get("event_id")),
            "last_status_kind": _normalize_text(last_event.get("status_kind")),
        }

    @staticmethod
    def _load_recovery_operations(run_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        operations = [
            dict(item)
            for item in list((run_snapshot.get("metadata") or {}).get("recovery_operations") or [])
            if isinstance(item, dict)
        ]
        latest = dict((run_snapshot.get("metadata") or {}).get("latest_recovery_operation") or {})
        return {
            "operation_count": len(operations),
            "latest_operation_id": _normalize_text(latest.get("operation_id")),
            "latest_status": _normalize_text(latest.get("operation_status")),
            "latest_entrypoint": _normalize_text(latest.get("entrypoint")),
        }

    @staticmethod
    def _build_descriptor_evidence(
        tool_descriptor: Dict[str, Any] | None,
        loop_descriptor: Dict[str, Any] | None,
        *,
        binding_evidence: Dict[str, Any],
        unsafe_keys: List[str] | None = None,
        stale: bool = False,
    ) -> List[Dict[str, Any]]:
        descriptors: List[Dict[str, Any]] = []
        all_missing_bindings = list(binding_evidence.get("missing_binding_ids") or [])
        unsafe = bool(unsafe_keys)
        if tool_descriptor:
            binding_ids = {
                "tool_executor_binding_id": _normalize_text(tool_descriptor.get("tool_executor_binding_id")),
            }
            binding_ids = {key: value for key, value in binding_ids.items() if value}
            descriptors.append({
                "descriptor_kind": "tool_approval_continuation",
                "request_id": _normalize_text(tool_descriptor.get("request_id")),
                "status": _normalize_text(tool_descriptor.get("status")),
                "binding_ids": binding_ids,
                "lifecycle_state": classify_descriptor_state(
                    binding_ids=binding_ids,
                    missing_binding_ids=[
                        binding_id
                        for binding_id in all_missing_bindings
                        if binding_id in set(binding_ids.values())
                    ],
                    unsafe=unsafe,
                    stale=stale,
                ),
            })
        if loop_descriptor:
            binding_ids = {
                key: _normalize_text(loop_descriptor.get(key))
                for key in ("reflector_binding_id", "reviewer_binding_id", "fallback_handler_binding_id")
                if _normalize_text(loop_descriptor.get(key))
            }
            descriptors.append({
                "descriptor_kind": "loop_continuation",
                "request_id": _normalize_text(loop_descriptor.get("request_id")),
                "status": _normalize_text(loop_descriptor.get("status")),
                "binding_ids": binding_ids,
                "lifecycle_state": classify_descriptor_state(
                    binding_ids=binding_ids,
                    missing_binding_ids=[
                        binding_id
                        for binding_id in all_missing_bindings
                        if binding_id in set(binding_ids.values())
                    ],
                    unsafe=unsafe,
                    stale=stale,
                ),
            })
        return descriptors

    @staticmethod
    def _find_unsafe_descriptor_keys(descriptors: List[Dict[str, Any] | None]) -> List[str]:
        unsafe: list[str] = []
        for descriptor in descriptors:
            if not isinstance(descriptor, dict):
                continue
            for key, value in descriptor.items():
                normalized_key = _normalize_text(key)
                if normalized_key in UNSAFE_DESCRIPTOR_KEYS or callable(value):
                    unsafe.append(normalized_key)
        return list(dict.fromkeys(unsafe))

    def _resolve_bindings(
        self,
        tool_descriptor: Dict[str, Any] | None,
        loop_descriptor: Dict[str, Any] | None,
    ) -> Dict[str, Any]:
        binding_ids: Dict[str, str] = {}
        if tool_descriptor:
            binding_ids["tool_executor_binding_id"] = _normalize_text(tool_descriptor.get("tool_executor_binding_id"))
        if loop_descriptor:
            for key in ("reflector_binding_id", "reviewer_binding_id", "fallback_handler_binding_id"):
                value = _normalize_text(loop_descriptor.get(key))
                if value:
                    binding_ids[key] = value
        binding_ids = {key: value for key, value in binding_ids.items() if value}
        missing = [
            binding_id
            for binding_id in binding_ids.values()
            if not callable(self._resolve_binding(binding_id))
        ]
        return {
            "binding_ids": binding_ids,
            "missing_binding_ids": missing,
            "resolved_binding_count": len(binding_ids) - len(missing),
            "all_bindings_resolved": bool(binding_ids) and not missing,
        }

    def _resolve_binding(self, binding_id: str) -> Any | None:
        resolve = getattr(self._continuation_registry, "resolve", None)
        if not callable(resolve):
            return None
        return resolve(binding_id)
