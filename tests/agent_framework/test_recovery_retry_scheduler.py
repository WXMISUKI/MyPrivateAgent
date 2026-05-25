import unittest

from backend.agent_framework.continuation_registry import InMemoryEmbeddedContinuationRegistry
from backend.agent_framework.persistence import InMemoryEmbeddedRunWorkspaceStore
from backend.agent_framework.recovery_retry_scheduler import (
    RECOVERY_RETRY_PRODUCTION_SCHEDULER_GATE_CONTRACT_VERSION,
    RECOVERY_RETRY_SCHEDULER_CONTRACT_VERSION,
    RecoveryRetryScheduler,
    build_recovery_retry_production_scheduler_gate_contract,
    build_recovery_retry_scheduler_contract,
)
from backend.agent_framework.sdk import EmbeddedAgentRuntimeSDK


class _DurableRetryWorkspaceStore(InMemoryEmbeddedRunWorkspaceStore):
    def describe_backend(self):
        backend = super().describe_backend()
        backend.update({
            "backend_kind": "sqlalchemy",
            "backend_mode": "strict_sql",
            "durable": True,
            "fallback_active": False,
        })
        return backend


class _FakeAuditRecorder:
    def __init__(self):
        self.operations = []

    def record_operation(self, **kwargs):
        self.operations.append(kwargs)
        operation = kwargs["operation"]
        return {
            "trace_written": True,
            "dedupe_key": f"retry-audit:{operation['operation_id']}",
            "operation_id": operation["operation_id"],
        }


def _tool_executor(_run):
    return {
        "tool_name": "filesystem_write",
        "args": {"path": "retry.md"},
        "result": "ok",
    }


def _reviewer(_run):
    return {"status": "approved", "summary": "retry ok"}


def _build_retryable_workspace():
    store = _DurableRetryWorkspaceStore()
    registry = InMemoryEmbeddedContinuationRegistry()
    registry.register("tool_executor.filesystem_write", _tool_executor)
    registry.register("reviewer.quality_gate", _reviewer)
    writer = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)
    result = writer.create_run({
        "conversation_id": 42,
        "user_id": 7,
        "model_name": "doubao",
        "run_kind": "chat",
    })
    executed = writer.execute_run(
        result["run"]["run_id"],
        tool_policy=lambda _run: {
            "status": "approval_required",
            "tool_name": "filesystem_write",
            "tool_args": {"path": "retry.md"},
            "reason": "approval required",
        },
        tool_executor=_tool_executor,
        reviewer=_reviewer,
    )
    run_id = result["run"]["run_id"]
    request_id = executed["approval_request"]["request_id"]
    previous_operation = _build_previous_operation(
        run_id=run_id,
        request_id=request_id,
        recovery_reason="transient_workspace_unavailable",
    )
    snapshot = store.get_run_snapshot(run_id)
    metadata = dict(snapshot.get("metadata") or {})
    metadata["latest_recovery_operation"] = dict(previous_operation)
    metadata["recovery_operations"] = [dict(previous_operation)]
    snapshot["metadata"] = metadata
    store.save_run_snapshot(snapshot)
    return store, registry, run_id, request_id, previous_operation


def _build_previous_operation(*, run_id, request_id, recovery_reason, retry=None):
    operation = {
        "contract_version": "phase-ii-durable-recovery-operation-v1",
        "operation_id": f"recovery_operation:{run_id}:submit_approval.approved:previous",
        "run_id": run_id,
        "entrypoint": "submit_approval.approved",
        "operation_status": "blocked",
        "recovery_reason": recovery_reason,
        "blocked_reason": recovery_reason,
        "continuation_ref": {
            "continuation_kind": "tool_approval",
            "continuation_id": request_id,
            "descriptor_present": True,
            "binding_ids": {"tool_executor_binding_id": "tool_executor.filesystem_write"},
            "missing_binding_ids": [],
        },
        "workspace_backend": {
            "backend_kind": "sqlalchemy",
            "backend_mode": "strict_sql",
            "durable": True,
            "fallback_active": False,
        },
        "persistence_posture": "durable_ready",
        "worker_ownership": {
            "implemented": False,
            "boundary": "worker_lease_not_implemented",
        },
        "recorded_at": "2026-05-24T00:00:00+00:00",
    }
    if retry is not None:
        operation["retry"] = dict(retry)
    return operation


