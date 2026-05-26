import unittest

from backend.agent_framework.child_executor_backends import (
    build_child_executor_backend_registry_contract,
    build_child_executor_sandbox_worker_backend_entry,
)
from backend.agent_framework.child_executor_sandbox_worker_backend import (
    build_child_executor_sandbox_backend_binding_contract,
    build_sandbox_dispatch_attempt_envelope,
    build_sandbox_worker_backend_adapter_contract,
    validate_sandbox_dispatch_attempt,
)
from backend.agent_framework.sdk import build_child_executor_dispatch_contract


def _ready_adapter_contract():
    return build_sandbox_worker_backend_adapter_contract(
        backend_id="sandbox_worker",
        input_contract={"required_fields": ["child_run_id"]},
        output_contract={"required_fields": ["output_ref", "audit_ref"]},
        resource_limits={"cpu_seconds": 30, "memory_mb": 512, "timeout_seconds": 60},
        isolation_guards={
            "process_or_worker_isolation": True,
            "environment_allowlist": ["PYTHONPATH"],
            "workspace_boundary": "run_workspace",
            "network_policy": "disabled_by_default",
        },
        audit_hooks={"record_dispatch": True},
        idempotency={"idempotency_key_required": True},
    )


def _ready_gate_for_backend(backend_evidence):
    return {
        "allowed": True,
        "gate_status": "allowed",
        "preflight": {"worker_runtime_backend": backend_evidence["backend_id"]},
        "child_executor_execution_prerequisites": {
            "ready": True,
            "overall_status": "ready",
            "missing_requirements": [],
            "requirements": [
                {
                    "requirement": "worker_backend_dispatch_ready",
                    "status": "ready",
                    "evidence": backend_evidence,
                },
                {
                    "requirement": "explicit_executor_binding_opt_in",
                    "status": "ready",
                    "evidence": {
                        "contract_version": "phase-ii-child-executor-explicit-binding-v1",
                        "binding_status": "ready",
                        "ready": True,
                        "binding_source": "test.explicit_opt_in",
                        "selected_backend": backend_evidence["backend_id"],
                        "backend_id": backend_evidence["backend_id"],
                        "adapter_kind": backend_evidence.get("adapter_kind", ""),
                        "missing_requirements": [],
                        "blockers": [],
                        "will_execute": False,
                        "will_dispatch": False,
                    },
                }
            ],
            "explicit_executor_binding": {
                "contract_version": "phase-ii-child-executor-explicit-binding-v1",
                "binding_status": "ready",
                "ready": True,
                "binding_source": "test.explicit_opt_in",
                "selected_backend": backend_evidence["backend_id"],
                "backend_id": backend_evidence["backend_id"],
                "adapter_kind": backend_evidence.get("adapter_kind", ""),
            },
        },
    }


