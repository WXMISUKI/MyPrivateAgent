import unittest

from backend.agent_framework.child_executor_dispatcher import (
    CHILD_EXECUTOR_DISPATCH_ATTEMPT_HANDOFF_CONTRACT_VERSION,
    CHILD_EXECUTOR_DISPATCH_RESULT_HANDOFF_CONTRACT_VERSION,
    CHILD_EXECUTOR_DISPATCH_RESULT_RETRY_AUDIT_POLICY_CONTRACT_VERSION,
    CHILD_EXECUTOR_DISPATCHER_CONTRACT_VERSION,
    ChildExecutorDispatcher,
    build_child_executor_dispatch_attempt_handoff_contract,
    build_child_executor_dispatch_result_handoff_contract,
    build_child_executor_dispatch_result_retry_audit_policy_contract,
    build_child_executor_dispatcher_contract,
)
from backend.agent_framework.child_executor_sandbox_worker_backend import (
    SandboxChildExecutorBackend,
    build_sandbox_dispatch_attempt_envelope,
)


def _ready_dispatch_contract():
    return {
        "contract_version": "phase-ii-child-executor-dispatch-v1",
        "overall_status": "ready",
        "dispatch_ready": True,
        "will_dispatch": False,
        "backend_id": "test_worker",
        "backend_status": "ready",
        "backend_dispatch_ready": True,
        "gate_allowed": True,
        "prerequisites_ready": True,
        "blockers": [],
    }


def _ready_sandbox_dispatch_contract():
    return {
        **_ready_dispatch_contract(),
        "backend_id": "sandbox_worker",
        "backend_adapter_kind": "sandbox_worker",
        "sandbox_backend_selected": True,
        "sandbox_backend_ready": True,
        "sandbox_adapter_ready": True,
        "sandbox_guard_ready": True,
        "sandbox_audit_ready": True,
        "sandbox_idempotency_ready": True,
    }


def _ready_sandbox_dispatch_contract_with_binding():
    return {
        **_ready_sandbox_dispatch_contract(),
        "child_executor_sandbox_backend_binding": {
            "contract_version": "phase-ii-child-executor-sandbox-backend-binding-v1",
            "overall_status": "ready",
            "ready": True,
            "backend_id": "sandbox_worker",
            "binding_status": "ready",
            "dispatcher_binding_ready": True,
            "missing_sections": [],
        },
    }


class _FakeAuditRecorder:
    def __init__(self):
        self.dispatches = []

    def record_dispatch(self, *, dispatch_attempt):
        self.dispatches.append(dispatch_attempt)
        return {
            "trace_written": True,
            "attempt_id": dispatch_attempt["attempt_id"],
            "dedupe_key": f"child-dispatch:{dispatch_attempt['attempt_id']}",
        }


