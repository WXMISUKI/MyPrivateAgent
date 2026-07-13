import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import backend.agent_framework.adapters as adapters_module
from backend.database import Base
from backend.agent_framework.adapters import SQLAlchemyEmbeddedRunWorkspaceStore
from backend.agent_framework.persistence import (
    InMemoryEmbeddedRunWorkspaceStore,
    build_durable_workspace_production_recovery_gate_contract,
    build_embedded_sdk_production_recovery_authorization_contract,
    build_embedded_sdk_persistence_interface,
)


class EmbeddedWorkspaceStoreTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.store = SQLAlchemyEmbeddedRunWorkspaceStore(TestingSessionLocal)

    def tearDown(self):
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def test_store_can_persist_run_snapshot_events_approval_and_continuations(self):
        self.store.save_run_snapshot({
            "run_id": "run-demo-1",
            "conversation_id": 42,
            "parent_run_id": "root-run",
            "run_kind": "chat",
            "state": "waiting_approval",
            "metadata": {"agent_name": "fraud_assistant"},
        })
        self.store.save_events("run-demo-1", [{"status_kind": "run_created"}])
        self.store.save_approval_snapshot({
            "request_id": "approval-demo-1",
            "run_id": "run-demo-1",
            "status": "pending",
        })
        self.store.save_tool_continuation_descriptor("approval-demo-1", {
            "status": "pending",
            "request_id": "approval-demo-1",
        })
        self.store.save_loop_continuation_descriptor("run-demo-1", {
            "status": "pending",
            "request_id": "approval-demo-1",
            "resume_mode": "observing_to_done",
        })

        self.assertEqual(self.store.get_run_snapshot("run-demo-1")["run_id"], "run-demo-1")
        self.assertEqual(self.store.get_events("run-demo-1")[0]["status_kind"], "run_created")
        self.assertEqual(self.store.get_approval_snapshot("approval-demo-1")["status"], "pending")
        self.assertEqual(self.store.get_tool_continuation_descriptor("approval-demo-1")["status"], "pending")
        self.assertEqual(self.store.get_loop_continuation_descriptor("run-demo-1")["resume_mode"], "observing_to_done")

    def test_store_can_delete_continuation_descriptors(self):
        self.store.save_tool_continuation_descriptor("approval-demo-1", {"status": "pending"})
        self.store.save_loop_continuation_descriptor("run-demo-1", {"status": "pending"})

        self.store.delete_tool_continuation_descriptor("approval-demo-1")
        self.store.delete_loop_continuation_descriptor("run-demo-1")

        self.assertIsNone(self.store.get_tool_continuation_descriptor("approval-demo-1"))
        self.assertIsNone(self.store.get_loop_continuation_descriptor("run-demo-1"))

    def test_store_reports_sqlalchemy_backend_without_fallback_when_healthy(self):
        description = self.store.describe_backend()

        self.assertEqual(description["backend_kind"], "sqlalchemy")
        self.assertTrue(description["durable"])
        self.assertEqual(description["backend_mode"], "prefer_sql_with_fallback")
        self.assertTrue(description["operation_fallback_allowed"])
        self.assertFalse(description["fallback_active"])
        self.assertEqual(description["fallback_reason"], "")
        self.assertEqual(description["last_error"], "")
        state_contract = description["state_contract"]
        self.assertEqual(
            state_contract["contract_version"],
            "phase-ii-durable-workspace-state-contract-v1",
        )
        self.assertIn("run_snapshot", state_contract["durable_state_kinds"])
        self.assertIn("approval_snapshot", state_contract["durable_state_kinds"])
        self.assertIn("tool_continuation_descriptor", state_contract["durable_state_kinds"])
        self.assertIn("loop_continuation_descriptor", state_contract["durable_state_kinds"])
        self.assertIn("artifact_ref", state_contract["durable_state_kinds"])
        self.assertIn("child_executor_output", state_contract["durable_state_kinds"])
        self.assertIn("executable_continuation_callable", state_contract["runtime_only_state_kinds"])
        self.assertIn("python_function_binding", state_contract["runtime_only_state_kinds"])

    def test_in_memory_store_reports_same_state_contract_without_durable_capability(self):
        description = InMemoryEmbeddedRunWorkspaceStore().describe_backend()

        self.assertEqual(description["backend_kind"], "in_memory")
        self.assertFalse(description["durable"])
        state_contract = description["state_contract"]
        self.assertEqual(
            state_contract["contract_version"],
            "phase-ii-durable-workspace-state-contract-v1",
        )
        self.assertIn("run_snapshot", state_contract["durable_state_kinds"])
        self.assertIn("executable_continuation_callable", state_contract["runtime_only_state_kinds"])

    def test_persistence_interface_derives_memory_preview_posture(self):
        description = InMemoryEmbeddedRunWorkspaceStore().describe_backend()

        interface = build_embedded_sdk_persistence_interface(description)

        self.assertEqual(
            interface["contract_version"],
            "phase-ii-embedded-sdk-persistence-interface-v1",
        )
        self.assertEqual(interface["persistence_posture"], "memory_preview")
        self.assertFalse(interface["durable"])
        self.assertFalse(interface["cross_process_candidate"])
        self.assertEqual(interface["cross_process_block_reason"], "workspace_backend_not_durable")
        self.assertEqual(interface["production_recovery_gate"]["overall_status"], "blocked")
        self.assertEqual(interface["production_recovery_authorization"]["overall_status"], "blocked")
        self.assertFalse(interface["production_recovery_authorization"]["will_execute"])
        self.assertIn(
            "authorization_request_source",
            interface["production_recovery_authorization"]["missing_sections"],
        )
        self.assertFalse(interface["production_recovery_gate"]["production_default_enabled"])
        self.assertIn(
            "durable_workspace_backend",
            interface["production_recovery_gate"]["missing_sections"],
        )
        self.assertEqual(
            interface["state_contract"]["contract_version"],
            "phase-ii-durable-workspace-state-contract-v1",
        )

    def test_persistence_interface_derives_durable_ready_posture(self):
        description = self.store.describe_backend()

        interface = build_embedded_sdk_persistence_interface(description)

        self.assertEqual(interface["persistence_posture"], "durable_ready")
        self.assertEqual(interface["workspace_backend_kind"], "sqlalchemy")
        self.assertTrue(interface["durable"])
        self.assertFalse(interface["fallback_active"])
        self.assertTrue(interface["cross_process_candidate"])
        self.assertEqual(interface["cross_process_block_reason"], "")
        self.assertEqual(
            interface["production_recovery_gate"]["contract_version"],
            "phase-ii-durable-workspace-production-recovery-gate-v1",
        )
        self.assertEqual(interface["production_recovery_gate"]["overall_status"], "blocked")
        self.assertNotIn(
            "descriptor_lifecycle_governance",
            interface["production_recovery_gate"]["missing_sections"],
        )
        self.assertNotIn(
            "loader_execution_handoff_policy",
            interface["production_recovery_gate"]["missing_sections"],
        )
        self.assertNotIn(
            "recovery_audit_operation_history",
            interface["production_recovery_gate"]["missing_sections"],
        )
        self.assertNotIn(
            "registry_binding_resolution",
            interface["production_recovery_gate"]["missing_sections"],
        )
        self.assertNotIn(
            "checkpoint_resume_cursor_gate",
            interface["production_recovery_gate"]["missing_sections"],
        )
        self.assertEqual(
            interface["production_recovery_authorization"]["contract_version"],
            "phase-ii-embedded-sdk-production-recovery-authorization-v1",
        )
        self.assertEqual(interface["production_recovery_authorization"]["overall_status"], "blocked")
        self.assertFalse(interface["production_recovery_authorization"]["authorization_ready"])
        self.assertFalse(interface["production_recovery_authorization"]["will_execute"])
        self.assertIn(
            "authorization_request_source",
            interface["production_recovery_authorization"]["missing_sections"],
        )
        self.assertIn("tool_continuation_descriptor", interface["state_contract"]["durable_state_kinds"])

    def test_persistence_interface_derives_durable_degraded_posture(self):
        description = {
            "backend_kind": "sqlalchemy",
            "backend_mode": "prefer_sql_with_fallback",
            "durable": True,
            "fallback_active": True,
            "fallback_reason": "save_run_snapshot",
            "last_error": "db unavailable",
            "state_contract": InMemoryEmbeddedRunWorkspaceStore().describe_backend()["state_contract"],
        }

        interface = build_embedded_sdk_persistence_interface(description)

        self.assertEqual(interface["persistence_posture"], "durable_degraded")
        self.assertTrue(interface["durable"])
        self.assertTrue(interface["fallback_active"])
        self.assertEqual(interface["fallback_reason"], "save_run_snapshot")
        self.assertFalse(interface["cross_process_candidate"])
        self.assertEqual(interface["cross_process_block_reason"], "workspace_backend_fallback_active")
        self.assertEqual(interface["production_recovery_gate"]["overall_status"], "blocked")
        self.assertIn(
            "durable_workspace_backend",
            interface["production_recovery_gate"]["missing_sections"],
        )

    def test_production_recovery_gate_can_be_ready_only_with_all_sections_ready(self):
        description = self.store.describe_backend()

        gate = build_durable_workspace_production_recovery_gate_contract(
            backend_description=description,
            descriptor_lifecycle_governed=True,
            registry_binding_policy_ready=True,
            checkpoint_resume_cursor_gate_ready=True,
            worker_ownership_gate_ready=True,
            worker_ownership_production_gate={
                "contract_version": "phase-ii-worker-ownership-production-gate-v1",
                "overall_status": "ready",
                "production_default_enabled": True,
                "missing_sections": [],
                "next_allowed_action": "consider_explicit_production_default_enablement",
            },
            recovery_audit_ready=True,
            rollout_checklist_ready=True,
            loader_execution_handoff_policy_ready=True,
        )

        self.assertEqual(gate["contract_version"], "phase-ii-durable-workspace-production-recovery-gate-v1")
        self.assertEqual(gate["overall_status"], "ready")
        self.assertTrue(gate["ready"])
        self.assertEqual(gate["missing_sections"], [])
        self.assertFalse(gate["production_default_enabled"])

    def test_production_recovery_authorization_defaults_to_blocked_without_caller_owned_source(self):
        description = self.store.describe_backend()
        gate = build_durable_workspace_production_recovery_gate_contract(
            backend_description=description,
            descriptor_lifecycle_governed=True,
            registry_binding_policy_ready=True,
            checkpoint_resume_cursor_gate_ready=True,
            worker_ownership_gate_ready=True,
            worker_ownership_production_gate={
                "contract_version": "phase-ii-worker-ownership-production-gate-v1",
                "overall_status": "ready",
                "production_default_enabled": True,
                "missing_sections": [],
                "next_allowed_action": "consider_explicit_production_default_enablement",
            },
            recovery_audit_ready=True,
            rollout_checklist_ready=True,
            loader_execution_handoff_policy_ready=True,
        )

        authorization = build_embedded_sdk_production_recovery_authorization_contract(
            backend_description=description,
            production_recovery_gate=gate,
        )

        self.assertEqual(
            authorization["contract_version"],
            "phase-ii-embedded-sdk-production-recovery-authorization-v1",
        )
        self.assertEqual(authorization["overall_status"], "blocked")
        self.assertFalse(authorization["authorization_ready"])
        self.assertFalse(authorization["will_execute"])
        self.assertIn("authorization_request_source", authorization["missing_sections"])
        self.assertIn("worker_ownership_enablement_input", authorization["missing_sections"])

    def test_production_recovery_authorization_can_be_ready_without_executing_recovery(self):
        description = self.store.describe_backend()
        gate = build_durable_workspace_production_recovery_gate_contract(
            backend_description=description,
            descriptor_lifecycle_governed=True,
            registry_binding_policy_ready=True,
            checkpoint_resume_cursor_gate_ready=True,
            worker_ownership_gate_ready=True,
            worker_ownership_production_gate={
                "contract_version": "phase-ii-worker-ownership-production-gate-v1",
                "overall_status": "ready",
                "production_default_enabled": True,
                "missing_sections": [],
                "next_allowed_action": "consider_explicit_production_default_enablement",
            },
            recovery_audit_ready=True,
            rollout_checklist_ready=True,
            loader_execution_handoff_policy_ready=True,
        )

        authorization = build_embedded_sdk_production_recovery_authorization_contract(
            backend_description=description,
            production_recovery_gate=gate,
            worker_ownership_production_enablement_runtime_config_consumer={
                "contract_version": (
                    "phase-ii-worker-ownership-production-enablement-runtime-config-consumer-v1"
                ),
                "overall_status": "ready",
                "source_kind": "runtime_config",
                "config_id": "recovery-auth-1",
                "approved_by": "ops@example.com",
                "approved_at": "2026-07-13T10:00:00Z",
                "target_store_mode": "strict_sql",
                "target_backend": "postgres",
                "lock_adapter_kind": "postgres_advisory_lock",
                "missing_sections": [],
                "enablement_input_source": {
                    "overall_status": "ready",
                    "input_source_kind": "config",
                    "request_id": "recovery-auth-1",
                    "requested_by": "ops@example.com",
                    "requested_at": "2026-07-13T10:00:00Z",
                    "target_store_mode": "strict_sql",
                    "missing_sections": [],
                },
            },
        )

        self.assertEqual(authorization["overall_status"], "ready")
        self.assertTrue(authorization["authorization_ready"])
        self.assertEqual(authorization["authorization_source"], "runtime_config")
        self.assertEqual(authorization["missing_sections"], [])
        self.assertFalse(authorization["will_execute"])

    def test_store_marks_fallback_when_session_factory_fails(self):
        def _broken_session_factory():
            raise RuntimeError("db unavailable")

        broken_store = SQLAlchemyEmbeddedRunWorkspaceStore(_broken_session_factory)

        broken_store.save_run_snapshot({
            "run_id": "run-broken-1",
            "conversation_id": 1,
            "metadata": {"agent_name": "fallback"},
        })

        description = broken_store.describe_backend()
        self.assertEqual(description["backend_kind"], "sqlalchemy")
        self.assertTrue(description["durable"])
        self.assertTrue(description["fallback_active"])
        self.assertEqual(description["fallback_reason"], "save_run_snapshot")
        self.assertIn("db unavailable", description["last_error"])
        self.assertEqual(broken_store.get_run_snapshot("run-broken-1")["run_id"], "run-broken-1")

    def test_store_can_run_in_strict_sql_mode_without_operation_fallback(self):
        strict_store = SQLAlchemyEmbeddedRunWorkspaceStore(
            self.store._session_factory,
            allow_operation_fallback=False,
            backend_mode="strict_sql",
        )

        description = strict_store.describe_backend()
        self.assertEqual(description["backend_mode"], "strict_sql")
        self.assertFalse(description["operation_fallback_allowed"])

    def test_store_raises_in_strict_sql_mode_when_session_factory_fails(self):
        def _broken_session_factory():
            raise RuntimeError("db unavailable")

        strict_store = SQLAlchemyEmbeddedRunWorkspaceStore(
            _broken_session_factory,
            allow_operation_fallback=False,
            backend_mode="strict_sql",
        )

        with self.assertRaisesRegex(RuntimeError, "strict_sql failure during save_run_snapshot"):
            strict_store.save_run_snapshot({
                "run_id": "run-strict-1",
                "metadata": {"agent_name": "strict"},
            })

    def test_get_embedded_workspace_store_returns_in_memory_store_in_memory_only_mode(self):
        with patch.object(adapters_module, "_embedded_workspace_store", None):
            with patch.object(adapters_module, "EMBEDDED_WORKSPACE_STORE_MODE", "memory_only"):
                store = adapters_module.get_embedded_workspace_store()

        self.assertEqual(store.describe_backend()["backend_kind"], "in_memory")

    def test_get_embedded_workspace_store_raises_when_strict_sql_backend_cannot_initialize(self):
        with patch.object(adapters_module, "_embedded_workspace_store", None):
            with patch.object(adapters_module, "EMBEDDED_WORKSPACE_STORE_MODE", "strict_sql"):
                with patch.object(adapters_module, "DB_MODE", "sqlite"):
                    with patch.object(adapters_module, "SQLAlchemyEmbeddedRunWorkspaceStore", side_effect=RuntimeError("boom")):
                        with self.assertRaisesRegex(RuntimeError, "strict_sql mode requires a working SQL backend"):
                            adapters_module.get_embedded_workspace_store()

    def test_set_embedded_workspace_store_mode_resets_singleton(self):
        with patch.object(adapters_module, "_embedded_workspace_store", object()):
            mode = adapters_module.set_embedded_workspace_store_mode("memory_only")
            self.assertEqual(mode, "memory_only")
            self.assertIsNone(adapters_module._embedded_workspace_store)


if __name__ == "__main__":
    unittest.main()