class ChildExecutorSandboxWorkerBackendTests(unittest.TestCase):
    def test_adapter_contract_reports_ready_when_all_guards_are_present(self):
        contract = _ready_adapter_contract()

        self.assertTrue(contract["adapter_contract_ready"])
        self.assertTrue(contract["sandbox_guard_ready"])
        self.assertTrue(contract["audit_ready"])
        self.assertTrue(contract["idempotency_ready"])
        self.assertEqual(contract["missing_guards"], [])

    def test_backend_registry_keeps_incomplete_sandbox_backend_not_ready(self):
        incomplete = build_sandbox_worker_backend_adapter_contract(
            backend_id="sandbox_worker",
            input_contract={"required_fields": ["child_run_id"]},
            output_contract={"required_fields": ["output_ref"]},
        )
        entry = build_child_executor_sandbox_worker_backend_entry(
            backend_id="sandbox_worker",
            label="Sandbox worker",
            adapter_contract=incomplete,
        )

        registry = build_child_executor_backend_registry_contract(extra_backends=[entry])
        backend = registry["backends_by_id"]["sandbox_worker"]

        self.assertFalse(backend["dispatch_ready"])
        self.assertFalse(backend["sandbox_guard_ready"])
        self.assertIn("sandbox_guard_not_ready", backend["blockers"])
        self.assertIn("sandbox_guard_missing:isolation", backend["missing_guard_blockers"])

    def test_backend_registry_can_model_dispatch_ready_sandbox_backend(self):
        entry = build_child_executor_sandbox_worker_backend_entry(
            backend_id="sandbox_worker",
            label="Sandbox worker",
            adapter_contract=_ready_adapter_contract(),
        )

        registry = build_child_executor_backend_registry_contract(extra_backends=[entry])
        backend = registry["backends_by_id"]["sandbox_worker"]

        self.assertTrue(backend["dispatch_ready"])
        self.assertEqual(backend["adapter_kind"], "sandbox_worker")
        self.assertTrue(backend["adapter_contract_ready"])
        self.assertEqual(registry["ready_backend_count"], 1)

    def test_sandbox_backend_binding_blocks_default_missing_explicit_binding(self):
        entry = build_child_executor_sandbox_worker_backend_entry(
            backend_id="sandbox_worker",
            label="Sandbox worker",
            adapter_contract=_ready_adapter_contract(),
        )

        binding = build_child_executor_sandbox_backend_binding_contract(
            backend_id="sandbox_worker",
            backend_registry_entry=entry,
            adapter_contract=entry["adapter_contract"],
            dispatcher_backend_adapters={"sandbox_worker": lambda _payload: {}},
        )

        self.assertEqual(binding["overall_status"], "blocked")
        self.assertFalse(binding["ready"])
        self.assertIn("explicit_binding", binding["missing_sections"])
        self.assertFalse(binding["will_dispatch"])

    def test_sandbox_backend_binding_blocks_ready_adapter_without_callable_dispatcher_adapter(self):
        entry = build_child_executor_sandbox_worker_backend_entry(
            backend_id="sandbox_worker",
            label="Sandbox worker",
            adapter_contract=_ready_adapter_contract(),
        )

        binding = build_child_executor_sandbox_backend_binding_contract(
            backend_id="sandbox_worker",
            backend_registry_entry=entry,
            adapter_contract=entry["adapter_contract"],
            dispatcher_backend_adapters={},
            explicit_binding={
                "ready": True,
                "binding_status": "ready",
                "binding_source": "test.explicit_opt_in",
            },
        )

        self.assertEqual(binding["overall_status"], "blocked")
        self.assertFalse(binding["dispatcher_binding_ready"])
        self.assertIn("dispatcher_backend_adapter", binding["missing_sections"])
        self.assertTrue(binding["attempt_envelope_supported"])

    def test_sandbox_backend_binding_ready_for_explicit_callable_binding(self):
        entry = build_child_executor_sandbox_worker_backend_entry(
            backend_id="sandbox_worker",
            label="Sandbox worker",
            adapter_contract=_ready_adapter_contract(),
        )

        binding = build_child_executor_sandbox_backend_binding_contract(
            backend_id="sandbox_worker",
            backend_registry_entry=entry,
            adapter_contract=entry["adapter_contract"],
            dispatcher_backend_adapters={"sandbox_worker": lambda _payload: {}},
            explicit_binding={
                "ready": True,
                "binding_status": "ready",
                "binding_source": "test.explicit_opt_in",
            },
        )

        self.assertEqual(binding["overall_status"], "ready")
        self.assertTrue(binding["ready"])
        self.assertTrue(binding["dispatcher_binding_ready"])
        self.assertTrue(binding["attempt_envelope_supported"])
        self.assertTrue(binding["audit_idempotency_ready"])
        self.assertFalse(binding["will_dispatch"])

    def test_dispatch_contract_blocks_sandbox_backend_with_missing_guard_evidence(self):
        backend_evidence = {
            "backend_id": "sandbox_worker",
            "status": "ready",
            "dispatch_ready": True,
            "dispatch_mode": "sandbox_worker",
            "adapter_kind": "sandbox_worker",
            "adapter_contract_ready": True,
            "sandbox_guard_ready": False,
            "audit_ready": True,
            "idempotency_ready": True,
            "missing_guard_blockers": ["sandbox_guard_missing:network_policy"],
        }

        contract = build_child_executor_dispatch_contract(
            gate=_ready_gate_for_backend(backend_evidence),
            backend_registry=build_child_executor_backend_registry_contract(extra_backends=[backend_evidence]),
        )

        self.assertEqual(contract["overall_status"], "blocked")
        self.assertFalse(contract["dispatch_ready"])
        self.assertTrue(contract["sandbox_backend_selected"])
        self.assertFalse(contract["sandbox_backend_ready"])
        self.assertIn("sandbox_guard_ready", contract["blockers"])
        self.assertIn("sandbox_backend_binding_ready", contract["blockers"])
        self.assertIn("sandbox_guard_missing:network_policy", contract["blockers"])

    def test_dispatch_contract_nests_attempt_handoff_evidence(self):
        entry = build_child_executor_sandbox_worker_backend_entry(
            backend_id="sandbox_worker",
            label="Sandbox worker",
            adapter_contract=_ready_adapter_contract(),
        )

        contract = build_child_executor_dispatch_contract(
            gate=_ready_gate_for_backend(entry),
            backend_registry=build_child_executor_backend_registry_contract(extra_backends=[entry]),
            dispatcher_backend_adapters={"sandbox_worker": lambda _payload: {}},
        )

        handoff = contract["child_executor_dispatch_attempt_handoff"]
        binding = contract["child_executor_sandbox_backend_binding"]
        self.assertEqual(contract["overall_status"], "ready")
        self.assertEqual(binding["overall_status"], "ready")
        self.assertTrue(contract["sandbox_backend_binding_ready"])
        self.assertEqual(handoff["overall_status"], "ready")
        self.assertTrue(handoff["attempt_envelope_supported"])
        self.assertTrue(handoff["attempt_validation_ready"])
        self.assertFalse(handoff["will_dispatch"])

    def test_validate_sandbox_dispatch_attempt_requires_compact_envelope(self):
        invalid = validate_sandbox_dispatch_attempt({"status": "completed"})

        self.assertFalse(invalid["valid"])
        self.assertEqual(invalid["error_code"], "sandbox_attempt_missing_fields")
        self.assertIn("attempt_id", invalid["missing_fields"])

        valid = validate_sandbox_dispatch_attempt(
            build_sandbox_dispatch_attempt_envelope(
                attempt_id="attempt-1",
                backend_id="sandbox_worker",
                child_run_id="child-1",
                status="completed",
                will_dispatch=True,
                sandbox_ref="sandbox://attempt-1",
                output_ref="artifact://child-1/output",
                audit_ref="trace://attempt-1",
            )
        )

        self.assertTrue(valid["valid"])
        self.assertEqual(valid["attempt"]["output_ref"], "artifact://child-1/output")


if __name__ == "__main__":
    unittest.main()
