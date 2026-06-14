"""Deterministic Embedded SDK recovery acceptance smoke evidence."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Callable, Dict

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.agent_framework.adapters import SQLAlchemyEmbeddedRunWorkspaceStore
from backend.agent_framework.continuation_registry import InMemoryEmbeddedContinuationRegistry
from backend.agent_framework.persistence import InMemoryEmbeddedRunWorkspaceStore
from backend.agent_framework.sdk import EmbeddedAgentRuntimeSDK
from backend.database import Base
import backend.models  # noqa: F401


EMBEDDED_SDK_RECOVERY_ACCEPTANCE_SMOKE_VERSION = "embedded-sdk-recovery-acceptance-smoke-v1"


def _tool_executor(_run: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "tool_name": "filesystem_write",
        "args": {"path": "embedded-sdk-recovery-acceptance.md"},
        "result": "ok",
    }


def _reviewer(_run: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "reviewer": "quality_gate",
        "status": "approved",
        "summary": "embedded sdk recovery acceptance ok",
    }


def _tool_policy(_run: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "approval_required",
        "tool_name": "filesystem_write",
        "tool_args": {"path": "embedded-sdk-recovery-acceptance.md"},
        "reason": "Acceptance smoke validates explicit Embedded SDK recovery.",
    }


def _new_registry(*, include_bindings: bool) -> InMemoryEmbeddedContinuationRegistry:
    registry = InMemoryEmbeddedContinuationRegistry()
    if include_bindings:
        registry.register(
            "tool_executor.filesystem_write",
            _tool_executor,
            binding_kind="tool_executor",
            metadata={"tool_name": "filesystem_write"},
        )
        registry.register(
            "reviewer.quality_gate",
            _reviewer,
            binding_kind="reviewer",
            metadata={"reviewer": "quality_gate"},
        )
    return registry


def _compact_workspace_backend(store: Any) -> Dict[str, Any]:
    describe_backend = getattr(store, "describe_backend", None)
    backend = dict(describe_backend() or {}) if callable(describe_backend) else {}
    return {
        "backend_kind": str(backend.get("backend_kind") or "").strip(),
        "backend_mode": str(backend.get("backend_mode") or "").strip(),
        "durable": bool(backend.get("durable")),
        "fallback_active": bool(backend.get("fallback_active")),
        "fallback_reason": str(backend.get("fallback_reason") or "").strip(),
        "last_error": str(backend.get("last_error") or "").strip(),
    }


def _compact_continuation(value: Dict[str, Any] | None) -> Dict[str, Any]:
    item = dict(value or {})
    binding_ids = dict(item.get("binding_ids") or {})
    return {
        "descriptor_present": bool(item.get("descriptor_present")),
        "recovery_status": str(item.get("recovery_status") or "").strip(),
        "recovery_reason": str(item.get("recovery_reason") or "").strip(),
        "binding_ids": {
            key: str(value or "").strip()
            for key, value in binding_ids.items()
            if str(value or "").strip()
        },
        "requires_registry_binding": bool(item.get("requires_registry_binding")),
        "requires_durable_workspace": bool(item.get("requires_durable_workspace")),
    }


def _compact_recovery_entrypoints(probe: Dict[str, Any]) -> list[Dict[str, Any]]:
    return [
        {
            "method": str(item.get("method") or "").strip(),
            "mode": str(item.get("mode") or "").strip(),
            "available": bool(item.get("available")),
            "run_state": str(item.get("run_state") or "").strip(),
            "recovery_reason": str(item.get("recovery_reason") or "").strip(),
            "blocked_reason": str(item.get("blocked_reason") or "").strip(),
        }
        for item in list(probe.get("recovery_entrypoints") or [])
        if isinstance(item, dict)
    ]


def _compact_operation(operation: Dict[str, Any] | None) -> Dict[str, Any]:
    item = dict(operation or {})
    workspace = dict(item.get("workspace") or item.get("workspace_backend") or {})
    return {
        "operation_status": str(item.get("operation_status") or "").strip(),
        "entrypoint": str(item.get("entrypoint") or "").strip(),
        "recovery_reason": str(item.get("recovery_reason") or "").strip(),
        "blocked_reason": str(item.get("blocked_reason") or "").strip(),
        "persistence_posture": str(item.get("persistence_posture") or "").strip(),
        "workspace": {
            "backend_kind": str(workspace.get("backend_kind") or "").strip(),
            "backend_mode": str(workspace.get("backend_mode") or "").strip(),
            "durable": bool(workspace.get("durable")),
            "fallback_active": bool(workspace.get("fallback_active")),
        },
    }


def _collect_latest_operation(*payloads: Dict[str, Any]) -> Dict[str, Any]:
    for payload in reversed(payloads):
        run = dict(payload.get("run") or {})
        metadata = dict(run.get("metadata") or {})
        operation = dict(metadata.get("latest_recovery_operation") or {})
        if operation:
            return _compact_operation(operation)
    return {}


def _build_blocker(code: str, message: str, **evidence: Any) -> Dict[str, Any]:
    blocker = {
        "code": code,
        "message": message,
    }
    if evidence:
        blocker["evidence"] = dict(evidence)
    return blocker


def _build_payload(
    *,
    scenario: str,
    store: Any,
    registry: InMemoryEmbeddedContinuationRegistry,
    probe: Dict[str, Any],
    approved: Dict[str, Any] | None = None,
    resumed: Dict[str, Any] | None = None,
    extra_blockers: list[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    approved = dict(approved or {})
    resumed = dict(resumed or {})
    workspace_backend = _compact_workspace_backend(store)
    tool_continuation = _compact_continuation(dict(probe.get("tool_continuation") or {}))
    loop_continuation = _compact_continuation(dict(probe.get("loop_continuation") or {}))
    resumed_state = str((dict(resumed.get("run") or {})).get("state") or "").strip()
    approved_state = str((dict(approved.get("run") or {})).get("state") or "").strip()
    recovery_entrypoints = _compact_recovery_entrypoints(probe)
    registry_catalog = registry.build_catalog()

    blockers = list(extra_blockers or [])
    if not bool(workspace_backend.get("durable")):
        blockers.append(_build_blocker(
            "DURABLE_WORKSPACE_REQUIRED",
            "Embedded SDK recovery acceptance requires a durable workspace backend.",
            workspace_backend=workspace_backend,
        ))
    if bool(workspace_backend.get("fallback_active")):
        blockers.append(_build_blocker(
            "WORKSPACE_FALLBACK_ACTIVE",
            "Workspace fallback blocks durable recovery acceptance.",
            workspace_backend=workspace_backend,
        ))
    missing_binding = {
        str(tool_continuation.get("recovery_reason") or "").strip(),
        str(loop_continuation.get("recovery_reason") or "").strip(),
        str(probe.get("recovery_reason") or "").strip(),
    }
    if "missing_registered_binding" in missing_binding:
        blockers.append(_build_blocker(
            "REGISTRY_BINDING_REQUIRED",
            "Required persisted continuation binding is not registered.",
            registry_binding_count=registry_catalog.get("total_bindings"),
        ))
    if not bool(probe.get("recoverable")):
        blockers.append(_build_blocker(
            "RECOVERY_PROBE_NOT_RECOVERABLE",
            "Recovery probe did not report a recoverable run.",
            recovery_reason=str(probe.get("recovery_reason") or "").strip(),
        ))

    accepted = (
        not blockers
        and bool(probe.get("recoverable"))
        and bool(workspace_backend.get("durable"))
        and not bool(workspace_backend.get("fallback_active"))
        and str(tool_continuation.get("recovery_reason") or "") == "ready_via_registry"
        and str(loop_continuation.get("recovery_reason") or "") == "ready_via_registry"
        and approved_state == "observing"
        and resumed_state == "done"
    )
    if bool(probe.get("recoverable")) and (approved_state or resumed_state) and not accepted and not blockers:
        blockers.append(_build_blocker(
            "RECOVERY_ACCEPTANCE_CHAIN_INCOMPLETE",
            "Recovery probe was recoverable but approval or loop continuation did not complete.",
            approved_state=approved_state,
            resumed_state=resumed_state,
        ))

    payload = {
        "contract_version": EMBEDDED_SDK_RECOVERY_ACCEPTANCE_SMOKE_VERSION,
        "scenario": scenario,
        "decision": "accepted" if accepted else "blocked",
        "workspace_backend": workspace_backend,
        "continuation_registry": {
            "registry_type": str(registry_catalog.get("registry_type") or "").strip(),
            "total_bindings": int(registry_catalog.get("total_bindings") or 0),
            "bindings": [
                {
                    "binding_id": str(item.get("binding_id") or "").strip(),
                    "binding_kind": str(item.get("binding_kind") or "").strip(),
                    "handler_name": str(item.get("handler_name") or "").strip(),
                    "metadata": dict(item.get("metadata") or {}),
                }
                for item in list(registry_catalog.get("bindings") or [])
                if isinstance(item, dict)
            ],
        },
        "recovery_entrypoints": recovery_entrypoints,
        "tool_continuation": tool_continuation,
        "loop_continuation": loop_continuation,
        "loop_continuation_result": {
            "approved_state": approved_state,
            "resumed_state": resumed_state,
        },
        "operation_evidence": {
            "latest_recovery_operation": _collect_latest_operation(approved, resumed),
        },
        "blockers": blockers,
        "warnings": [],
        "non_goals": [
            "no_worker_lease",
            "no_background_auto_recovery",
            "no_distributed_executor",
            "no_real_llm_execution",
            "no_default_chat_behavior_change",
            "no_provider_invocation",
        ],
    }
    return sanitize_acceptance_evidence(payload)


def _run_recovery_chain(
    *,
    store: Any,
    writer_registry: InMemoryEmbeddedContinuationRegistry,
    reader_registry: InMemoryEmbeddedContinuationRegistry,
    execute_recovery: bool,
) -> Dict[str, Any]:
    writer = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=writer_registry)
    result = writer.create_run({
        "conversation_id": 42,
        "user_id": 7,
        "model_name": "doubao",
        "run_kind": "chat",
    })
    executed = writer.execute_run(
        result["run"]["run_id"],
        tool_policy=_tool_policy,
        tool_executor=_tool_executor,
        reviewer=_reviewer,
    )

    reader = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=reader_registry)
    probe = reader.probe_run_recovery(result["run"]["run_id"])
    approved: Dict[str, Any] = {}
    resumed: Dict[str, Any] = {}
    if execute_recovery and bool(probe.get("recoverable")):
        approved = reader.submit_approval(executed["approval_request"]["request_id"], "approved")
        resumed = reader.resume_run(result["run"]["run_id"], continue_loop=True)
    return {
        "probe": probe,
        "approved": approved,
        "resumed": resumed,
    }


def _with_sqlite_store(callback: Callable[[SQLAlchemyEmbeddedRunWorkspaceStore], Dict[str, Any]]) -> Dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        sqlite_path = Path(tmp_dir) / "embedded_sdk_recovery_acceptance.db"
        engine = create_engine(
            f"sqlite:///{sqlite_path.as_posix()}",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        try:
            store = SQLAlchemyEmbeddedRunWorkspaceStore(
                testing_session_local,
                allow_operation_fallback=False,
                backend_mode="strict_sql",
            )
            return callback(store)
        finally:
            Base.metadata.drop_all(bind=engine)
            engine.dispose()


def run_embedded_sdk_recovery_acceptance_smoke(
    scenario: str = "accepted",
) -> Dict[str, Any]:
    normalized = str(scenario or "accepted").strip().lower().replace("_", "-")
    if normalized in {"accepted", "durable", "durable-registry-backed"}:
        def _run(store: SQLAlchemyEmbeddedRunWorkspaceStore) -> Dict[str, Any]:
            registry = _new_registry(include_bindings=True)
            result = _run_recovery_chain(
                store=store,
                writer_registry=registry,
                reader_registry=registry,
                execute_recovery=True,
            )
            return _build_payload(
                scenario="accepted",
                store=store,
                registry=registry,
                probe=result["probe"],
                approved=result["approved"],
                resumed=result["resumed"],
            )

        return _with_sqlite_store(_run)

    if normalized in {"memory-only", "memory", "blocked-memory"}:
        store = InMemoryEmbeddedRunWorkspaceStore()
        registry = _new_registry(include_bindings=True)
        result = _run_recovery_chain(
            store=store,
            writer_registry=registry,
            reader_registry=registry,
            execute_recovery=False,
        )
        return _build_payload(
            scenario="memory-only",
            store=store,
            registry=registry,
            probe=result["probe"],
        )

    if normalized in {"missing-registry-binding", "missing-registry", "blocked-registry"}:
        def _run(store: SQLAlchemyEmbeddedRunWorkspaceStore) -> Dict[str, Any]:
            writer_registry = _new_registry(include_bindings=True)
            reader_registry = _new_registry(include_bindings=False)
            result = _run_recovery_chain(
                store=store,
                writer_registry=writer_registry,
                reader_registry=reader_registry,
                execute_recovery=False,
            )
            return _build_payload(
                scenario="missing-registry-binding",
                store=store,
                registry=reader_registry,
                probe=result["probe"],
            )

        return _with_sqlite_store(_run)

    return {
        "contract_version": EMBEDDED_SDK_RECOVERY_ACCEPTANCE_SMOKE_VERSION,
        "scenario": normalized,
        "decision": "blocked",
        "workspace_backend": {},
        "recovery_entrypoints": [],
        "tool_continuation": {},
        "loop_continuation": {},
        "loop_continuation_result": {},
        "operation_evidence": {},
        "blockers": [
            _build_blocker(
                "UNKNOWN_ACCEPTANCE_SCENARIO",
                f"Unknown Embedded SDK recovery acceptance scenario: {scenario}",
            )
        ],
        "warnings": [],
        "non_goals": [
            "no_worker_lease",
            "no_background_auto_recovery",
            "no_distributed_executor",
            "no_real_llm_execution",
            "no_default_chat_behavior_change",
            "no_provider_invocation",
        ],
    }


def sanitize_acceptance_evidence(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): sanitize_acceptance_evidence(item)
            for key, item in value.items()
            if not callable(item) and not _is_unsafe_object(item)
        }
    if isinstance(value, list):
        return [
            sanitize_acceptance_evidence(item)
            for item in value
            if not callable(item) and not _is_unsafe_object(item)
        ]
    if isinstance(value, tuple):
        return [
            sanitize_acceptance_evidence(item)
            for item in value
            if not callable(item) and not _is_unsafe_object(item)
        ]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _is_unsafe_object(value: Any) -> bool:
    if value is None or isinstance(value, (str, int, float, bool, dict, list, tuple)):
        return False
    module = str(getattr(value.__class__, "__module__", "") or "")
    if module.startswith(("backend.", "agent_framework.", "sqlalchemy.")):
        return True
    return hasattr(value, "__dict__")