class RecoveryRetrySchedulerTests(unittest.TestCase):
    def test_contract_declares_opt_in_scheduler(self):
        contract = build_recovery_retry_scheduler_contract()

        self.assertEqual(contract["contract_version"], RECOVERY_RETRY_SCHEDULER_CONTRACT_VERSION)
        self.assertTrue(contract["implemented"])
        self.assertFalse(contract["enabled_by_default"])
        self.assertTrue(contract["opt_in_required"])
        self.assertFalse(contract["production_automatic_retry_supported"])
        self.assertEqual(
            contract["production_scheduler_gate"]["contract_version"],
            RECOVERY_RETRY_PRODUCTION_SCHEDULER_GATE_CONTRACT_VERSION,
        )
        self.assertEqual(contract["production_scheduler_gate"]["overall_status"], "blocked")
        self.assertFalse(contract["production_scheduler_gate"]["automatic_retry_enabled_by_default"])
        self.assertIn(
            "durable_scheduling_state",
            contract["production_scheduler_gate"]["missing_sections"],
        )
        self.assertEqual(contract["retry_policy"]["contract_version"], "phase-ii-recovery-retry-protocol-v1")
        self.assertTrue(contract["executes_only_recovery_entrypoints"])

    def test_production_scheduler_gate_reports_ready_only_when_all_sections_are_ready(self):
        blocked = build_recovery_retry_production_scheduler_gate_contract()

        self.assertEqual(
            blocked["contract_version"],
            RECOVERY_RETRY_PRODUCTION_SCHEDULER_GATE_CONTRACT_VERSION,
        )
        self.assertEqual(blocked["overall_status"], "blocked")
        self.assertFalse(blocked["ready"])
        self.assertFalse(blocked["automatic_retry_enabled_by_default"])
        self.assertIn("worker_ownership", blocked["missing_sections"])
        self.assertIn("no_background_retry_loop", blocked["non_goals"])

        ready = build_recovery_retry_production_scheduler_gate_contract(
            durable_scheduling_state_ready=True,
            deterministic_idempotency_dedupe_ready=True,
            backoff_clock_ready=True,
            worker_ownership_ready=True,
            recovery_audit_timeline_ready=True,
        )

        self.assertEqual(ready["overall_status"], "ready")
        self.assertTrue(ready["ready"])
        self.assertEqual(ready["missing_sections"], [])
        self.assertFalse(ready["automatic_retry_enabled_by_default"])

    def test_scheduler_default_is_disabled_and_does_not_execute_retry(self):
        store, registry, run_id, request_id, previous_operation = _build_retryable_workspace()
        sdk = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)
        scheduler = RecoveryRetryScheduler(sdk=sdk)

        decision = scheduler.schedule_next_attempt(run_id)

        self.assertEqual(decision["status"], "disabled")
        self.assertTrue(decision["eligible"])
        self.assertFalse(decision["will_execute"])
        self.assertEqual(decision["retry_attempt"]["attempt_number"], 1)
        self.assertEqual(decision["retry_attempt"]["previous_operation_id"], previous_operation["operation_id"])
        self.assertEqual(store.get_approval_snapshot(request_id)["status"], "pending")

    def test_production_automatic_retry_fails_closed_when_gate_is_blocked(self):
        store, registry, run_id, request_id, _previous_operation = _build_retryable_workspace()
        sdk = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)

        decision = sdk.schedule_recovery_retry(
            run_id,
            enabled=True,
            production_automatic_retry=True,
        )

        self.assertEqual(decision["status"], "blocked")
        self.assertEqual(decision["blocked_reason"], "production_scheduler_gate_blocked")
        self.assertTrue(decision["eligible"])
        self.assertFalse(decision["will_execute"])
        self.assertEqual(
            decision["production_scheduler_gate"]["contract_version"],
            RECOVERY_RETRY_PRODUCTION_SCHEDULER_GATE_CONTRACT_VERSION,
        )
        self.assertEqual(decision["production_scheduler_gate"]["overall_status"], "blocked")
        self.assertIn(
            "durable_scheduling_state",
            decision["production_scheduler_gate"]["missing_sections"],
        )
        self.assertEqual(store.get_approval_snapshot(request_id)["status"], "pending")

    def test_scheduler_executes_enabled_retry_and_records_compact_evidence(self):
        store, registry, run_id, _request_id, previous_operation = _build_retryable_workspace()
        sdk = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)
        audit = _FakeAuditRecorder()

        decision = sdk.schedule_recovery_retry(
            run_id,
            enabled=True,
            audit_recorder=audit,
            user_id=7,
            conversation_id=42,
        )

        self.assertEqual(decision["status"], "executed")
        self.assertTrue(decision["will_execute"])
        self.assertEqual(decision["result_state"], "observing")
        latest = decision["latest_operation"]
        self.assertEqual(latest["operation_status"], "recovered")
        self.assertEqual(latest["retry"]["attempt_number"], 1)
        self.assertEqual(latest["retry"]["previous_operation_id"], previous_operation["operation_id"])
        self.assertEqual(latest["retry"]["status"], "retryable")
        self.assertEqual(latest["retry"]["recovery_reason"], "transient_workspace_unavailable")
        self.assertTrue(decision["audit_trace"]["trace_written"])
        self.assertEqual(audit.operations[0]["operation"]["operation_id"], latest["operation_id"])

    def test_scheduler_stops_for_terminal_recovery_reason(self):
        store, registry, run_id, request_id, _previous = _build_retryable_workspace()
        terminal_operation = _build_previous_operation(
            run_id=run_id,
            request_id=request_id,
            recovery_reason="denied",
        )
        snapshot = store.get_run_snapshot(run_id)
        metadata = dict(snapshot.get("metadata") or {})
        metadata["latest_recovery_operation"] = dict(terminal_operation)
        metadata["recovery_operations"] = [dict(terminal_operation)]
        snapshot["metadata"] = metadata
        store.save_run_snapshot(snapshot)
        sdk = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)

        decision = sdk.schedule_recovery_retry(run_id, enabled=True)

        self.assertEqual(decision["status"], "terminal")
        self.assertFalse(decision["eligible"])
        self.assertFalse(decision["will_execute"])
        self.assertEqual(decision["classifier"]["blocked_reason"], "terminal_retry_decision")
        self.assertEqual(store.get_approval_snapshot(request_id)["status"], "pending")

    def test_scheduler_stops_for_exhausted_previous_retry(self):
        store, registry, run_id, request_id, _previous = _build_retryable_workspace()
        exhausted_operation = _build_previous_operation(
            run_id=run_id,
            request_id=request_id,
            recovery_reason="transient_workspace_unavailable",
            retry={
                "attempt_number": 3,
                "max_attempts": 3,
                "status": "exhausted",
                "recovery_reason": "transient_workspace_unavailable",
            },
        )
        snapshot = store.get_run_snapshot(run_id)
        metadata = dict(snapshot.get("metadata") or {})
        metadata["latest_recovery_operation"] = dict(exhausted_operation)
        metadata["recovery_operations"] = [dict(exhausted_operation)]
        snapshot["metadata"] = metadata
        store.save_run_snapshot(snapshot)
        sdk = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)

        decision = sdk.schedule_recovery_retry(run_id, enabled=True)

        self.assertEqual(decision["status"], "blocked")
        self.assertFalse(decision["eligible"])
        self.assertFalse(decision["will_execute"])
        self.assertEqual(decision["classifier"]["blocked_reason"], "terminal_retry_decision")


if __name__ == "__main__":
    unittest.main()
