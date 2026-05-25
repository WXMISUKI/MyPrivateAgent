import unittest

from backend.agent_framework.continuation_registry import InMemoryEmbeddedContinuationRegistry
from backend.agent_framework.persistence import InMemoryEmbeddedRunWorkspaceStore
from backend.agent_framework.sdk import EmbeddedAgentRuntimeSDK
from backend.agent_framework.worker_ownership import (
    InMemoryRuntimeWorkerOwnershipStore,
    WORKER_OWNERSHIP_REASON_STALE_FENCING_TOKEN,
)


class _DurableTestWorkspaceStore(InMemoryEmbeddedRunWorkspaceStore):
    def describe_backend(self):
        backend = super().describe_backend()
        return {
            **backend,
            "backend_kind": "test_durable",
            "backend_mode": "strict_test",
            "durable": True,
            "fallback_active": False,
            "fallback_reason": "",
            "last_error": "",
        }


class SdkWorkerOwnershipGateTests(unittest.TestCase):
    def _prepare_tool_recovery_case(self):
        store = _DurableTestWorkspaceStore()
        registry = InMemoryEmbeddedContinuationRegistry()
        ownership_store = InMemoryRuntimeWorkerOwnershipStore()
        tool_calls = []

        def _tool_executor(_run):
            tool_calls.append("called")
            return {
                "tool_name": "filesystem_write",
                "args": {"path": "case.md"},
                "result": "写入成功",
            }

        registry.register("tool_executor.filesystem_write", _tool_executor)
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
                "reason": "高风险写文件工具需要人工审批",
            },
            tool_executor=_tool_executor,
        )
        return store, registry, ownership_store, tool_calls, result, executed

    def test_submit_approval_recovery_records_valid_worker_ownership(self):
        store, registry, ownership_store, tool_calls, result, executed = self._prepare_tool_recovery_case()
        run_id = result["run"]["run_id"]
        request_id = executed["approval_request"]["request_id"]
        ownership = ownership_store.claim_run(run_id, "worker-a", lease_ttl_seconds=30)
        descriptor = store.get_tool_continuation_descriptor(request_id)
        descriptor["worker_ownership"] = dict(ownership)
        store.save_tool_continuation_descriptor(request_id, descriptor)

        reader = EmbeddedAgentRuntimeSDK(
            workspace_store=store,
            continuation_registry=registry,
            worker_ownership_store=ownership_store,
        )
        approved = reader.submit_approval(request_id, "approved")

        self.assertEqual(tool_calls, ["called"])
        operation = approved["run"]["metadata"]["latest_recovery_operation"]
        self.assertEqual(operation["operation_status"], "recovered")
        self.assertTrue(operation["worker_ownership"]["implemented"])
        self.assertTrue(operation["worker_ownership"]["owned"])
        self.assertEqual(operation["worker_ownership"]["lease_status"], "validated")
        self.assertEqual(operation["worker_ownership"]["worker_id"], "worker-a")

    def test_submit_approval_recovery_fails_closed_for_stale_fencing_token(self):
        store, registry, ownership_store, tool_calls, result, executed = self._prepare_tool_recovery_case()
        run_id = result["run"]["run_id"]
        request_id = executed["approval_request"]["request_id"]
        ownership = ownership_store.claim_run(run_id, "worker-a", lease_ttl_seconds=30)
        descriptor = store.get_tool_continuation_descriptor(request_id)
        descriptor["worker_ownership"] = {
            **ownership,
            "fencing_token": ownership["fencing_token"] + 100,
        }
        store.save_tool_continuation_descriptor(request_id, descriptor)

        reader = EmbeddedAgentRuntimeSDK(
            workspace_store=store,
            continuation_registry=registry,
            worker_ownership_store=ownership_store,
        )
        with self.assertRaisesRegex(ValueError, WORKER_OWNERSHIP_REASON_STALE_FENCING_TOKEN):
            reader.submit_approval(request_id, "approved")

        self.assertEqual(tool_calls, [])
        events = list(reader.stream_events(run_id))
        failed_event = next(event for event in events if event["status_kind"] == "recovery_failed_closed")
        operation = failed_event["recovery_operation"]
        self.assertEqual(operation["operation_status"], "blocked")
        self.assertEqual(operation["recovery_reason"], WORKER_OWNERSHIP_REASON_STALE_FENCING_TOKEN)
        self.assertTrue(operation["worker_ownership"]["implemented"])
        self.assertFalse(operation["worker_ownership"]["owned"])
        self.assertEqual(
            operation["worker_ownership"]["reason"],
            WORKER_OWNERSHIP_REASON_STALE_FENCING_TOKEN,
        )

    def test_recovery_without_ownership_evidence_preserves_default_boundary(self):
        store, registry, _ownership_store, tool_calls, _result, executed = self._prepare_tool_recovery_case()
        request_id = executed["approval_request"]["request_id"]

        reader = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)
        approved = reader.submit_approval(request_id, "approved")

        self.assertEqual(tool_calls, ["called"])
        operation = approved["run"]["metadata"]["latest_recovery_operation"]
        self.assertFalse(operation["worker_ownership"]["implemented"])


if __name__ == "__main__":
    unittest.main()