class ChildExecutorDispatcherTests(unittest.TestCase):
    def test_contract_declares_opt_in_dispatcher(self):
        contract = build_child_executor_dispatcher_contract()

        self.assertEqual(contract["contract_version"], CHILD_EXECUTOR_DISPATCHER_CONTRACT_VERSION)
        self.assertTrue(contract["implemented"])
        self.assertFalse(contract["enabled_by_default"])
        self.assertTrue(contract["opt_in_required"])
        self.assertFalse(contract["default_will_dispatch"])

    def test_dispatch_attempt_handoff_blocks_default_non_sandbox_contract(self):
        handoff = build_child_executor_dispatch_attempt_handoff_contract(
            dispatch_contract={
                **_ready_dispatch_contract(),
                "overall_status": "blocked",
                "dispatch_ready": False,
            }
        )

        self.assertEqual(
            handoff["contract_version"],
            CHILD_EXECUTOR_DISPATCH_ATTEMPT_HANDOFF_CONTRACT_VERSION,
        )
        self.assertEqual(handoff["overall_status"], "blocked")
        self.assertFalse(handoff["ready"])
        self.assertFalse(handoff["will_dispatch"])
        self.assertIn("dispatch_contract_ready", handoff["missing_sections"])
        self.assertIn("sandbox_backend_selected", handoff["missing_sections"])

    def test_dispatch_attempt_handoff_ready_for_opt_in_sandbox_envelope(self):
        handoff = build_child_executor_dispatch_attempt_handoff_contract(
            dispatch_contract=_ready_sandbox_dispatch_contract()
        )

        self.assertEqual(handoff["overall_status"], "ready")
        self.assertTrue(handoff["ready"])
        self.assertTrue(handoff["attempt_envelope_supported"])
        self.assertTrue(handoff["attempt_validation_ready"])
        self.assertTrue(handoff["unsafe_payload_guard_ready"])
        self.assertFalse(handoff["will_dispatch"])

    def test_dispatch_attempt_handoff_guards_unsafe_payload(self):
        handoff = build_child_executor_dispatch_attempt_handoff_contract(
            dispatch_contract=_ready_sandbox_dispatch_contract(),
            payload={"child_run_id": "child-1", "handler": object()},
        )

        self.assertEqual(handoff["overall_status"], "blocked")
        self.assertFalse(handoff["unsafe_payload_guard_ready"])
        self.assertIn("unsafe_payload_guard", handoff["missing_sections"])
        self.assertEqual(handoff["unsafe_payload_keys"], ["handler"])

    def test_dispatcher_default_disabled_does_not_invoke_backend(self):
        invoked = []
        dispatcher = ChildExecutorDispatcher(
            backend_adapters={"test_worker": lambda payload: invoked.append(payload) or {"status": "completed"}},
        )

        attempt = dispatcher.dispatch(
            dispatch_contract=_ready_dispatch_contract(),
            payload={"parent_run_id": "parent-1", "child_run_id": "child-1"},
        )

        self.assertEqual(attempt["dispatch_status"], "blocked")
        self.assertEqual(attempt["blocked_reason"], "dispatcher_disabled")
        self.assertFalse(attempt["will_dispatch"])
        self.assertEqual(attempt["dispatch_result_handoff"]["overall_status"], "blocked")
        self.assertFalse(attempt["dispatch_result_handoff"]["parent_merge_performed"])
        self.assertEqual(invoked, [])

    def test_dispatcher_fails_closed_when_dispatch_contract_is_blocked(self):
        audit = _FakeAuditRecorder()
        dispatcher = ChildExecutorDispatcher(enabled=True, backend_adapters={}, audit_recorder=audit)
        blocked_contract = {
            **_ready_dispatch_contract(),
            "overall_status": "blocked",
            "dispatch_ready": False,
            "blockers": ["worker_backend_dispatch_ready"],
        }

        attempt = dispatcher.dispatch(dispatch_contract=blocked_contract, payload={})

        self.assertEqual(attempt["dispatch_status"], "blocked")
        self.assertEqual(attempt["blocked_reason"], "dispatch_contract_not_ready")
        self.assertIn("worker_backend_dispatch_ready", attempt["blockers"])
        self.assertFalse(attempt["will_dispatch"])
        self.assertTrue(attempt["audit"]["trace_written"])
        self.assertEqual(audit.dispatches[0]["blocked_reason"], "dispatch_contract_not_ready")

    def test_dispatcher_invokes_ready_backend_and_records_audit(self):
        audit = _FakeAuditRecorder()

        def _adapter(payload):
            return {
                "status": "completed",
                "child_run_id": payload["child_run_id"],
                "summary": "child completed",
                "output_ref": "artifact://child-1/output",
            }

        dispatcher = ChildExecutorDispatcher(
            enabled=True,
            backend_adapters={"test_worker": _adapter},
            audit_recorder=audit,
        )

        attempt = dispatcher.dispatch(
            dispatch_contract=_ready_dispatch_contract(),
            payload={
                "parent_run_id": "parent-1",
                "child_run_id": "child-1",
                "intent_label": "general_analysis",
                "input_preview": "analyze this",
            },
        )

        self.assertEqual(attempt["dispatch_status"], "dispatched")
        self.assertTrue(attempt["dispatched"])
        self.assertTrue(attempt["will_dispatch"])
        self.assertEqual(attempt["backend_result"]["child_run_id"], "child-1")
        self.assertEqual(attempt["backend_result"]["output_ref"], "artifact://child-1/output")
        self.assertTrue(attempt["audit"]["trace_written"])
        self.assertEqual(audit.dispatches[0]["attempt_id"], attempt["attempt_id"])
        handoff = attempt["dispatch_result_handoff"]
        self.assertEqual(handoff["contract_version"], CHILD_EXECUTOR_DISPATCH_RESULT_HANDOFF_CONTRACT_VERSION)
        self.assertEqual(handoff["overall_status"], "ready")
        self.assertEqual(handoff["child_run_id"], "child-1")
        self.assertTrue(handoff["output_ref_present"])
        self.assertTrue(handoff["audit_evidence_present"])
        self.assertFalse(handoff["parent_merge_performed"])
        self.assertFalse(handoff["merge_authorization"])
        self.assertFalse(handoff["retry_scheduled"])
        retry_policy = handoff["dispatch_result_retry_audit_policy"]
        self.assertEqual(
            retry_policy["contract_version"],
            CHILD_EXECUTOR_DISPATCH_RESULT_RETRY_AUDIT_POLICY_CONTRACT_VERSION,
        )
        self.assertEqual(retry_policy["retry_policy_status"], "not_required")
        self.assertFalse(retry_policy["retry_scheduled"])
        self.assertFalse(retry_policy["will_retry"])

    def test_dispatcher_fails_closed_when_backend_adapter_raises(self):
        def _adapter(_payload):
            raise RuntimeError("sandbox unavailable")

        dispatcher = ChildExecutorDispatcher(
            enabled=True,
            backend_adapters={"test_worker": _adapter},
        )

        attempt = dispatcher.dispatch(dispatch_contract=_ready_dispatch_contract(), payload={})

        self.assertEqual(attempt["dispatch_status"], "blocked")
        self.assertEqual(attempt["blocked_reason"], "backend_adapter_failed")
        self.assertIn("sandbox unavailable", attempt["error"])

    def test_dispatcher_validates_sandbox_attempt_output(self):
        def _adapter(payload):
            return build_sandbox_dispatch_attempt_envelope(
                attempt_id="attempt-1",
                backend_id="sandbox_worker",
                child_run_id=payload["child_run_id"],
                status="completed",
                will_dispatch=True,
                sandbox_ref="sandbox://attempt-1",
                output_ref="artifact://child-1/output",
                audit_ref="trace://attempt-1",
            )

        dispatcher = ChildExecutorDispatcher(
            enabled=True,
            backend_adapters={"sandbox_worker": _adapter},
        )

        attempt = dispatcher.dispatch(
            dispatch_contract=_ready_sandbox_dispatch_contract_with_binding(),
            payload={"parent_run_id": "parent-1", "child_run_id": "child-1"},
        )

        self.assertEqual(attempt["dispatch_status"], "dispatched")
        self.assertEqual(attempt["sandbox_backend_binding_status"], "ready")
        self.assertTrue(attempt["sandbox_backend_binding_ready"])
        self.assertTrue(attempt["will_dispatch"])
        self.assertEqual(attempt["backend_result"]["sandbox_ref"], "sandbox://attempt-1")
        self.assertEqual(attempt["backend_result"]["audit_ref"], "trace://attempt-1")
        handoff = attempt["dispatch_result_handoff"]
        self.assertEqual(handoff["overall_status"], "ready")
        self.assertTrue(handoff["backend_result_schema_valid"])
        self.assertEqual(handoff["sandbox_ref"], "sandbox://attempt-1")
        self.assertEqual(handoff["audit_ref"], "trace://attempt-1")
        self.assertFalse(handoff["production_dispatch_authorized"])
        self.assertEqual(
            handoff["dispatch_result_retry_audit_policy"]["retry_policy_status"],
            "not_required",
        )

    def test_dispatcher_invokes_opt_in_sandbox_execution_seam_once(self):
        backend = SandboxChildExecutorBackend()
        dispatcher = ChildExecutorDispatcher(
            enabled=True,
            backend_adapters={"sandbox_worker": backend},
        )

        attempt = dispatcher.dispatch(
            dispatch_contract=_ready_sandbox_dispatch_contract_with_binding(),
            payload={
                "parent_run_id": "parent-1",
                "child_run_id": "child-1",
                "idempotency_key": "idem-child-1",
            },
        )

        self.assertEqual(attempt["dispatch_status"], "dispatched")
        self.assertTrue(attempt["will_dispatch"])
        self.assertEqual(backend.invocation_count, 1)
        self.assertEqual(backend.executor_invocation_count, 1)
        self.assertEqual(attempt["backend_result"]["status"], "completed")
        self.assertEqual(attempt["backend_result"]["output_ref"], "artifact://child-1/output")
        handoff = attempt["dispatch_result_handoff"]
        self.assertEqual(handoff["overall_status"], "ready")
        self.assertFalse(handoff["parent_merge_performed"])
        self.assertFalse(handoff["retry_scheduled"])
        self.assertFalse(handoff["production_dispatch_authorized"])

    def test_dispatcher_fails_closed_when_sandbox_output_is_malformed(self):
        dispatcher = ChildExecutorDispatcher(
            enabled=True,
            backend_adapters={"sandbox_worker": lambda _payload: {"status": "completed"}},
        )

        attempt = dispatcher.dispatch(
            dispatch_contract=_ready_sandbox_dispatch_contract(),
            payload={"child_run_id": "child-1"},
        )

        self.assertEqual(attempt["dispatch_status"], "blocked")
        self.assertEqual(attempt["blocked_reason"], "sandbox_attempt_invalid")
        self.assertEqual(attempt["error_code"], "sandbox_attempt_missing_fields")
        self.assertIn("attempt_id", attempt["missing_backend_result_fields"])
        handoff = attempt["dispatch_result_handoff"]
        self.assertEqual(handoff["overall_status"], "blocked")
        self.assertEqual(handoff["blocked_reason"], "sandbox_attempt_invalid")
        self.assertIn("backend_result", handoff["missing_sections"])
        self.assertFalse(handoff["merge_authorization"])
        retry_policy = handoff["dispatch_result_retry_audit_policy"]
        self.assertEqual(retry_policy["retry_policy_status"], "terminal")
        self.assertFalse(retry_policy["will_retry"])

    def test_dispatcher_rejects_unsafe_sandbox_payload(self):
        invoked = []
        dispatcher = ChildExecutorDispatcher(
            enabled=True,
            backend_adapters={"sandbox_worker": lambda payload: invoked.append(payload) or {}},
        )

        attempt = dispatcher.dispatch(
            dispatch_contract=_ready_sandbox_dispatch_contract(),
            payload={"child_run_id": "child-1", "handler": object()},
        )

        self.assertEqual(attempt["dispatch_status"], "blocked")
        self.assertEqual(attempt["blocked_reason"], "sandbox_payload_unsafe")
        self.assertEqual(attempt["error_code"], "unsafe_payload")
        self.assertEqual(invoked, [])

    def test_dispatcher_preserves_and_enforces_sandbox_binding_evidence(self):
        invoked = []
        dispatcher = ChildExecutorDispatcher(
            enabled=True,
            backend_adapters={"sandbox_worker": lambda payload: invoked.append(payload) or {}},
        )
        contract = {
            **_ready_sandbox_dispatch_contract(),
            "child_executor_sandbox_backend_binding": {
                "overall_status": "blocked",
                "ready": False,
                "missing_sections": ["dispatcher_backend_adapter"],
            },
        }

        attempt = dispatcher.dispatch(
            dispatch_contract=contract,
            payload={"child_run_id": "child-1"},
        )

        self.assertEqual(attempt["dispatch_status"], "blocked")
        self.assertEqual(attempt["blocked_reason"], "sandbox_backend_binding_not_ready")
        self.assertEqual(attempt["sandbox_backend_binding_status"], "blocked")
        self.assertFalse(attempt["sandbox_backend_binding_ready"])
        self.assertEqual(
            attempt["sandbox_backend_binding_missing_sections"],
            ["dispatcher_backend_adapter"],
        )
        self.assertEqual(invoked, [])

    def test_dispatch_result_handoff_blocks_malformed_result_directly(self):
        handoff = build_child_executor_dispatch_result_handoff_contract(
            dispatch_attempt={
                "dispatch_status": "dispatched",
                "dispatched": True,
                "will_dispatch": True,
                "backend_id": "sandbox_worker",
                "backend_result": {
                    "status": "completed",
                    "child_run_id": "child-1",
                    "output_ref": "",
                },
                "audit": {},
            }
        )

        self.assertEqual(handoff["overall_status"], "blocked")
        self.assertFalse(handoff["ready"])
        self.assertIn("output_ref", handoff["missing_sections"])
        self.assertIn("audit_evidence", handoff["missing_sections"])
        self.assertFalse(handoff["parent_merge_performed"])

    def test_dispatch_result_retry_audit_policy_marks_retryable_failure_ready(self):
        policy = build_child_executor_dispatch_result_retry_audit_policy_contract(
            result_handoff={
                "overall_status": "blocked",
                "ready": False,
                "dispatch_status": "dispatched",
                "backend_result_status": "failed",
                "backend_result_error_code": "sandbox_timeout",
                "retryable": True,
                "audit_evidence_present": True,
                "idempotency_key": "child-dispatch:attempt-1",
                "missing_sections": ["backend_result"],
            }
        )

        self.assertEqual(policy["overall_status"], "ready")
        self.assertEqual(policy["retry_policy_status"], "retryable")
        self.assertTrue(policy["retryable"])
        self.assertTrue(policy["scheduler_required"])
        self.assertFalse(policy["retry_scheduled"])
        self.assertFalse(policy["will_retry"])
        self.assertEqual(policy["retry_reason"], "sandbox_timeout")

    def test_dispatch_result_retry_audit_policy_requires_idempotency_for_retryable_failure(self):
        policy = build_child_executor_dispatch_result_retry_audit_policy_contract(
            result_handoff={
                "overall_status": "blocked",
                "ready": False,
                "dispatch_status": "dispatched",
                "backend_result_status": "failed",
                "backend_result_error_code": "sandbox_timeout",
                "retryable": True,
                "audit_evidence_present": True,
                "idempotency_key": "",
            }
        )

        self.assertEqual(policy["overall_status"], "blocked")
        self.assertEqual(policy["retry_policy_status"], "retryable")
        self.assertIn("idempotency_evidence", policy["missing_sections"])
        self.assertFalse(policy["retry_scheduled"])

    def test_dispatch_result_retry_audit_policy_marks_unsafe_payload_terminal(self):
        policy = build_child_executor_dispatch_result_retry_audit_policy_contract(
            result_handoff={
                "overall_status": "blocked",
                "ready": False,
                "dispatch_status": "blocked",
                "dispatcher_blocked_reason": "sandbox_payload_unsafe",
                "retryable": False,
                "audit_evidence_present": True,
                "idempotency_key": "child-dispatch:attempt-unsafe",
            }
        )

        self.assertEqual(policy["overall_status"], "ready")
        self.assertEqual(policy["retry_policy_status"], "terminal")
        self.assertTrue(policy["terminal"])
        self.assertFalse(policy["will_retry"])


if __name__ == "__main__":
    unittest.main()
