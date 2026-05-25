import unittest

from backend.agent_framework.child_executor_dispatcher import (
    CHILD_EXECUTOR_DISPATCHER_CONTRACT_VERSION,
    ChildExecutorDispatcher,
    build_child_executor_dispatcher_contract,
)
from backend.agent_framework.child_executor_sandbox_worker_backend import (
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
            dispatch_contract=_ready_sandbox_dispatch_contract(),
            payload={"parent_run_id": "parent-1", "child_run_id": "child-1"},
        )

        self.assertEqual(attempt["dispatch_status"], "dispatched")
        self.assertTrue(attempt["will_dispatch"])
        self.assertEqual(attempt["backend_result"]["sandbox_ref"], "sandbox://attempt-1")
        self.assertEqual(attempt["backend_result"]["audit_ref"], "trace://attempt-1")

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


if __name__ == "__main__":
    unittest.main()
