import unittest

from backend.agent_framework.continuation_registry import InMemoryEmbeddedContinuationRegistry
from backend.agent_framework.durable_recovery_loader import (
    DURABLE_RECOVERY_LOADER_CONTRACT_VERSION,
    DurableRecoveryLoader,
    build_durable_recovery_loader_contract,
)
from backend.agent_framework.persistence import InMemoryEmbeddedRunWorkspaceStore
from backend.agent_framework.sdk import EmbeddedAgentRuntimeSDK


class _DurableLoaderWorkspaceStore(InMemoryEmbeddedRunWorkspaceStore):
    def describe_backend(self):
        backend = super().describe_backend()
        backend.update({
            "backend_kind": "sqlalchemy",
            "backend_mode": "strict_sql",
            "durable": True,
            "fallback_active": False,
        })
        return backend


def _tool_executor(_run):
    return {
        "tool_name": "filesystem_write",
        "args": {"path": "case.md"},
        "result": "ok",
    }


def _reviewer(_run):
    return {"status": "approved", "summary": "ok"}


def _build_ready_workspace():
    store = _DurableLoaderWorkspaceStore()
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
            "tool_args": {"path": "case.md"},
            "reason": "approval required",
        },
        tool_executor=_tool_executor,
        reviewer=_reviewer,
    )
    return store, registry, result["run"]["run_id"], executed["approval_request"]["request_id"]


class DurableRecoveryLoaderTests(unittest.TestCase):
    def test_contract_declares_non_executing_registry_loader(self):
        contract = build_durable_recovery_loader_contract()

        self.assertEqual(contract["contract_version"], DURABLE_RECOVERY_LOADER_CONTRACT_VERSION)
        self.assertFalse(contract["executes_recovery"])
        self.assertFalse(contract["deserializes_callables"])
        self.assertIn("run_snapshot", contract["required_state"])
        self.assertIn("continuation_registry_binding", contract["required_gates"])

    def test_loader_reconstructs_ready_registry_backed_candidate(self):
        store, registry, run_id, request_id = _build_ready_workspace()
        loader = DurableRecoveryLoader(workspace_store=store, continuation_registry=registry)

        candidate = loader.load(run_id=run_id, approval_request_id=request_id)

        self.assertEqual(candidate["contract_version"], DURABLE_RECOVERY_LOADER_CONTRACT_VERSION)
        self.assertEqual(candidate["status"], "ready")
        self.assertTrue(candidate["ready"])
        self.assertEqual(candidate["recovery_reason"], "ready_via_registry")
        self.assertFalse(candidate["executes_recovery"])
        self.assertFalse(candidate["deserializes_callables"])
        self.assertEqual(candidate["run_snapshot"]["run_id"], run_id)
        self.assertEqual(candidate["approval_snapshot"]["status"], "pending")
        self.assertEqual(candidate["event_log"]["last_status_kind"], "loop_continuation_registered")
        self.assertTrue(candidate["binding_evidence"]["all_bindings_resolved"])
        self.assertEqual(
            candidate["descriptor_lifecycle"]["contract_version"],
            "phase-ii-continuation-descriptor-lifecycle-governance-v1",
        )
        self.assertTrue(candidate["descriptor_lifecycle"]["governed"])
        self.assertTrue(candidate["descriptor_lifecycle"]["all_ready"])
        self.assertIn("ready", candidate["descriptor_lifecycle"]["states"])
        handoff = candidate["loader_execution_handoff"]
        self.assertEqual(
            handoff["contract_version"],
            "phase-ii-durable-loader-execution-handoff-policy-v1",
        )
        self.assertEqual(handoff["status"], "blocked")
        self.assertEqual(handoff["blocked_reason"], "explicit_handoff_required")
        self.assertFalse(handoff["will_execute"])

    def test_loader_fails_closed_when_run_snapshot_missing(self):
        loader = DurableRecoveryLoader(
            workspace_store=_DurableLoaderWorkspaceStore(),
            continuation_registry=InMemoryEmbeddedContinuationRegistry(),
        )

        candidate = loader.load(run_id="missing-run")

        self.assertEqual(candidate["status"], "blocked")
        self.assertFalse(candidate["ready"])
        self.assertEqual(candidate["recovery_reason"], "run_snapshot_missing")

    def test_loader_fails_closed_when_binding_is_unresolved(self):
        store, _registry, run_id, request_id = _build_ready_workspace()
        loader = DurableRecoveryLoader(
            workspace_store=store,
            continuation_registry=InMemoryEmbeddedContinuationRegistry(),
        )

        candidate = loader.load(run_id=run_id, approval_request_id=request_id)

        self.assertEqual(candidate["status"], "blocked")
        self.assertEqual(candidate["recovery_reason"], "missing_registered_binding")
        self.assertIn("tool_executor.filesystem_write", candidate["missing_binding_ids"])
        self.assertIn("bound", candidate["descriptor_lifecycle"]["states"])

    def test_loader_rejects_unsafe_callable_like_descriptor_payload(self):
        store, registry, run_id, request_id = _build_ready_workspace()
        descriptor = store.get_tool_continuation_descriptor(request_id)
        descriptor["tool_executor"] = "serialized callable should not be loaded"
        store.save_tool_continuation_descriptor(request_id, descriptor)
        loader = DurableRecoveryLoader(workspace_store=store, continuation_registry=registry)

        candidate = loader.load(run_id=run_id, approval_request_id=request_id)

        self.assertEqual(candidate["status"], "blocked")
        self.assertEqual(candidate["recovery_reason"], "descriptor_corrupted")
        self.assertIn("tool_executor", candidate["unsafe_descriptor_keys"])
        self.assertIn("unsafe", candidate["descriptor_lifecycle"]["states"])

    def test_loader_fails_closed_when_approval_state_is_stale(self):
        store, registry, run_id, request_id = _build_ready_workspace()
        approval = store.get_approval_snapshot(request_id)
        approval["status"] = "denied"
        store.save_approval_snapshot(approval)
        loader = DurableRecoveryLoader(workspace_store=store, continuation_registry=registry)

        candidate = loader.load(run_id=run_id, approval_request_id=request_id)

        self.assertEqual(candidate["status"], "blocked")
        self.assertEqual(candidate["recovery_reason"], "denied")
        self.assertIn("stale", candidate["descriptor_lifecycle"]["states"])

    def test_sdk_probe_exposes_durable_recovery_loader_candidate(self):
        store, registry, run_id, _request_id = _build_ready_workspace()
        reader = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)

        probe = reader.probe_run_recovery(run_id)

        loader_candidate = probe["durable_recovery_loader"]
        self.assertEqual(loader_candidate["contract_version"], DURABLE_RECOVERY_LOADER_CONTRACT_VERSION)
        self.assertEqual(loader_candidate["status"], "ready")
        self.assertTrue(loader_candidate["ready"])
        self.assertEqual(loader_candidate["recovery_reason"], "ready_via_registry")

    def test_sdk_recovery_entrypoint_fails_closed_for_unsafe_descriptor(self):
        store, registry, _run_id, request_id = _build_ready_workspace()
        descriptor = store.get_tool_continuation_descriptor(request_id)
        descriptor["handler"] = "unsafe serialized handler"
        store.save_tool_continuation_descriptor(request_id, descriptor)
        reader = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)

        with self.assertRaisesRegex(ValueError, "descriptor_corrupted"):
            reader.submit_approval(request_id, "approved")

        failed_event = next(
            event
            for event in reader.stream_events(store.get_approval_snapshot(request_id)["run_id"])
            if event["status_kind"] == "recovery_failed_closed"
        )
        self.assertEqual(failed_event["recovery"]["recovery_reason"], "descriptor_corrupted")
        self.assertEqual(failed_event["recovery_operation"]["operation_status"], "blocked")


if __name__ == "__main__":
    unittest.main()
