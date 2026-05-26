import unittest
from unittest.mock import Mock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import backend.agent_framework.adapters as adapters_module
import backend.agent_framework.continuation_registry as continuation_registry_module
import backend.agent_framework.runtime_dependencies as runtime_dependencies_module
from backend.agent_framework.adapters import InMemoryArtifactStore
from backend.agent_framework.adapters import SQLAlchemyEmbeddedRunWorkspaceStore
from backend.agent_framework.continuation_registry import InMemoryEmbeddedContinuationRegistry
from backend.agent_framework.persistence import InMemoryEmbeddedRunWorkspaceStore
from backend.agent_framework.child_executor_backends import (
    build_child_executor_backend_registry_contract,
    resolve_child_executor_backend,
)
from backend.agent_framework.runtime_dependencies import (
    EmbeddedRuntimeDependencies,
    EmbeddedRuntimeFactory,
    create_default_embedded_runtime_sdk,
    get_default_embedded_runtime_factory,
)
from backend.agent_framework.sdk import (
    EmbeddedAgentRuntimeSDK,
    build_child_executor_dispatch_contract,
    build_embedded_sdk_contract,
    validate_embedded_sdk_event_payloads,
)
from backend.agent_framework.tools import ToolSpec
from backend.agent_framework.worker_ownership import InMemoryRuntimeWorkerOwnershipStore
from backend.services.runtime_surface_builders import RuntimeRecoveryContractBuilder
from backend.database import Base
from backend.harness.tool_registry import ToolRegistry
from backend.services.sdk_approval_timeline_service import SdkApprovalLifecycleTimelineService
from backend.services.tool_runtime_service import ToolRuntimeService


class _DurableTestWorkspaceStore(InMemoryEmbeddedRunWorkspaceStore):
    def describe_backend(self):
        return {
            "backend_kind": "test_durable",
            "backend_mode": "strict_test",
            "durable": True,
            "fallback_active": False,
            "fallback_reason": "",
            "last_error": "",
            "state_contract": super().describe_backend()["state_contract"],
        }


class _DurableCountingWorkerOwnershipStore(InMemoryRuntimeWorkerOwnershipStore):
    def __init__(self):
        super().__init__()
        self.claim_calls = 0

    def claim_run(self, *args, **kwargs):
        self.claim_calls += 1
        return super().claim_run(*args, **kwargs)

    def build_contract(self):
        contract = super().build_contract()
        return {
            **contract,
            "adapter_kind": "sqlalchemy",
            "durable": True,
        }


class _DegradedDurableTestWorkspaceStore(InMemoryEmbeddedRunWorkspaceStore):
    def describe_backend(self):
        return {
            "backend_kind": "test_durable",
            "backend_mode": "strict_test",
            "durable": True,
            "fallback_active": True,
            "fallback_reason": "save_run_snapshot",
            "last_error": "db unavailable",
            "state_contract": super().describe_backend()["state_contract"],
        }


class _StubQueryControlTimelineService:
    def __init__(self):
        self.calls = []

    def record_stage(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "trace_written": True,
            "audit_written": True,
            "conversation_id": kwargs.get("conversation_id"),
            "snapshot_ref": {"source": "query_control", "event_type": f"query_control_{kwargs.get('stage')}"},
            "dedupe_key": f"query_control:{kwargs.get('channel')}:{kwargs.get('stage')}:{kwargs.get('conversation_id')}:{kwargs.get('query_id')}",
        }


class _FailingQueryControlTimelineService:
    def record_stage(self, **_kwargs):
        raise RuntimeError("query control recorder unavailable")


class _StubApprovalLifecycleTraceRecorder:
    def __init__(self):
        self.calls = []

    def record_event(self, **kwargs):
        self.calls.append(kwargs)
        event = kwargs.get("event") or {}
        return {
            "trace_written": True,
            "status_kind": event.get("status_kind"),
            "dedupe_key": f"test:{event.get('status_kind')}:{event.get('approval_request_id')}",
        }


class _FailingApprovalLifecycleTraceRecorder:
    def record_event(self, **_kwargs):
        raise RuntimeError("approval trace recorder unavailable")


class _FakeApprovalTraceService:
    def __init__(self):
        self.appended = []
        self.seen_dedupe_keys = set()

    def has_runtime_trace_dedupe_key(self, **kwargs):
        return kwargs.get("dedupe_key") in self.seen_dedupe_keys

    def append_runtime_trace(self, **kwargs):
        self.appended.append(kwargs)
        payload = kwargs.get("payload") or {}
        self.seen_dedupe_keys.add(payload.get("dedupe_key"))
        return True


class EmbeddedAgentRuntimeSDKTests(unittest.TestCase):
    def _build_tool_runtime_service(self):
        return ToolRuntimeService(
            tool_registry=ToolRegistry(),
            mcp_registry_service=Mock(build_capability_catalog=Mock(return_value={"capabilities": []})),
            framework_adapter_registry=Mock(build_health_entries=Mock(return_value=[])),
        )

    def test_sdk_contract_declares_minimal_embedded_methods(self):
        sdk = EmbeddedAgentRuntimeSDK()

        contract = sdk.build_contract()

        self.assertEqual(contract["contract_version"], "phase-b-embedded-sdk-v1")
        self.assertEqual(
            [item["method"] for item in contract["methods"]],
            [
                "create_run",
                "stream_events",
                "list_continuation_bindings",
                "probe_run_recovery",
                "register_tool",
                "submit_approval",
                "resume_run",
                "delegate_run",
                "evaluate_child_executor_preflight",
                "evaluate_child_executor_gate",
                "evaluate_child_executor_routing",
                "bind_child_executor_routing",
                "execute_bound_child_executor_stub",
                "execute_bound_child_executor",
                "merge_child_executor_output",
                "list_child_executor_outputs",
                "summarize_child_executor_outputs",
                "summarize_child_executor_merged_semantics",
                "create_artifact",
                "list_artifacts",
                "execute_run",
            ],
        )
        stability_by_method = {item["method"]: item["stability"] for item in contract["methods"]}
        self.assertEqual(stability_by_method["create_run"], "preview")
        self.assertEqual(stability_by_method["stream_events"], "preview")
        self.assertEqual(stability_by_method["list_continuation_bindings"], "preview")
        self.assertEqual(stability_by_method["probe_run_recovery"], "preview")
        self.assertEqual(stability_by_method["submit_approval"], "preview")
        self.assertEqual(stability_by_method["resume_run"], "preview")
        self.assertEqual(stability_by_method["delegate_run"], "preview")
        self.assertEqual(stability_by_method["evaluate_child_executor_preflight"], "preview")
        self.assertEqual(stability_by_method["evaluate_child_executor_gate"], "preview")
        self.assertEqual(stability_by_method["evaluate_child_executor_routing"], "preview")
        self.assertEqual(stability_by_method["bind_child_executor_routing"], "preview")
        self.assertEqual(stability_by_method["execute_bound_child_executor_stub"], "preview")
        self.assertEqual(stability_by_method["execute_bound_child_executor"], "preview")
        self.assertEqual(stability_by_method["merge_child_executor_output"], "preview")
        self.assertEqual(stability_by_method["list_child_executor_outputs"], "preview")
        self.assertEqual(stability_by_method["summarize_child_executor_outputs"], "preview")
        self.assertEqual(stability_by_method["summarize_child_executor_merged_semantics"], "preview")
        self.assertEqual(stability_by_method["create_artifact"], "preview")
        self.assertEqual(stability_by_method["list_artifacts"], "preview")
        self.assertEqual(stability_by_method["execute_run"], "preview")
        self.assertEqual(stability_by_method["register_tool"], "preview")
        event_status_kinds = {item["status_kind"]: item for item in contract["event_status_kinds"]}
        self.assertEqual(event_status_kinds["loop_continuation_registered"]["stability"], "preview")
        self.assertEqual(event_status_kinds["loop_continuation_consumed"]["category"], "continuation")
        self.assertEqual(event_status_kinds["loop_continuation_discarded"]["required_payload"], ["loop_continuation"])
        self.assertEqual(event_status_kinds["approval_ignored"]["category"], "approval")
        self.assertEqual(
            event_status_kinds["approval_ignored"]["required_payload"],
            ["approval_request_id", "approval_request", "original_decision", "attempted_decision"],
        )
        self.assertEqual(event_status_kinds["tool_approval_continued"]["category"], "tool")
        self.assertEqual(event_status_kinds["recovery_probe_evaluated"]["required_payload"], ["recovery"])
        self.assertEqual(event_status_kinds["recovery_failed_closed"]["category"], "recovery")
        self.assertEqual(
            contract["volatile_runtime_state"],
            [
                "_runs",
                "_events",
                "_approvals",
                "_artifacts",
                "_tool_continuations",
                "_loop_continuations",
            ],
        )
        self.assertEqual(
            contract["persistence_seams"],
            [
                "run_workspace_snapshot",
                "run_event_log",
                "approval_snapshot",
                "tool_approval_continuation_descriptor",
                "loop_continuation_descriptor",
                "artifact_store_seam",
            ],
        )
        self.assertEqual(
            [item["method"] for item in contract["recovery_entrypoints"]],
            ["probe_run_recovery", "submit_approval", "resume_run", "resume_run"],
        )
        approval_entry = next(
            item
            for item in contract["recovery_entrypoints"]
            if item["method"] == "submit_approval" and item.get("mode") == "approved"
        )
        self.assertTrue(approval_entry["cross_process_ready"])
        self.assertTrue(approval_entry["requires_durable_workspace"])
        self.assertTrue(approval_entry["requires_registry_bindings"])
        continue_loop_entry = next(
            item
            for item in contract["recovery_entrypoints"]
            if item["method"] == "resume_run" and item.get("mode") == "continue_loop"
        )
        self.assertTrue(continue_loop_entry["cross_process_ready"])
        self.assertTrue(continue_loop_entry["requires_durable_workspace"])
        self.assertTrue(continue_loop_entry["requires_registry_bindings"])
        recovery_operation_contract = contract["recovery_operation_contract"]
        self.assertEqual(
            recovery_operation_contract["contract_version"],
            "phase-ii-durable-recovery-operation-v1",
        )
        self.assertEqual(
            [item["entrypoint"] for item in recovery_operation_contract["entrypoints"]],
            ["submit_approval.approved", "resume_run.continue_loop"],
        )
        self.assertIn("recovered", recovery_operation_contract["operation_statuses"])
        self.assertFalse(recovery_operation_contract["worker_ownership"]["implemented"])
        default_resume_entry = next(
            item
            for item in contract["recovery_entrypoints"]
            if item["method"] == "resume_run" and item.get("mode") == "default"
        )
        self.assertFalse(default_resume_entry["requires_durable_workspace"])
        self.assertFalse(default_resume_entry["requires_registry_bindings"])
        self.assertEqual(contract["delegate_preflight"]["status"], "relationship_only")
        self.assertFalse(contract["delegate_preflight"]["real_child_executor_ready"])
        self.assertFalse(contract["delegate_preflight"]["promotion_ready"])
        self.assertIn(
            "child_run_recovery_boundary_defined",
            contract["delegate_preflight"]["promotion_requirements"],
        )
        self.assertIn("child_context_budget_defined", contract["delegate_preflight"]["missing_requirements"])
        self.assertIn("explicit_executor_binding_opt_in", contract["delegate_preflight"]["missing_requirements"])
        self.assertEqual(len(contract["delegate_preflight"]["requirement_checks"]), 5)

    def test_sdk_event_payload_validator_reports_missing_required_payload_fields(self):
        validation = validate_embedded_sdk_event_payloads([
            {
                "status_kind": "approval_created",
                "approval_request_id": "approval_1",
            },
            {
                "status_kind": "execution_loop_done",
                "run": {"run_id": "run_1"},
            },
        ])

        self.assertFalse(validation["valid"])
        self.assertEqual(validation["checked_event_count"], 2)
        self.assertEqual(validation["missing_payload_count"], 2)
        self.assertEqual(
            validation["missing_payloads"],
            [
                {
                    "index": 0,
                    "status_kind": "approval_created",
                    "missing_fields": ["approval_request"],
                },
                {
                    "index": 1,
                    "status_kind": "execution_loop_done",
                    "missing_fields": ["completed_steps"],
                },
            ],
        )

    def test_sdk_emitted_lifecycle_events_match_declared_required_payloads(self):
        sdk = EmbeddedAgentRuntimeSDK()
        direct_run = sdk.create_run({"run_kind": "chat"})
        sdk.execute_run(direct_run["run"]["run_id"])

        approval_run = sdk.create_run({"run_kind": "chat"})
        executed = sdk.execute_run(
            approval_run["run"]["run_id"],
            tool_policy=lambda _run: {
                "status": "approval_required",
                "tool_name": "filesystem_write",
                "tool_args": {"path": "case.md"},
                "reason": "高风险写文件工具需要人工审批",
            },
            tool_executor=lambda _run: {
                "tool_name": "filesystem_write",
                "args": {"path": "case.md"},
                "result": "写入成功",
            },
        )
        sdk.submit_approval(executed["approval_request"]["request_id"], "approved")
        sdk.resume_run(approval_run["run"]["run_id"], continue_loop=True)

        discarded_run = sdk.create_run({"run_kind": "chat"})
        discarded = sdk.execute_run(
            discarded_run["run"]["run_id"],
            tool_policy=lambda _run: {
                "status": "approval_required",
                "tool_name": "filesystem_write",
                "tool_args": {"path": "case.md"},
                "reason": "高风险写文件工具需要人工审批",
            },
            tool_executor=lambda _run: {
                "tool_name": "filesystem_write",
                "args": {"path": "case.md"},
                "result": "不应该执行",
            },
        )
        sdk.submit_approval(discarded["approval_request"]["request_id"], "denied")

        events = [
            *sdk.stream_events(direct_run["run"]["run_id"]),
            *sdk.stream_events(approval_run["run"]["run_id"]),
            *sdk.stream_events(discarded_run["run"]["run_id"]),
        ]

        validation = validate_embedded_sdk_event_payloads(events, contract=sdk.build_contract())

        self.assertTrue(validation["valid"])
        self.assertEqual(validation["missing_payloads"], [])
        emitted_status_kinds = {event["status_kind"] for event in events if event.get("status_kind")}
        self.assertTrue({
            "run_created",
            "approval_created",
            "approval_resolved",
            "loop_continuation_registered",
            "loop_continuation_consumed",
            "loop_continuation_discarded",
            "execution_loop_step",
            "execution_loop_done",
            "tool_approval_continued",
        }.issubset(emitted_status_kinds))

    def test_register_tool_updates_tool_runtime_registry(self):
        tool_runtime_service = self._build_tool_runtime_service()
        sdk = EmbeddedAgentRuntimeSDK(tool_runtime_service=tool_runtime_service)

        registered = sdk.register_tool({
            "name": "risk_lookup",
            "description": "Lookup risk indicators for a case.",
            "permission_level": "auto",
            "deterministic": True,
            "render_mode": "plain_text",
            "tags": ["risk"],
        })
        runtime_contract = tool_runtime_service.build_runtime_contract()

        self.assertEqual(registered["status"], "registered")
        self.assertEqual(registered["tool_spec"]["name"], "risk_lookup")
        self.assertFalse(registered["handler_registered"])
        self.assertTrue(registered["tool_registry_bridge"]["tool_runtime_service"])
        self.assertEqual(runtime_contract["tool_spec_count"], 1)
        self.assertEqual(runtime_contract["tools"][0]["name"], "risk_lookup")

    def test_register_tool_can_bind_executable_handler_for_tool_runtime_service(self):
        tool_runtime_service = self._build_tool_runtime_service()
        sdk = EmbeddedAgentRuntimeSDK(tool_runtime_service=tool_runtime_service)

        registered = sdk.register_tool(
            ToolSpec(
                name="risk_lookup",
                description="Lookup risk indicators.",
                permission_level="auto",
                deterministic=True,
                tags=("risk",),
            ),
            handler=lambda args: f"命中风险标签: {args['case_id']}",
            parameters={"case_id": {"type": "string", "required": True}},
        )
        executed = tool_runtime_service.execute_tool("risk_lookup", {"case_id": "case-1"})

        self.assertEqual(registered["status"], "registered")
        self.assertTrue(registered["handler_registered"])
        self.assertEqual(executed["status"], "ok")
        self.assertEqual(executed["result_text"], "命中风险标签: case-1")
        self.assertEqual(executed["execution"]["schema_validation"]["status"], "passed")

    def test_register_tool_rejects_invalid_tool_definition(self):
        tool_runtime_service = self._build_tool_runtime_service()
        sdk = EmbeddedAgentRuntimeSDK(tool_runtime_service=tool_runtime_service)

        with self.assertRaises(ValueError):
            sdk.register_tool({"name": "", "description": "missing name"})
        with self.assertRaises(ValueError):
            sdk.register_tool({"name": "risk_lookup", "description": ""})

        runtime_contract = tool_runtime_service.build_runtime_contract()
        self.assertEqual(runtime_contract["tool_spec_count"], 0)

    def test_execute_run_can_use_registered_tool_runtime_service_by_default(self):
        tool_runtime_service = self._build_tool_runtime_service()
        sdk = EmbeddedAgentRuntimeSDK(tool_runtime_service=tool_runtime_service)
        sdk.register_tool(
            ToolSpec(
                name="risk_lookup",
                description="Lookup risk indicators.",
                permission_level="auto",
                deterministic=True,
                tags=("risk",),
            ),
            handler=lambda args: f"命中风险标签: {args['case_id']}",
            parameters={"case_id": {"type": "string", "required": True}},
        )
        run = sdk.create_run({"run_kind": "chat"})

        executed = sdk.execute_run(
            run["run"]["run_id"],
            tool_policy=lambda _run: {
                "status": "allowed",
                "tool_name": "risk_lookup",
                "tool_args": {"case_id": "case-1"},
            },
        )

        history = executed["run"]["tool_history"]
        self.assertEqual(executed["run"]["state"], "done")
        self.assertEqual(history[0]["tool_name"], "risk_lookup")
        self.assertEqual(history[0]["result"], "命中风险标签: case-1")
        self.assertEqual(history[0]["execution"]["executor"], "tool_runtime_service")
        self.assertEqual(history[0]["execution"]["schema_validation"]["status"], "passed")

    def test_execute_run_pauses_ask_tool_and_resumes_runtime_service_after_approval(self):
        tool_runtime_service = self._build_tool_runtime_service()
        calls = []
        sdk = EmbeddedAgentRuntimeSDK(tool_runtime_service=tool_runtime_service)
        sdk.register_tool(
            ToolSpec(
                name="filesystem_write",
                description="Write file.",
                permission_level="ask",
                deterministic=False,
                tags=("filesystem", "write"),
            ),
            handler=lambda args: calls.append(dict(args)) or "written",
            parameters={"path": {"type": "string", "required": True}},
        )
        run = sdk.create_run({"run_kind": "chat"})

        waiting = sdk.execute_run(
            run["run"]["run_id"],
            tool_policy=lambda _run: {
                "status": "allowed",
                "tool_name": "filesystem_write",
                "tool_args": {"path": "case.md"},
            },
        )
        resumed = sdk.submit_approval(waiting["approval_request"]["request_id"], "approved")

        self.assertEqual(waiting["run"]["state"], "waiting_approval")
        self.assertEqual(calls, [{"path": "case.md"}])
        history = resumed["run"]["tool_history"]
        self.assertEqual(history[0]["tool_name"], "filesystem_write")
        self.assertEqual(history[0]["result"], "written")
        self.assertEqual(history[0]["execution"]["executor"], "tool_runtime_service")
        self.assertEqual(
            history[0]["execution"]["policy_decision"]["original_status"],
            "approval_required",
        )

    def test_execute_run_denies_deny_tool_before_runtime_service_invocation(self):
        tool_runtime_service = self._build_tool_runtime_service()
        calls = []
        sdk = EmbeddedAgentRuntimeSDK(tool_runtime_service=tool_runtime_service)
        sdk.register_tool(
            ToolSpec(
                name="dangerous_delete",
                description="Delete files.",
                permission_level="deny",
                deterministic=False,
                tags=("filesystem", "delete"),
            ),
            handler=lambda args: calls.append(dict(args)) or "deleted",
            parameters={"path": {"type": "string", "required": True}},
        )
        run = sdk.create_run({"run_kind": "chat"})

        executed = sdk.execute_run(
            run["run"]["run_id"],
            tool_policy=lambda _run: {
                "status": "allowed",
                "tool_name": "dangerous_delete",
                "tool_args": {"path": "case.md"},
            },
        )

        self.assertEqual(executed["run"]["state"], "failed")
        self.assertEqual(executed["run"]["stop_reason"], "tool_policy_denied")
        self.assertEqual(calls, [])

    def test_create_run_returns_runtime_snapshot_and_streamable_event(self):
        sdk = EmbeddedAgentRuntimeSDK()

        result = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
        })

        run = result["run"]
        self.assertTrue(run["runtime_core"])
        self.assertEqual(run["conversation_id"], 42)
        self.assertEqual(run["user_id"], 7)
        self.assertEqual(run["model_name"], "doubao")
        self.assertEqual(run["state"], "init")

        events = list(sdk.stream_events(run["run_id"]))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "status")
        self.assertEqual(events[0]["run_id"], run["run_id"])
        self.assertEqual(events[0]["status_kind"], "run_created")

    def test_list_continuation_bindings_returns_registry_catalog(self):
        registry = InMemoryEmbeddedContinuationRegistry()

        def _tool_executor(_run):
            return None

        def _reviewer(_run):
            return {"status": "approved"}

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
            metadata={"gate": "quality_gate"},
        )
        sdk = EmbeddedAgentRuntimeSDK(continuation_registry=registry)

        catalog = sdk.list_continuation_bindings()

        self.assertEqual(catalog["registry_type"], "InMemoryEmbeddedContinuationRegistry")
        self.assertEqual(catalog["total_bindings"], 2)
        self.assertEqual(
            [item["binding_id"] for item in catalog["bindings"]],
            ["reviewer.quality_gate", "tool_executor.filesystem_write"],
        )
        tool_binding = next(item for item in catalog["bindings"] if item["binding_id"] == "tool_executor.filesystem_write")
        self.assertEqual(tool_binding["binding_kind"], "tool_executor")
        self.assertEqual(tool_binding["handler_name"], "_tool_executor")
        self.assertEqual(tool_binding["metadata"]["tool_name"], "filesystem_write")

    def test_default_sdk_uses_shared_continuation_registry_singleton(self):
        with patch.object(
            continuation_registry_module,
            "_embedded_continuation_registry_singleton",
            InMemoryEmbeddedContinuationRegistry(),
        ):
            sdk = EmbeddedAgentRuntimeSDK()

            catalog = sdk.list_continuation_bindings()

        self.assertEqual(catalog["registry_type"], "InMemoryEmbeddedContinuationRegistry")
        self.assertEqual(catalog["total_bindings"], 0)

    def test_sdk_can_accept_runtime_dependencies_bundle(self):
        store = _DurableTestWorkspaceStore()
        registry = InMemoryEmbeddedContinuationRegistry()
        ownership_store = InMemoryRuntimeWorkerOwnershipStore()
        dependencies = EmbeddedRuntimeDependencies(
            workspace_store=store,
            continuation_registry=registry,
            worker_ownership_store=ownership_store,
        )

        sdk = EmbeddedAgentRuntimeSDK(runtime_dependencies=dependencies)

        self.assertIs(sdk._workspace_store, store)
        self.assertIs(sdk._continuation_registry, registry)
        self.assertIs(sdk._worker_ownership_store, ownership_store)

    def test_create_default_embedded_runtime_sdk_uses_dependency_bundle(self):
        store = _DurableTestWorkspaceStore()
        registry = InMemoryEmbeddedContinuationRegistry()
        dependencies = EmbeddedRuntimeDependencies(
            workspace_store=store,
            continuation_registry=registry,
        )

        sdk = create_default_embedded_runtime_sdk(runtime_dependencies=dependencies)

        self.assertIs(sdk._workspace_store, store)
        self.assertIs(sdk._continuation_registry, registry)

    def test_runtime_factory_can_create_sdk_with_shared_dependencies(self):
        store = _DurableTestWorkspaceStore()
        registry = InMemoryEmbeddedContinuationRegistry()
        ownership_store = InMemoryRuntimeWorkerOwnershipStore()
        factory = EmbeddedRuntimeFactory(
            dependencies=EmbeddedRuntimeDependencies(
                workspace_store=store,
                continuation_registry=registry,
                worker_ownership_store=ownership_store,
            )
        )

        sdk = factory.create_sdk()

        self.assertIs(sdk._workspace_store, store)
        self.assertIs(sdk._continuation_registry, registry)
        self.assertIs(sdk._worker_ownership_store, ownership_store)

    def test_runtime_factory_can_create_sdk_and_agent_with_shared_persistence_dependencies(self):
        store = _DurableTestWorkspaceStore()
        registry = InMemoryEmbeddedContinuationRegistry()
        factory = EmbeddedRuntimeFactory(
            dependencies=EmbeddedRuntimeDependencies(
                workspace_store=store,
                continuation_registry=registry,
            )
        )

        sdk = factory.create_sdk()
        agent = factory.create_agent(name="fraud_assistant")

        self.assertIs(sdk._workspace_store, store)
        self.assertIs(agent.sdk._workspace_store, store)
        self.assertIs(sdk._continuation_registry, registry)
        self.assertIs(agent.sdk._continuation_registry, registry)

    def test_runtime_factory_contract_surfaces_default_runtime_profile(self):
        store = _DurableTestWorkspaceStore()
        registry = InMemoryEmbeddedContinuationRegistry()
        ownership_store = InMemoryRuntimeWorkerOwnershipStore()
        factory = EmbeddedRuntimeFactory(
            dependencies=EmbeddedRuntimeDependencies(
                workspace_store=store,
                continuation_registry=registry,
                worker_ownership_store=ownership_store,
            )
        )

        with patch.object(runtime_dependencies_module, "get_embedded_workspace_store_mode", return_value="strict_sql"):
            contract = factory.build_runtime_contract()

        self.assertEqual(contract["contract_version"], "phase-ii-embedded-runtime-factory-v1")
        self.assertTrue(contract["shared_default_runtime"])
        self.assertEqual(contract["default_runtime_profile"]["db_mode"], "sqlite")
        self.assertEqual(contract["default_runtime_profile"]["db_mode_source"], "default")
        self.assertEqual(contract["default_runtime_profile"]["embedded_workspace_store_mode"], "strict_sql")
        self.assertEqual(contract["default_runtime_profile"]["embedded_workspace_store_mode_source"], "derived_from_db_mode")
        self.assertEqual(contract["default_runtime_profile"]["worker_ownership_store_mode"], "memory_only")
        self.assertEqual(contract["default_runtime_profile"]["worker_ownership_store_mode_source"], "default")
        self.assertEqual(contract["default_runtime_profile"]["default_runtime_mode"], "durable_default")
        self.assertEqual(contract["default_runtime_profile"]["recovery_posture"], "cross_process_candidate")
        self.assertEqual(contract["default_runtime_profile"]["persistence_posture"], "durable_ready")
        self.assertEqual(contract["default_runtime_profile"]["workspace_strategy_rule"], "memory_only_if_db_mode_memory_else_strict_sql")
        self.assertTrue(contract["default_runtime_profile"]["durable_by_default"])
        self.assertEqual(contract["default_runtime_profile"]["recommended_bootstrap"], "EmbeddedRuntimeFactory")
        self.assertEqual(
            contract["default_runtime_profile"]["configurable_bootstrap_knobs"],
            ["DB_MODE", "EMBEDDED_WORKSPACE_STORE_MODE", "WORKER_OWNERSHIP_STORE_MODE"],
        )
        self.assertEqual(
            contract["default_runtime_profile"]["hot_reloadable_bootstrap_knobs"],
            ["EMBEDDED_WORKSPACE_STORE_MODE", "WORKER_OWNERSHIP_STORE_MODE"],
        )
        self.assertEqual(
            contract["default_runtime_profile"]["restart_required_bootstrap_knobs"],
            ["DB_MODE"],
        )
        self.assertEqual(contract["workspace_backend"]["backend_kind"], "test_durable")
        self.assertTrue(contract["workspace_backend"]["durable"])
        self.assertEqual(
            contract["persistence_interface"]["contract_version"],
            "phase-ii-embedded-sdk-persistence-interface-v1",
        )
        self.assertEqual(contract["persistence_interface"]["persistence_posture"], "durable_ready")
        self.assertEqual(contract["persistence_interface"]["workspace_backend_kind"], "test_durable")
        self.assertEqual(contract["persistence_interface"]["workspace_backend_mode"], "strict_test")
        self.assertTrue(contract["persistence_interface"]["cross_process_candidate"])
        self.assertEqual(contract["persistence_interface"]["cross_process_block_reason"], "")
        self.assertEqual(contract["continuation_registry"]["registry_type"], "InMemoryEmbeddedContinuationRegistry")
        self.assertIn("worker_ownership_store", contract["dependency_sources"])
        self.assertTrue(contract["worker_ownership"]["available"])
        self.assertEqual(contract["worker_ownership"]["adapter_kind"], "in_memory")
        self.assertFalse(contract["worker_ownership"]["durable"])
        self.assertEqual(contract["worker_ownership"]["enforcement_mode"], "opt_in_descriptor_evidence")
        self.assertIn("validate_ownership", contract["worker_ownership"]["operations"])
        readiness = contract["worker_ownership"]["operational_readiness"]
        self.assertEqual(readiness["contract_version"], "phase-ii-worker-ownership-operations-v1")
        self.assertFalse(readiness["production_ready"])
        self.assertEqual(readiness["recovery_entry_claim_mode"], "descriptor_evidence_only")
        self.assertEqual(contract["default_recovery_expectation"]["contract_version"], "phase-ii-default-recovery-expectation-v1")
        self.assertFalse(contract["default_recovery_expectation"]["default_probe_recoverable"])
        self.assertEqual(contract["default_recovery_expectation"]["default_probe_reason"], "descriptor_missing")
        self.assertTrue(contract["default_recovery_expectation"]["cross_process_candidate"])
        self.assertEqual(contract["default_recovery_expectation"]["cross_process_block_reason"], "")
        self.assertIn("runtime.run_recovery_probe", contract["recovery_capabilities"])
        self.assertEqual(contract["factory_methods"], ["create_sdk", "create_agent"])

    def test_runtime_factory_contract_surfaces_memory_preview_persistence_posture(self):
        factory = EmbeddedRuntimeFactory(
            dependencies=EmbeddedRuntimeDependencies(
                workspace_store=InMemoryEmbeddedRunWorkspaceStore(),
                continuation_registry=InMemoryEmbeddedContinuationRegistry(),
            )
        )

        contract = factory.build_runtime_contract()

        self.assertEqual(contract["default_runtime_profile"]["default_runtime_mode"], "memory_preview")
        self.assertEqual(contract["default_runtime_profile"]["recovery_posture"], "in_process_only")
        self.assertEqual(contract["default_runtime_profile"]["persistence_posture"], "memory_preview")
        self.assertEqual(contract["persistence_interface"]["persistence_posture"], "memory_preview")
        self.assertFalse(contract["persistence_interface"]["cross_process_candidate"])
        self.assertEqual(
            contract["persistence_interface"]["cross_process_block_reason"],
            "workspace_backend_not_durable",
        )

    def test_runtime_factory_contract_surfaces_durable_degraded_persistence_posture(self):
        factory = EmbeddedRuntimeFactory(
            dependencies=EmbeddedRuntimeDependencies(
                workspace_store=_DegradedDurableTestWorkspaceStore(),
                continuation_registry=InMemoryEmbeddedContinuationRegistry(),
            )
        )

        contract = factory.build_runtime_contract()

        self.assertEqual(contract["default_runtime_profile"]["default_runtime_mode"], "durable_degraded")
        self.assertEqual(contract["default_runtime_profile"]["recovery_posture"], "degraded_fallback")
        self.assertEqual(contract["default_runtime_profile"]["persistence_posture"], "durable_degraded")
        self.assertEqual(contract["persistence_interface"]["persistence_posture"], "durable_degraded")
        self.assertTrue(contract["persistence_interface"]["fallback_active"])
        self.assertEqual(contract["persistence_interface"]["fallback_reason"], "save_run_snapshot")
        self.assertEqual(
            contract["persistence_interface"]["cross_process_block_reason"],
            "workspace_backend_fallback_active",
        )

    def test_get_default_runtime_factory_exposes_default_dependencies(self):
        factory = get_default_embedded_runtime_factory()

        self.assertIsInstance(factory.dependencies, EmbeddedRuntimeDependencies)

    def test_create_run_can_create_pending_approval_and_submit_decision(self):
        sdk = EmbeddedAgentRuntimeSDK()

        result = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "run_kind": "child",
            "approval_request": {
                "request_id": "approval_1",
                "tool_name": "mcp_filesystem_write",
                "tool_args": {"path": "README.md"},
                "permission_level": "ask",
                "reason": "需要人工确认文件写入。",
                "reason_code": "high_risk_tool_requires_approval",
            },
        })

        run_id = result["run"]["run_id"]
        self.assertEqual(result["run"]["state"], "waiting_approval")
        self.assertEqual(result["approval_request"]["request_id"], "approval_1")
        self.assertEqual(result["approval_request"]["status"], "pending")
        self.assertEqual(result["approval_request"]["run_id"], run_id)

        submitted = sdk.submit_approval("approval_1", "approved")

        self.assertEqual(submitted["approval_request"]["status"], "approved")
        self.assertEqual(submitted["approval_request"]["result"], "approved")
        self.assertEqual(submitted["run"]["state"], "observing")
        events = list(sdk.stream_events(run_id))
        self.assertTrue(any(event["status_kind"] == "approval_created" for event in events))
        self.assertTrue(any(event["status_kind"] == "approval_resolved" for event in events))

    def test_approval_lifecycle_trace_recorder_is_opt_in(self):
        sdk = EmbeddedAgentRuntimeSDK()
        result = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "run_kind": "child",
            "approval_request": {
                "request_id": "approval_1",
                "tool_name": "mcp_filesystem_write",
                "permission_level": "ask",
                "reason": "需要人工确认文件写入。",
            },
        })

        submitted = sdk.submit_approval("approval_1", "approved")

        self.assertEqual(submitted["approval_request"]["status"], "approved")
        self.assertNotIn("approval_lifecycle_trace_records", submitted["run"]["metadata"])
        events = list(sdk.stream_events(result["run"]["run_id"]))
        self.assertTrue(any(event["status_kind"] == "approval_resolved" for event in events))

    def test_approval_lifecycle_trace_recorder_records_resolved_replayed_and_ignored(self):
        recorder = _StubApprovalLifecycleTraceRecorder()
        sdk = EmbeddedAgentRuntimeSDK(approval_lifecycle_trace_recorder=recorder)
        result = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "run_kind": "child",
            "approval_request": {
                "request_id": "approval_1",
                "tool_name": "mcp_filesystem_write",
                "permission_level": "ask",
                "reason": "需要人工确认文件写入。",
            },
        })

        approved = sdk.submit_approval("approval_1", "approved")
        replayed = sdk.submit_approval("approval_1", "approved")
        ignored = sdk.submit_approval("approval_1", "denied")

        self.assertEqual(approved["approval_request"]["status"], "approved")
        self.assertEqual(replayed["approval_submission"]["status"], "replayed")
        self.assertEqual(ignored["approval_submission"]["status"], "ignored")
        status_kinds = [call["event"]["status_kind"] for call in recorder.calls]
        self.assertEqual(status_kinds, ["approval_resolved", "approval_replayed", "approval_ignored"])
        run = sdk._runs[result["run"]["run_id"]]
        records = run.metadata["approval_lifecycle_trace_records"]
        self.assertEqual([record["status_kind"] for record in records], status_kinds)

    def test_approval_lifecycle_trace_recorder_failure_is_fail_open(self):
        sdk = EmbeddedAgentRuntimeSDK(
            approval_lifecycle_trace_recorder=_FailingApprovalLifecycleTraceRecorder()
        )
        result = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "run_kind": "child",
            "approval_request": {
                "request_id": "approval_1",
                "tool_name": "mcp_filesystem_write",
                "permission_level": "ask",
                "reason": "需要人工确认文件写入。",
            },
        })

        submitted = sdk.submit_approval("approval_1", "approved")

        self.assertEqual(submitted["approval_request"]["status"], "approved")
        run = sdk._runs[result["run"]["run_id"]]
        failures = run.metadata["approval_lifecycle_trace_failures"]
        self.assertEqual(failures[0]["status_kind"], "approval_resolved")
        self.assertIn("approval trace recorder unavailable", failures[0]["error"])

    def test_approval_lifecycle_trace_service_dedupes_repeated_replay_evidence(self):
        trace_service = _FakeApprovalTraceService()
        service = SdkApprovalLifecycleTimelineService(
            db=object(),
            trace_service_factory=lambda _db: trace_service,
        )
        sdk = EmbeddedAgentRuntimeSDK()
        result = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "run_kind": "child",
            "approval_request": {
                "request_id": "approval_1",
                "tool_name": "mcp_filesystem_write",
                "permission_level": "ask",
                "reason": "需要人工确认文件写入。",
            },
        })
        run_context = sdk._runs[result["run"]["run_id"]]
        event = {
            "status_kind": "approval_replayed",
            "approval_request_id": "approval_1",
            "approval_request": {
                "request_id": "approval_1",
                "status": "approved",
                "result": "approved",
            },
            "approval_submission": {
                "status": "replayed",
                "original_decision": "approved",
                "attempted_decision": "approved",
            },
            "original_decision": "approved",
            "attempted_decision": "approved",
            "summary": "Embedded SDK replayed resolved approval submission",
        }

        first = service.record_event(run_context=run_context, event=event)
        second = service.record_event(run_context=run_context, event=event)

        self.assertTrue(first["trace_written"])
        self.assertFalse(second["trace_written"])
        self.assertEqual(second["dedupe_source"], "persisted_trace")
        self.assertEqual(len(trace_service.appended), 1)
        payload = trace_service.appended[0]["payload"]
        self.assertEqual(payload["status_kind"], "approval_replayed")
        self.assertEqual(payload["approval_request_id"], "approval_1")
        self.assertNotIn("handler", payload)
        self.assertNotIn("callable", payload)

    def test_approval_lifecycle_trace_service_records_recovery_failed_closed_reason(self):
        trace_service = _FakeApprovalTraceService()
        service = SdkApprovalLifecycleTimelineService(
            db=object(),
            trace_service_factory=lambda _db: trace_service,
        )
        sdk = EmbeddedAgentRuntimeSDK()
        result = sdk.create_run({"conversation_id": 42, "user_id": 7, "run_kind": "chat"})
        run_context = sdk._runs[result["run"]["run_id"]]
        event = {
            "status_kind": "recovery_failed_closed",
            "summary": "Embedded SDK recovery failed closed",
            "recovery": {
                "request_id": "approval_1",
                "reason": "missing_executable_continuation",
                "blocked_reason": "missing_executable_continuation",
            },
        }

        recorded = service.record_event(run_context=run_context, event=event)

        self.assertTrue(recorded["trace_written"])
        trace = trace_service.appended[0]
        self.assertEqual(trace["severity"], "warning")
        self.assertEqual(trace["payload"]["status_kind"], "recovery_failed_closed")
        self.assertEqual(trace["payload"]["recovery_reason"], "missing_executable_continuation")

    def test_resume_run_continues_observing_run_and_emits_state_event(self):
        sdk = EmbeddedAgentRuntimeSDK()
        result = sdk.create_run({
            "run_kind": "child",
            "approval_request": {
                "request_id": "approval_1",
                "tool_name": "mcp_filesystem_write",
                "reason": "需要人工确认文件写入。",
            },
        })
        run_id = result["run"]["run_id"]
        sdk.submit_approval("approval_1", "approved")

        resumed = sdk.resume_run(run_id)

        self.assertEqual(resumed["run"]["state"], "generating")
        self.assertEqual(resumed["run"]["iteration"], 1)
        self.assertEqual(resumed["run"]["stop_reason"], "run_resumed")
        events = list(sdk.stream_events(run_id))
        self.assertTrue(any(event["status_kind"] == "run_resumed" for event in events))
        self.assertEqual(events[-1]["state"], "generating")

    def test_resume_run_rejects_runs_that_are_not_ready_to_resume(self):
        sdk = EmbeddedAgentRuntimeSDK()
        result = sdk.create_run({"run_kind": "chat"})

        with self.assertRaises(ValueError):
            sdk.resume_run(result["run"]["run_id"])

    def test_delegate_run_creates_child_run_and_records_parent_event(self):
        sdk = EmbeddedAgentRuntimeSDK()
        parent = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
            "metadata": {"agent_name": "fraud_assistant"},
        })

        child = sdk.delegate_run(parent["run"]["run_id"], {
            "input": "复核交易风险",
            "metadata": {"agent_name": "risk_reviewer"},
        })

        child_run = child["run"]
        self.assertEqual(child_run["parent_run_id"], parent["run"]["run_id"])
        self.assertEqual(child_run["run_kind"], "child")
        self.assertEqual(child_run["conversation_id"], 42)
        self.assertEqual(child_run["user_id"], 7)
        self.assertEqual(child_run["model_name"], "doubao")
        self.assertEqual(child_run["metadata"]["agent_name"], "risk_reviewer")
        self.assertEqual(child_run["metadata"]["input"], "复核交易风险")
        self.assertEqual(child["child_executor_preflight"]["status"], "relationship_only")
        self.assertFalse(child["child_executor_preflight"]["real_child_executor_ready"])
        self.assertFalse(child["child_executor_preflight"]["promotion_ready"])
        self.assertEqual(
            child_run["metadata"]["child_executor_preflight"]["promotion_requirements"],
            child["child_executor_preflight"]["promotion_requirements"],
        )

        parent_events = list(sdk.stream_events(parent["run"]["run_id"]))
        self.assertTrue(any(event["status_kind"] == "child_run_created" for event in parent_events))
        child_event = next(event for event in parent_events if event["status_kind"] == "child_run_created")
        self.assertEqual(child_event["child_run_id"], child_run["run_id"])
        self.assertEqual(child_event["child_executor_preflight"]["status"], "relationship_only")

    def test_evaluate_child_executor_preflight_can_inherit_parent_defaults_without_creating_run(self):
        sdk = EmbeddedAgentRuntimeSDK()
        parent = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
            "metadata": {"agent_name": "fraud_assistant"},
        })

        preflight = sdk.evaluate_child_executor_preflight(
            {
                "input": "复核交易风险",
                "merge_strategy": "append_summary",
                "metadata": {
                    "scheduler_policy": {"timeout_seconds": 45},
                    "worker_runtime_backend": "embedded_sdk_worker",
                    "explicit_executor_binding_opt_in": True,
                },
            },
            parent_run_id=parent["run"]["run_id"],
        )

        self.assertEqual(preflight["status"], "promotion_candidate")
        self.assertTrue(preflight["promotion_ready"])
        self.assertEqual(preflight["executor_binding_status"], "ready")
        self.assertEqual(preflight["executor_binding_blockers"], [])
        self.assertEqual(preflight["recommended_next_step"], "wire_executor_backend")
        backend_check = next(
            item
            for item in preflight["requirement_checks"]
            if item["requirement"] == "worker_runtime_backend_selected"
        )
        self.assertTrue(backend_check["satisfied"])
        self.assertEqual(
            backend_check["evidence"]["backend_registry"]["backend_id"],
            "embedded_sdk_worker",
        )
        self.assertFalse(backend_check["evidence"]["backend_registry"]["dispatch_ready"])

    def test_child_executor_backend_registry_reports_default_relationship_only(self):
        registry = build_child_executor_backend_registry_contract()

        self.assertEqual(registry["contract_version"], "phase-ii-child-executor-backend-registry-v1")
        self.assertEqual(registry["overall_status"], "relationship_only")
        self.assertEqual(registry["default_backend_id"], "embedded_sdk_worker")
        self.assertEqual(registry["ready_backend_count"], 0)
        self.assertIn("embedded_sdk_worker", registry["backends_by_id"])
        self.assertFalse(registry["backends_by_id"]["embedded_sdk_worker"]["dispatch_ready"])

    def test_child_executor_backend_registry_blocks_unknown_backend(self):
        evidence = resolve_child_executor_backend("does_not_exist")

        self.assertFalse(evidence["known"])
        self.assertEqual(evidence["status"], "unknown")
        self.assertFalse(evidence["dispatch_ready"])
        self.assertIn("unknown_child_executor_backend", evidence["blockers"])

    def test_child_executor_dispatch_contract_reports_default_blocked_boundary(self):
        contract = build_embedded_sdk_contract()["child_executor_dispatch_contract"]

        self.assertEqual(contract["contract_version"], "phase-ii-child-executor-dispatch-v1")
        self.assertEqual(contract["overall_status"], "blocked")
        self.assertFalse(contract["dispatch_ready"])
        self.assertFalse(contract["will_dispatch"])
        self.assertTrue(contract["relationship_seam_preserved"])
        self.assertIn("promotion_gate_allowed", contract["blockers"])
        self.assertIn("worker_backend_dispatch_ready", contract["blockers"])
        self.assertIn("child_executor_backend_registry", contract["required_contracts"])

    def test_evaluate_child_executor_gate_reports_blocked_when_preflight_is_not_ready(self):
        sdk = EmbeddedAgentRuntimeSDK()
        parent = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
            "metadata": {"agent_name": "fraud_assistant"},
        })

        gate = sdk.evaluate_child_executor_gate(
            {"input": "复核交易风险"},
            parent_run_id=parent["run"]["run_id"],
        )

        self.assertEqual(gate["gate_status"], "blocked")
        self.assertFalse(gate["allowed"])
        self.assertEqual(gate["failure_reason"], "child_executor_preflight_blocked")
        self.assertEqual(gate["executor_path"], "")
        self.assertIn("child_context_budget_defined", gate["blockers"])
        self.assertEqual(gate["recommended_next_step"], "keep_relationship_only")
        prerequisites = gate["child_executor_execution_prerequisites"]
        self.assertEqual(prerequisites["contract_version"], "phase-ii-child-executor-execution-prerequisites-v1")
        self.assertEqual(prerequisites["overall_status"], "blocked")
        self.assertFalse(prerequisites["ready"])
        self.assertTrue(prerequisites["relationship_seam_preserved"])
        self.assertIn("child_context_budget_defined", prerequisites["missing_requirements"])
        self.assertIn("promotion_gate_allowed", prerequisites["missing_requirements"])

    def test_evaluate_child_executor_gate_reports_passed_when_preflight_is_ready(self):
        sdk = EmbeddedAgentRuntimeSDK()
        parent = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
            "metadata": {"agent_name": "fraud_assistant"},
        })

        gate = sdk.evaluate_child_executor_gate(
            {
                "input": "复核交易风险",
                "merge_strategy": "append_summary",
                "metadata": {
                    "scheduler_policy": {"timeout_seconds": 45},
                    "worker_runtime_backend": "embedded_sdk_worker",
                    "explicit_executor_binding_opt_in": True,
                },
            },
            parent_run_id=parent["run"]["run_id"],
        )

        self.assertEqual(gate["gate_status"], "passed")
        self.assertTrue(gate["allowed"])
        self.assertEqual(gate["failure_reason"], "")
        self.assertEqual(gate["executor_path"], "embedded_sdk_worker_candidate")
        self.assertEqual(gate["blockers"], [])
        self.assertEqual(gate["recommended_next_step"], "bind_embedded_sdk_worker_executor")
        self.assertEqual(gate["preflight"]["status"], "promotion_candidate")
        prerequisites = gate["child_executor_execution_prerequisites"]
        self.assertEqual(prerequisites["overall_status"], "blocked")
        self.assertFalse(prerequisites["ready"])
        self.assertTrue(prerequisites["relationship_seam_preserved"])
        self.assertIn("worker_backend_dispatch_ready", prerequisites["missing_requirements"])
        dispatch = build_child_executor_dispatch_contract(gate=gate)
        self.assertEqual(dispatch["overall_status"], "blocked")
        self.assertFalse(dispatch["dispatch_ready"])
        self.assertFalse(dispatch["will_dispatch"])
        self.assertTrue(dispatch["gate_allowed"])
        self.assertFalse(dispatch["prerequisites_ready"])
        self.assertFalse(dispatch["backend_dispatch_ready"])
        self.assertIn("worker_backend_dispatch_ready", dispatch["blockers"])

    def test_evaluate_child_executor_routing_reports_blocked_and_routed_status(self):
        sdk = EmbeddedAgentRuntimeSDK()
        parent = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
            "metadata": {"agent_name": "fraud_assistant"},
        })

        blocked = sdk.evaluate_child_executor_routing(
            {"input": "复核交易风险"},
            parent_run_id=parent["run"]["run_id"],
        )
        self.assertEqual(blocked["route_status"], "blocked")
        self.assertFalse(blocked["will_execute"])
        self.assertEqual(blocked["executor_path"], "")
        self.assertEqual(blocked["recommended_action"], "keep_relationship_only")

        routed = sdk.evaluate_child_executor_routing(
            {
                "input": "复核交易风险",
                "merge_strategy": "append_summary",
                "metadata": {
                    "scheduler_policy": {"timeout_seconds": 45},
                    "worker_runtime_backend": "embedded_sdk_worker",
                    "explicit_executor_binding_opt_in": True,
                },
            },
            parent_run_id=parent["run"]["run_id"],
        )
        self.assertEqual(routed["route_status"], "routed")
        self.assertFalse(routed["will_execute"])
        self.assertEqual(routed["executor_path"], "embedded_sdk_worker_candidate")
        self.assertEqual(routed["recommended_action"], "bind_embedded_sdk_worker_executor")
        self.assertEqual(routed["gate"]["gate_status"], "passed")

    def test_bind_child_executor_routing_reports_blocked_and_bound_status(self):
        sdk = EmbeddedAgentRuntimeSDK()
        parent = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
            "metadata": {"agent_name": "fraud_assistant"},
        })

        blocked = sdk.bind_child_executor_routing(
            {"input": "复核交易风险"},
            parent_run_id=parent["run"]["run_id"],
        )
        self.assertEqual(blocked["binding_status"], "blocked")
        self.assertEqual(blocked["binding_id"], "")
        self.assertEqual(blocked["recommended_action"], "keep_relationship_only")

        bound = sdk.bind_child_executor_routing(
            {
                "input": "复核交易风险",
                "merge_strategy": "append_summary",
                "metadata": {
                    "scheduler_policy": {"timeout_seconds": 45},
                    "worker_runtime_backend": "embedded_sdk_worker",
                    "explicit_executor_binding_opt_in": True,
                },
            },
            parent_run_id=parent["run"]["run_id"],
        )
        self.assertEqual(bound["binding_status"], "bound")
        self.assertFalse(bound["will_execute"])
        self.assertIn("embedded_sdk_worker_candidate", bound["binding_id"])
        self.assertEqual(bound["executor_path"], "embedded_sdk_worker_candidate")
        parent_events = list(sdk.stream_events(parent["run"]["run_id"]))
        binding_events = [event for event in parent_events if event["status_kind"] == "child_executor_binding_prepared"]
        binding_event = binding_events[-1]
        self.assertEqual(binding_event["child_executor_binding"]["binding_status"], "bound")

    def test_execute_bound_child_executor_stub_reports_blocked_and_recorded_status(self):
        sdk = EmbeddedAgentRuntimeSDK()
        parent = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
            "metadata": {"agent_name": "fraud_assistant"},
        })

        blocked_binding = sdk.bind_child_executor_routing(
            {"input": "复核交易风险"},
            parent_run_id=parent["run"]["run_id"],
        )
        blocked_stub = sdk.execute_bound_child_executor_stub(
            blocked_binding,
            parent_run_id=parent["run"]["run_id"],
        )
        self.assertEqual(blocked_stub["stub_status"], "blocked")
        self.assertEqual(blocked_stub["binding_id"], "")
        self.assertEqual(blocked_stub["recommended_action"], "keep_relationship_only")

        bound_binding = sdk.bind_child_executor_routing(
            {
                "input": "复核交易风险",
                "merge_strategy": "append_summary",
                "metadata": {
                    "agent_name": "risk_reviewer",
                    "scheduler_policy": {"timeout_seconds": 45},
                    "worker_runtime_backend": "embedded_sdk_worker",
                    "explicit_executor_binding_opt_in": True,
                },
            },
            parent_run_id=parent["run"]["run_id"],
        )
        recorded_stub = sdk.execute_bound_child_executor_stub(
            bound_binding,
            parent_run_id=parent["run"]["run_id"],
        )
        self.assertEqual(recorded_stub["stub_status"], "recorded")
        self.assertFalse(recorded_stub["will_execute"])
        self.assertIn("embedded_sdk_worker_candidate", recorded_stub["binding_id"])
        self.assertEqual(recorded_stub["executor_path"], "embedded_sdk_worker_candidate")
        parent_events = list(sdk.stream_events(parent["run"]["run_id"]))
        stub_events = [event for event in parent_events if event["status_kind"] == "child_executor_stub_recorded"]
        self.assertEqual(stub_events[-1]["child_executor_stub"]["stub_status"], "recorded")

    def test_execute_bound_child_executor_reports_blocked_and_executed_status(self):
        sdk = EmbeddedAgentRuntimeSDK()
        parent = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
            "metadata": {"agent_name": "fraud_assistant"},
        })

        blocked_binding = sdk.bind_child_executor_routing(
            {"input": "复核交易风险"},
            parent_run_id=parent["run"]["run_id"],
        )
        blocked_execution = sdk.execute_bound_child_executor(
            blocked_binding,
            parent_run_id=parent["run"]["run_id"],
        )
        self.assertEqual(blocked_execution["execution_status"], "blocked")
        self.assertEqual(blocked_execution["executor_path"], "")

        bound_binding = sdk.bind_child_executor_routing(
            {
                "input": "复核交易风险",
                "merge_strategy": "append_summary",
                "metadata": {
                    "agent_name": "risk_reviewer",
                    "scheduler_policy": {"timeout_seconds": 45},
                    "worker_runtime_backend": "embedded_sdk_worker",
                    "explicit_executor_binding_opt_in": True,
                },
            },
            parent_run_id=parent["run"]["run_id"],
        )
        executed = sdk.execute_bound_child_executor(
            bound_binding,
            parent_run_id=parent["run"]["run_id"],
        )
        self.assertEqual(executed["execution_status"], "executed")
        self.assertTrue(executed["will_execute"])
        self.assertEqual(executed["execution_mode"], "embedded_sdk_worker_skeleton")
        self.assertIn("risk_reviewer", executed["output_summary"])
        self.assertIn("风险复核结论", executed["output_text"])
        self.assertEqual(executed["output_payload"]["executor_kind"], "embedded_sdk_worker_skeleton")
        self.assertEqual(executed["output_payload"]["merge_strategy"], "append_summary")
        self.assertEqual(executed["output_payload"]["intent_label"], "risk_review")
        self.assertEqual(executed["output_payload"]["risk_level"], "medium")
        self.assertIn("交易", executed["output_payload"]["entities"])
        self.assertGreaterEqual(len(executed["output_payload"]["focus_points"]), 3)
        self.assertGreaterEqual(len(executed["output_payload"]["action_items"]), 3)
        self.assertEqual(executed["output_payload"]["business_result"]["result_type"], "risk_assessment")
        self.assertIn("风险复核", executed["output_payload"]["business_result"]["headline"])
        self.assertIn("交易", executed["output_payload"]["business_result"]["entities"])
        self.assertGreaterEqual(len(executed["output_payload"]["recommendations"]), 2)
        self.assertIn("child-output:", executed["output_envelope"]["artifact_ref"]["artifact_id"])
        self.assertEqual(executed["output_envelope"]["merge_hint"], "append_summary")
        self.assertTrue(executed["output_envelope"]["merge_ready"])
        self.assertEqual(len(executed["output_envelope"]["sections"]), 3)
        self.assertEqual(executed["output_envelope"]["payload"]["agent_name"], "risk_reviewer")
        self.assertEqual(executed["output_envelope"]["sections"][0]["metadata"]["intent_label"], "risk_review")
        self.assertEqual(executed["output_envelope"]["sections"][1]["section_id"], "risk_focus_points")
        self.assertEqual(executed["output_envelope"]["sections"][0]["metadata"]["entity_count"], 2)
        parent_events = list(sdk.stream_events(parent["run"]["run_id"]))
        execution_events = [event for event in parent_events if event["status_kind"] == "child_executor_executed"]
        self.assertEqual(execution_events[-1]["child_executor_execution"]["execution_status"], "executed")

    def test_execute_bound_child_executor_requires_explicit_executor_binding_opt_in(self):
        sdk = EmbeddedAgentRuntimeSDK()
        parent = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
            "metadata": {"agent_name": "fraud_assistant"},
        })

        binding = sdk.bind_child_executor_routing(
            {
                "input": "复核交易风险",
                "merge_strategy": "append_summary",
                "metadata": {
                    "agent_name": "risk_reviewer",
                    "scheduler_policy": {"timeout_seconds": 45},
                    "worker_runtime_backend": "embedded_sdk_worker",
                    "explicit_executor_binding_opt_in": False,
                },
            },
            parent_run_id=parent["run"]["run_id"],
        )
        execution = sdk.execute_bound_child_executor(
            binding,
            parent_run_id=parent["run"]["run_id"],
        )

        prerequisites = binding["route"]["gate"]["child_executor_execution_prerequisites"]
        self.assertIn("explicit_executor_binding_opt_in", prerequisites["missing_requirements"])
        self.assertEqual(binding["binding_status"], "blocked")
        self.assertEqual(execution["execution_status"], "blocked")
        self.assertFalse(execution["will_execute"])
        self.assertEqual(execution["execution_reason"], "child_executor_preflight_blocked")
        self.assertFalse(execution["explicit_executor_binding"]["ready"])

    def test_merge_child_executor_output_reports_blocked_and_merged_status(self):
        sdk = EmbeddedAgentRuntimeSDK()
        parent = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
            "metadata": {"agent_name": "fraud_assistant"},
        })

        blocked_execution = sdk.execute_bound_child_executor(
            sdk.bind_child_executor_routing(
                {"input": "复核交易风险"},
                parent_run_id=parent["run"]["run_id"],
            ),
            parent_run_id=parent["run"]["run_id"],
        )
        blocked_merge = sdk.merge_child_executor_output(
            blocked_execution,
            parent_run_id=parent["run"]["run_id"],
        )
        self.assertEqual(blocked_merge["merge_status"], "blocked")
        self.assertFalse(blocked_merge["merge_ready"])

        executed = sdk.execute_bound_child_executor(
            sdk.bind_child_executor_routing(
                {
                    "input": "复核交易风险",
                    "merge_strategy": "append_summary",
                    "metadata": {
                        "agent_name": "risk_reviewer",
                        "scheduler_policy": {"timeout_seconds": 45},
                        "worker_runtime_backend": "embedded_sdk_worker",
                    "explicit_executor_binding_opt_in": True,
                    },
                },
                parent_run_id=parent["run"]["run_id"],
            ),
            parent_run_id=parent["run"]["run_id"],
        )
        merged = sdk.merge_child_executor_output(
            executed,
            parent_run_id=parent["run"]["run_id"],
        )
        self.assertEqual(merged["merge_status"], "merged")
        self.assertTrue(merged["merge_ready"])
        self.assertEqual(merged["merge_strategy"], "append_summary")
        self.assertIn("risk_reviewer", merged["merged_summary"])
        self.assertIn("风险复核结论", merged["merged_output"])
        self.assertEqual(merged["section_count"], 3)
        parent_events = list(sdk.stream_events(parent["run"]["run_id"]))
        merge_events = [event for event in parent_events if event["status_kind"] == "child_executor_output_merged"]
        self.assertEqual(merge_events[-1]["child_executor_merge"]["merge_status"], "merged")

    def test_merge_child_executor_output_supports_role_sections_strategy(self):
        sdk = EmbeddedAgentRuntimeSDK()
        parent = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
            "metadata": {"agent_name": "fraud_assistant"},
        })

        executed = sdk.execute_bound_child_executor(
            sdk.bind_child_executor_routing(
                {
                    "input": "复核交易风险",
                    "merge_strategy": "role_sections",
                    "metadata": {
                        "agent_name": "risk_reviewer",
                        "scheduler_policy": {"timeout_seconds": 45},
                        "worker_runtime_backend": "embedded_sdk_worker",
                    "explicit_executor_binding_opt_in": True,
                    },
                },
                parent_run_id=parent["run"]["run_id"],
            ),
            parent_run_id=parent["run"]["run_id"],
        )
        merged = sdk.merge_child_executor_output(
            executed,
            parent_run_id=parent["run"]["run_id"],
        )

        self.assertEqual(merged["merge_status"], "merged")
        self.assertEqual(merged["merge_strategy"], "role_sections")
        self.assertIn("[risk_reviewer 已完成风险复核]", merged["merged_output"])
        self.assertIn("风险复核结论", merged["merged_output"])

    def test_execute_bound_child_executor_supports_planning_intent_structure(self):
        sdk = EmbeddedAgentRuntimeSDK()
        parent = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
            "metadata": {"agent_name": "fraud_assistant"},
        })

        executed = sdk.execute_bound_child_executor(
            sdk.bind_child_executor_routing(
                {
                    "input": "生成巡检计划",
                    "merge_strategy": "append_summary",
                    "metadata": {
                        "agent_name": "planner_agent",
                        "scheduler_policy": {"timeout_seconds": 45},
                        "worker_runtime_backend": "embedded_sdk_worker",
                    "explicit_executor_binding_opt_in": True,
                    },
                },
                parent_run_id=parent["run"]["run_id"],
            ),
            parent_run_id=parent["run"]["run_id"],
        )

        self.assertEqual(executed["output_payload"]["intent_label"], "planning")
        self.assertEqual(executed["output_payload"]["business_result"]["result_type"], "plan_outline")
        self.assertIn("巡检", executed["output_payload"]["entities"])
        self.assertGreaterEqual(len(executed["output_payload"]["focus_points"]), 3)
        self.assertEqual(len(executed["output_envelope"]["sections"]), 3)
        self.assertIn("计划提纲", executed["output_text"])

    def test_execute_bound_child_executor_supports_general_analysis_semantics(self):
        sdk = EmbeddedAgentRuntimeSDK()
        parent = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
            "metadata": {"agent_name": "fraud_assistant"},
        })

        executed = sdk.execute_bound_child_executor(
            sdk.bind_child_executor_routing(
                {
                    "input": "整理合并摘要并补充结果报告",
                    "merge_strategy": "append_summary",
                    "metadata": {
                        "agent_name": "analysis_agent",
                        "scheduler_policy": {"timeout_seconds": 45},
                        "worker_runtime_backend": "embedded_sdk_worker",
                    "explicit_executor_binding_opt_in": True,
                    },
                },
                parent_run_id=parent["run"]["run_id"],
            ),
            parent_run_id=parent["run"]["run_id"],
        )

        self.assertEqual(executed["output_payload"]["intent_label"], "general_analysis")
        self.assertEqual(executed["output_payload"]["business_result"]["result_type"], "analysis_summary")
        self.assertIn("合并", executed["output_payload"]["entities"])
        self.assertEqual(len(executed["output_envelope"]["sections"]), 2)
        self.assertEqual(executed["output_envelope"]["sections"][1]["section_id"], "analysis_actions")

    def test_list_child_executor_outputs_replays_execution_and_merge_records(self):
        sdk = EmbeddedAgentRuntimeSDK()
        parent = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
            "metadata": {"agent_name": "fraud_assistant"},
        })
        merged = sdk.merge_child_executor_output(
            sdk.execute_bound_child_executor(
                sdk.bind_child_executor_routing(
                    {
                        "input": "复核交易风险",
                        "merge_strategy": "append_summary",
                        "metadata": {
                            "agent_name": "risk_reviewer",
                            "scheduler_policy": {"timeout_seconds": 45},
                            "worker_runtime_backend": "embedded_sdk_worker",
                    "explicit_executor_binding_opt_in": True,
                        },
                    },
                    parent_run_id=parent["run"]["run_id"],
                ),
                parent_run_id=parent["run"]["run_id"],
            ),
            parent_run_id=parent["run"]["run_id"],
        )

        replay = sdk.list_child_executor_outputs(parent["run"]["run_id"])

        self.assertEqual(replay["contract_version"], "phase-ii-child-executor-replay-v1")
        self.assertEqual(replay["record_count"], 1)
        self.assertEqual(replay["records"][0]["execution_status"], "executed")
        self.assertEqual(replay["records"][0]["result_type"], "risk_assessment")
        self.assertIn("交易", replay["records"][0]["entities"])
        self.assertGreaterEqual(len(replay["records"][0]["focus_points"]), 3)
        self.assertEqual(replay["records"][0]["merge_status"], "merged")
        self.assertEqual(replay["records"][0]["merge_behavior"]["entities"], "append_dedup")
        self.assertEqual(replay["records"][0]["merged_semantics"]["intent_label"], "risk_review")
        self.assertIn("risk_reviewer", replay["latest_merged_summary"])
        self.assertEqual(replay["latest_merged_output"], merged["merged_output"])

    def test_summarize_child_executor_outputs_returns_compact_artifact_summary(self):
        sdk = EmbeddedAgentRuntimeSDK()
        parent = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
            "metadata": {"agent_name": "fraud_assistant"},
        })
        merged = sdk.merge_child_executor_output(
            sdk.execute_bound_child_executor(
                sdk.bind_child_executor_routing(
                    {
                        "input": "复核交易风险",
                        "merge_strategy": "append_summary",
                        "metadata": {
                            "agent_name": "risk_reviewer",
                            "scheduler_policy": {"timeout_seconds": 45},
                            "worker_runtime_backend": "embedded_sdk_worker",
                    "explicit_executor_binding_opt_in": True,
                        },
                    },
                    parent_run_id=parent["run"]["run_id"],
                ),
                parent_run_id=parent["run"]["run_id"],
            ),
            parent_run_id=parent["run"]["run_id"],
        )

        summary = sdk.summarize_child_executor_outputs(parent["run"]["run_id"])

        self.assertEqual(summary["contract_version"], "phase-ii-child-executor-artifact-summary-v1")
        self.assertEqual(summary["record_count"], 1)
        self.assertEqual(summary["latest_merge_strategy"], "append_summary")
        self.assertEqual(summary["latest_result_type"], "risk_assessment")
        self.assertIn("人工复核关键风险点", summary["latest_conclusion"])
        self.assertIn("交易", summary["latest_entities"])
        self.assertGreaterEqual(len(summary["latest_focus_points"]), 3)
        self.assertGreaterEqual(len(summary["latest_action_items"]), 3)
        self.assertEqual(summary["latest_merged_semantics"]["merge_behavior"]["entities"], "append_dedup")
        self.assertEqual(summary["latest_merged_output"], merged["merged_output"])
        self.assertIn("child-output:", summary["latest_artifact_id"])
        self.assertEqual(len(summary["artifact_ids"]), 1)

    def test_summarize_child_executor_merged_semantics_returns_catalog_and_sections(self):
        sdk = EmbeddedAgentRuntimeSDK()
        parent = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
            "metadata": {"agent_name": "fraud_assistant"},
        })
        sdk.merge_child_executor_output(
            sdk.execute_bound_child_executor(
                sdk.bind_child_executor_routing(
                    {
                        "input": "复核交易风险",
                        "merge_strategy": "append_summary",
                        "metadata": {
                            "agent_name": "risk_reviewer",
                            "scheduler_policy": {"timeout_seconds": 45},
                            "worker_runtime_backend": "embedded_sdk_worker",
                    "explicit_executor_binding_opt_in": True,
                        },
                    },
                    parent_run_id=parent["run"]["run_id"],
                ),
                parent_run_id=parent["run"]["run_id"],
            ),
            parent_run_id=parent["run"]["run_id"],
        )

        merged_semantics = sdk.summarize_child_executor_merged_semantics(parent["run"]["run_id"])

        self.assertEqual(merged_semantics["contract_version"], "phase-ii-child-executor-merged-semantics-v2")
        self.assertEqual(merged_semantics["intent_catalog_version"], "phase-ii-child-intent-catalog-v1")
        self.assertEqual(merged_semantics["supported_intents"], ["risk_review", "planning", "general_analysis"])
        self.assertEqual(merged_semantics["intent_label"], "risk_review")
        self.assertEqual(merged_semantics["parent_state_surface"]["intent_label"], "risk_review")
        self.assertEqual(merged_semantics["parent_state_surface"]["entity_count"], 2)
        self.assertIn("交易", merged_semantics["parent_state_surface"]["primary_entities"])
        self.assertEqual(merged_semantics["parent_state_surface"]["section_source"], "merged_sections")
        self.assertEqual(
            merged_semantics["parent_state_surface"]["section_ids"],
            ["merged_entities", "merged_focus", "merged_actions", "latest_conclusion"],
        )
        self.assertEqual(
            merged_semantics["parent_state_surface"]["section_counts"]["merged_entities"],
            merged_semantics["parent_state_surface"]["entity_count"],
        )
        self.assertEqual(
            merged_semantics["parent_state_surface"]["section_counts"]["merged_focus"],
            merged_semantics["parent_state_surface"]["focus_count"],
        )
        self.assertEqual(merged_semantics["merged_sections"]["merged_entities"]["merge_mode"], "append_dedup")
        self.assertEqual(merged_semantics["merged_sections"]["merged_entities"]["section_kind"], "list")
        self.assertEqual(merged_semantics["merged_sections"]["merged_entities"]["item_count"], 2)
        self.assertIn("交易", merged_semantics["merged_sections"]["merged_entities"]["items"])
        self.assertEqual(merged_semantics["merged_sections"]["latest_conclusion"]["merge_mode"], "replace_latest")
        self.assertEqual(merged_semantics["merged_sections"]["latest_conclusion"]["section_kind"], "text")
        self.assertGreater(merged_semantics["merged_sections"]["latest_conclusion"]["text_length"], 0)
        self.assertIn("人工复核关键风险点", merged_semantics["merged_sections"]["latest_conclusion"]["text"])

    def test_merge_child_executor_output_applies_intent_aware_merge_behavior(self):
        sdk = EmbeddedAgentRuntimeSDK()
        parent = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
            "metadata": {"agent_name": "fraud_assistant"},
        })

        risk_merge = sdk.merge_child_executor_output(
            sdk.execute_bound_child_executor(
                sdk.bind_child_executor_routing(
                    {
                        "input": "复核交易风险",
                        "merge_strategy": "append_summary",
                        "metadata": {
                            "agent_name": "risk_reviewer",
                            "scheduler_policy": {"timeout_seconds": 45},
                            "worker_runtime_backend": "embedded_sdk_worker",
                    "explicit_executor_binding_opt_in": True,
                        },
                    },
                    parent_run_id=parent["run"]["run_id"],
                ),
                parent_run_id=parent["run"]["run_id"],
            ),
            parent_run_id=parent["run"]["run_id"],
        )
        planning_merge = sdk.merge_child_executor_output(
            sdk.execute_bound_child_executor(
                sdk.bind_child_executor_routing(
                    {
                        "input": "制定巡检计划并明确执行顺序",
                        "merge_strategy": "append_summary",
                        "metadata": {
                            "agent_name": "planning_agent",
                            "scheduler_policy": {"timeout_seconds": 45},
                            "worker_runtime_backend": "embedded_sdk_worker",
                    "explicit_executor_binding_opt_in": True,
                        },
                    },
                    parent_run_id=parent["run"]["run_id"],
                ),
                parent_run_id=parent["run"]["run_id"],
            ),
            parent_run_id=parent["run"]["run_id"],
        )
        analysis_merge = sdk.merge_child_executor_output(
            sdk.execute_bound_child_executor(
                sdk.bind_child_executor_routing(
                    {
                        "input": "整理合并摘要并补充结果报告",
                        "merge_strategy": "append_summary",
                        "metadata": {
                            "agent_name": "analysis_agent",
                            "scheduler_policy": {"timeout_seconds": 45},
                            "worker_runtime_backend": "embedded_sdk_worker",
                    "explicit_executor_binding_opt_in": True,
                        },
                    },
                    parent_run_id=parent["run"]["run_id"],
                ),
                parent_run_id=parent["run"]["run_id"],
            ),
            parent_run_id=parent["run"]["run_id"],
        )

        self.assertEqual(risk_merge["merged_semantics"]["merge_behavior"]["focus_points"], "append_dedup")
        self.assertEqual(planning_merge["merged_semantics"]["merge_behavior"]["focus_points"], "replace_latest")
        self.assertEqual(analysis_merge["merged_semantics"]["merge_behavior"]["focus_points"], "summary_only")

        parent_run = sdk._runs[parent["run"]["run_id"]].snapshot()
        merged_semantics = parent_run["metadata"]["child_executor_merged_semantics"]
        self.assertEqual(merged_semantics["intent_label"], "general_analysis")
        self.assertIn("交易", merged_semantics["entities"])
        self.assertGreaterEqual(len(merged_semantics["action_items"]), 1)
        self.assertEqual(merged_semantics["merge_behavior"]["action_items"], "summary_only")

    def test_delegate_run_promotes_preflight_when_budget_merge_and_backend_are_defined(self):
        sdk = EmbeddedAgentRuntimeSDK()
        parent = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
            "metadata": {"agent_name": "fraud_assistant"},
        })

        child = sdk.delegate_run(parent["run"]["run_id"], {
            "input": "复核交易风险",
            "merge_strategy": "append_summary",
            "metadata": {
                "agent_name": "risk_reviewer",
                "scheduler_policy": {"timeout_seconds": 45},
                "worker_runtime_backend": "embedded_sdk_worker",
                    "explicit_executor_binding_opt_in": True,
            },
        })

        preflight = child["child_executor_preflight"]
        self.assertEqual(preflight["status"], "promotion_candidate")
        self.assertTrue(preflight["promotion_ready"])
        self.assertFalse(preflight["real_child_executor_ready"])
        self.assertEqual(preflight["missing_requirements"], [])
        checks = {item["requirement"]: item for item in preflight["requirement_checks"]}
        self.assertTrue(checks["child_run_recovery_boundary_defined"]["satisfied"])
        self.assertEqual(
            checks["child_context_budget_defined"]["source_path"],
            "metadata.scheduler_policy.timeout_seconds",
        )
        self.assertEqual(
            checks["child_result_merge_semantics_defined"]["source_path"],
            "payload.merge_strategy",
        )
        self.assertEqual(
            checks["worker_runtime_backend_selected"]["source_path"],
            "metadata.worker_runtime_backend",
        )

    def test_create_artifact_records_run_metadata_and_event(self):
        sdk = EmbeddedAgentRuntimeSDK()
        result = sdk.create_run({
            "conversation_id": 42,
            "run_kind": "chat",
        })
        run_id = result["run"]["run_id"]

        artifact_result = sdk.create_artifact(run_id, {
            "kind": "assessment_report",
            "content": "风险评分：高",
            "metadata": {"case_id": "case-1"},
        })

        artifact = artifact_result["artifact"]
        self.assertEqual(artifact["kind"], "assessment_report")
        self.assertEqual(artifact["content"], "风险评分：高")
        self.assertEqual(artifact["run_id"], run_id)
        self.assertEqual(artifact["conversation_id"], 42)
        self.assertEqual(artifact["metadata"]["case_id"], "case-1")
        self.assertTrue(artifact["artifact_id"].startswith("art_"))
        self.assertTrue(artifact["uri"].startswith("memory://runs/"))

        run = artifact_result["run"]
        self.assertEqual(run["metadata"]["artifacts"][0]["artifact_id"], artifact["artifact_id"])
        events = list(sdk.stream_events(run_id))
        self.assertTrue(any(event["status_kind"] == "artifact_created" for event in events))
        artifact_event = next(event for event in events if event["status_kind"] == "artifact_created")
        self.assertEqual(artifact_event["artifact"]["artifact_id"], artifact["artifact_id"])

    def test_create_artifact_can_use_injected_artifact_store(self):
        store = InMemoryArtifactStore()
        sdk = EmbeddedAgentRuntimeSDK(artifact_store=store)
        result = sdk.create_run({
            "conversation_id": 42,
            "run_kind": "chat",
        })
        run_id = result["run"]["run_id"]

        artifact_result = sdk.create_artifact(run_id, {
            "kind": "assessment_report",
            "content": "风险评分：高",
            "render_mode": "markdown",
            "metadata": {"case_id": "case-1"},
        })

        stored = store.list_artifacts(conversation_id=42, kind="assessment_report")
        artifact = artifact_result["artifact"]
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0].artifact_id, artifact["artifact_id"])
        self.assertEqual(stored[0].content, "风险评分：高")
        self.assertEqual(stored[0].render_mode, "markdown")
        self.assertEqual(artifact["uri"], f"artifact://{stored[0].artifact_id}")
        self.assertEqual(artifact["metadata"]["case_id"], "case-1")

    def test_list_artifacts_replays_run_artifacts_in_creation_order(self):
        sdk = EmbeddedAgentRuntimeSDK()
        result = sdk.create_run({
            "conversation_id": 42,
            "run_kind": "chat",
        })
        run_id = result["run"]["run_id"]
        first = sdk.create_artifact(run_id, {
            "kind": "assessment_report",
            "content": "风险评分：高",
        })["artifact"]
        second = sdk.create_artifact(run_id, {
            "kind": "evidence",
            "content": "命中黑名单手机号",
        })["artifact"]

        replay = sdk.list_artifacts(run_id)

        self.assertEqual(replay["run"]["run_id"], run_id)
        self.assertEqual(
            [artifact["artifact_id"] for artifact in replay["artifacts"]],
            [first["artifact_id"], second["artifact_id"]],
        )
        self.assertEqual(replay["artifacts"][1]["kind"], "evidence")
        self.assertEqual(replay["artifacts"][1]["content"], "命中黑名单手机号")

    def test_execute_run_uses_minimal_execution_loop_and_appends_events(self):
        sdk = EmbeddedAgentRuntimeSDK()
        result = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
        })

        executed = sdk.execute_run(result["run"]["run_id"])

        self.assertEqual(executed["run"]["state"], "done")
        self.assertEqual(executed["run"]["iteration"], 1)
        self.assertEqual(executed["run"]["stop_reason"], "loop_completed")
        self.assertEqual(executed["run"]["metadata"]["execution_loop"]["controller"], "minimal")
        events = list(sdk.stream_events(result["run"]["run_id"]))
        self.assertEqual(events[0]["status_kind"], "run_created")
        self.assertTrue(any(event["status_kind"] == "execution_loop_step" for event in events))
        self.assertEqual(events[-1]["type"], "done")
        self.assertEqual(events[-1]["status_kind"], "execution_loop_done")

    def test_execute_run_records_query_control_lifecycle_when_recorder_is_injected(self):
        query_control_timeline = _StubQueryControlTimelineService()
        sdk = EmbeddedAgentRuntimeSDK(
            query_control_db=object(),
            query_control_timeline_service=query_control_timeline,
        )
        result = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
        })

        sdk.execute_run(result["run"]["run_id"])

        stages = [call["stage"] for call in query_control_timeline.calls]
        self.assertIn("input_received", stages)
        self.assertIn("planning", stages)
        self.assertIn("model_stream", stages)
        self.assertIn("observation", stages)
        self.assertIn("review", stages)
        self.assertIn("final_output", stages)
        first_call = query_control_timeline.calls[0]
        self.assertEqual(first_call["channel"], "embedded_sdk")
        self.assertEqual(first_call["conversation_id"], 42)
        self.assertEqual(first_call["query_id"], result["run"]["run_id"])
        self.assertEqual(first_call["payload"]["source_status_kind"], "run_created")

    def test_delegate_run_records_subagent_query_control_lifecycle_when_recorder_is_injected(self):
        query_control_timeline = _StubQueryControlTimelineService()
        sdk = EmbeddedAgentRuntimeSDK(
            query_control_db=object(),
            query_control_timeline_service=query_control_timeline,
        )
        parent = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
        })

        sdk.delegate_run(parent["run"]["run_id"], {
            "input": "复核交易风险",
            "metadata": {"agent_name": "risk_reviewer"},
        })

        subagent_calls = [
            call for call in query_control_timeline.calls if call["channel"] == "subagent_lane"
        ]
        self.assertEqual(len(subagent_calls), 1)
        self.assertEqual(subagent_calls[0]["stage"], "input_received")
        self.assertEqual(subagent_calls[0]["conversation_id"], 42)
        self.assertEqual(subagent_calls[0]["query_id"], parent["run"]["run_id"])
        self.assertEqual(subagent_calls[0]["payload"]["source_status_kind"], "child_run_created")

    def test_query_control_recording_failure_does_not_break_sdk_execution(self):
        sdk = EmbeddedAgentRuntimeSDK(
            query_control_db=object(),
            query_control_timeline_service=_FailingQueryControlTimelineService(),
        )
        result = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
        })

        executed = sdk.execute_run(result["run"]["run_id"])

        self.assertEqual(executed["run"]["state"], "done")
        self.assertTrue(any(event["status_kind"] == "execution_loop_done" for event in executed["events"]))

    def test_execute_run_creates_formal_approval_when_tool_policy_requires_it(self):
        sdk = EmbeddedAgentRuntimeSDK()
        result = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
            "metadata": {"agent_role": "fraud_assistant"},
        })

        executed = sdk.execute_run(
            result["run"]["run_id"],
            tool_policy=lambda _run: {
                "status": "approval_required",
                "tool_name": "filesystem_write",
                "tool_args": {"path": "case.md"},
                "reason": "高风险写文件工具需要人工审批",
                "metadata": {
                    "permission_level": "ask",
                    "reason_code": "high_risk_tool_requires_approval",
                    "request_metadata": {"policy": "high_risk_tool_requires_approval"},
                },
            },
            tool_executor=lambda _run: {
                "tool_name": "filesystem_write",
                "result": "不应该执行",
            },
        )

        self.assertEqual(executed["run"]["metadata"]["loop_continuation"]["status"], "pending")
        self.assertEqual(executed["run"]["metadata"]["loop_continuation"]["resume_mode"], "observing_to_done")

        approval = executed["approval_request"]
        self.assertEqual(executed["run"]["state"], "waiting_approval")
        self.assertEqual(executed["run"]["metadata"]["approval_request_id"], approval["request_id"])
        self.assertEqual(executed["run"]["metadata"]["approval_request"], approval)
        self.assertEqual(approval["request_kind"], "tool_permission")
        self.assertEqual(approval["tool_name"], "filesystem_write")
        self.assertEqual(approval["tool_args"], {"path": "case.md"})
        self.assertEqual(approval["status"], "pending")
        self.assertEqual(approval["reason_code"], "high_risk_tool_requires_approval")
        self.assertEqual(approval["conversation_id"], 42)
        self.assertEqual(approval["user_id"], 7)
        self.assertEqual(approval["run_id"], result["run"]["run_id"])

        events = list(sdk.stream_events(result["run"]["run_id"]))
        approval_event = next(event for event in events if event["status_kind"] == "approval_created")
        self.assertEqual(approval_event["approval_request_id"], approval["request_id"])
        self.assertEqual(approval_event["approval_request"]["tool_name"], "filesystem_write")
        continuation_event = next(event for event in events if event["status_kind"] == "loop_continuation_registered")
        self.assertEqual(continuation_event["loop_continuation"]["status"], "pending")
        self.assertEqual(continuation_event["loop_continuation"]["resume_mode"], "observing_to_done")
        self.assertTrue(any(event["type"] == "tool_permission_required" for event in events))
        self.assertFalse(any(event["type"] == "tool_result" for event in events))

    def test_submit_approval_resumes_pending_tool_execution_when_approved(self):
        sdk = EmbeddedAgentRuntimeSDK()
        result = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
        })

        executed = sdk.execute_run(
            result["run"]["run_id"],
            tool_policy=lambda _run: {
                "status": "approval_required",
                "tool_name": "filesystem_write",
                "tool_args": {"path": "case.md"},
                "reason": "高风险写文件工具需要人工审批",
            },
            tool_executor=lambda _run: {
                "tool_name": "filesystem_write",
                "args": {"path": "case.md"},
                "result": "写入成功",
                "tool_call_id": "tool-after-approval",
                "execution": {"status": "success"},
            },
        )

        submitted = sdk.submit_approval(executed["approval_request"]["request_id"], "approved")

        self.assertEqual(submitted["approval_request"]["status"], "approved")
        self.assertEqual(submitted["run"]["state"], "observing")
        self.assertEqual(submitted["run"]["stop_reason"], "approval_approved")
        self.assertEqual(submitted["run"]["tool_history"][0]["tool_name"], "filesystem_write")
        self.assertEqual(submitted["run"]["tool_history"][0]["result"], "写入成功")
        self.assertEqual(submitted["run"]["metadata"]["tool_approval_continuation"]["status"], "consumed")

        events = list(sdk.stream_events(result["run"]["run_id"]))
        self.assertTrue(any(event["status_kind"] == "tool_approval_continued" for event in events))
        self.assertTrue(any(event["type"] == "tool_call_start" for event in events))
        self.assertTrue(any(event["type"] == "tool_result" for event in events))

    def test_resolved_approved_approval_ignores_later_denial(self):
        sdk = EmbeddedAgentRuntimeSDK()
        result = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
        })

        executed = sdk.execute_run(
            result["run"]["run_id"],
            tool_policy=lambda _run: {
                "status": "approval_required",
                "tool_name": "filesystem_write",
                "tool_args": {"path": "case.md"},
                "reason": "高风险写文件工具需要人工审批",
            },
            tool_executor=lambda _run: {
                "tool_name": "filesystem_write",
                "args": {"path": "case.md"},
                "result": "写入成功",
                "tool_call_id": "tool-after-approval",
                "execution": {"status": "success"},
            },
        )

        approved = sdk.submit_approval(executed["approval_request"]["request_id"], "approved")
        replay = sdk.submit_approval(executed["approval_request"]["request_id"], "denied")

        self.assertEqual(approved["approval_request"]["status"], "approved")
        self.assertEqual(replay["approval_request"]["status"], "approved")
        self.assertEqual(replay["approval_submission"]["status"], "ignored")
        self.assertEqual(replay["approval_submission"]["reason"], "approval_already_resolved")
        self.assertEqual(replay["approval_submission"]["original_decision"], "approved")
        self.assertEqual(replay["approval_submission"]["attempted_decision"], "denied")
        self.assertEqual(len(replay["run"]["tool_history"]), 1)
        self.assertEqual(replay["run"]["metadata"]["tool_approval_continuation"]["status"], "consumed")
        events = list(sdk.stream_events(result["run"]["run_id"]))
        ignored_event = next(event for event in events if event["status_kind"] == "approval_ignored")
        self.assertEqual(ignored_event["original_decision"], "approved")
        self.assertEqual(ignored_event["attempted_decision"], "denied")
        self.assertEqual(len([event for event in events if event["type"] == "tool_result"]), 1)
        probe = sdk.probe_run_recovery(result["run"]["run_id"])
        self.assertEqual(probe["checkpoint"]["status"], "stale")
        self.assertEqual(probe["checkpoint"]["recovery_reason"], "already_resolved")
        self.assertEqual(probe["resume_cursor"]["cursor_status"], "stale")
        self.assertEqual(probe["resume_cursor"]["recovery_reason"], "already_resolved")

    def test_resume_run_can_continue_loop_after_approved_tool_execution(self):
        sdk = EmbeddedAgentRuntimeSDK()
        result = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
        })

        executed = sdk.execute_run(
            result["run"]["run_id"],
            tool_policy=lambda _run: {
                "status": "approval_required",
                "tool_name": "filesystem_write",
                "tool_args": {"path": "case.md"},
                "reason": "高风险写文件工具需要人工审批",
            },
            tool_executor=lambda _run: {
                "tool_name": "filesystem_write",
                "args": {"path": "case.md"},
                "result": "写入成功",
            },
            reviewer=lambda _run: {
                "reviewer": "quality_gate",
                "status": "approved",
                "summary": "工具结果可接受",
            },
        )
        sdk.submit_approval(executed["approval_request"]["request_id"], "approved")

        resumed = sdk.resume_run(result["run"]["run_id"], continue_loop=True)

        self.assertEqual(resumed["run"]["state"], "done")
        self.assertEqual(resumed["run"]["metadata"]["loop_continuation"]["status"], "consumed")
        self.assertEqual(resumed["run"]["metadata"]["loop_continuation"]["resume_mode"], "observing_to_done")
        self.assertEqual(resumed["run"]["metadata"]["execution_review"]["status"], "approved")
        self.assertEqual(resumed["run"]["metadata"]["execution_loop"]["completed"], True)
        events = list(sdk.stream_events(result["run"]["run_id"]))
        self.assertTrue(any(event["status_kind"] == "execution_loop_reviewed" for event in events))
        consumed_event = next(event for event in events if event["status_kind"] == "loop_continuation_consumed")
        self.assertEqual(consumed_event["loop_continuation"]["status"], "consumed")
        self.assertEqual(events[-1]["status_kind"], "execution_loop_done")

    def test_denied_approval_discards_pending_tool_continuation(self):
        sdk = EmbeddedAgentRuntimeSDK()
        result = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
        })

        executed = sdk.execute_run(
            result["run"]["run_id"],
            tool_policy=lambda _run: {
                "status": "approval_required",
                "tool_name": "filesystem_write",
                "tool_args": {"path": "case.md"},
                "reason": "高风险写文件工具需要人工审批",
            },
            tool_executor=lambda _run: {
                "tool_name": "filesystem_write",
                "args": {"path": "case.md"},
                "result": "不应该执行",
            },
        )

        denied = sdk.submit_approval(executed["approval_request"]["request_id"], "denied")
        replay = sdk.submit_approval(executed["approval_request"]["request_id"], "approved")

        self.assertEqual(denied["approval_request"]["status"], "denied")
        self.assertEqual(replay["approval_request"]["status"], "denied")
        self.assertEqual(replay["approval_submission"]["status"], "ignored")
        self.assertEqual(replay["approval_submission"]["reason"], "approval_already_resolved")
        self.assertEqual(replay["approval_submission"]["original_decision"], "denied")
        self.assertEqual(replay["approval_submission"]["attempted_decision"], "approved")
        self.assertEqual(replay["run"]["tool_history"], [])
        self.assertEqual(replay["run"]["metadata"]["tool_approval_continuation"]["status"], "discarded")
        self.assertEqual(replay["run"]["metadata"]["loop_continuation"]["status"], "discarded")
        self.assertEqual(replay["run"]["metadata"]["loop_continuation"]["decision"], "denied")
        discarded_event = next(
            event
            for event in sdk.stream_events(result["run"]["run_id"])
            if event["status_kind"] == "loop_continuation_discarded"
        )
        self.assertEqual(discarded_event["loop_continuation"]["status"], "discarded")
        ignored_event = next(
            event
            for event in sdk.stream_events(result["run"]["run_id"])
            if event["status_kind"] == "approval_ignored"
        )
        self.assertEqual(ignored_event["original_decision"], "denied")
        self.assertEqual(ignored_event["attempted_decision"], "approved")
        self.assertFalse(any(event["type"] == "tool_result" for event in sdk.stream_events(result["run"]["run_id"])))

    def test_probe_run_recovery_blocks_approval_resume_when_approval_is_resolved(self):
        sdk = EmbeddedAgentRuntimeSDK()
        result = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
        })
        executed = sdk.execute_run(
            result["run"]["run_id"],
            tool_policy=lambda _run: {
                "status": "approval_required",
                "tool_name": "filesystem_write",
                "tool_args": {"path": "case.md"},
                "reason": "高风险写文件工具需要人工审批",
            },
            tool_executor=lambda _run: {
                "tool_name": "filesystem_write",
                "args": {"path": "case.md"},
                "result": "不应该执行",
            },
        )
        sdk.submit_approval(executed["approval_request"]["request_id"], "denied")

        probe = sdk.probe_run_recovery(result["run"]["run_id"])

        self.assertEqual(probe["approval_request"]["status"], "denied")
        self.assertEqual(probe["checkpoint"]["status"], "stale")
        self.assertEqual(probe["checkpoint"]["recovery_reason"], "denied")
        self.assertEqual(probe["resume_cursor"]["cursor_status"], "stale")
        self.assertEqual(probe["resume_cursor"]["recovery_reason"], "denied")
        probe_entrypoints = {
            (item["method"], item.get("mode") or ""): item
            for item in probe["recovery_entrypoints"]
        }
        approval_entry = probe_entrypoints[("submit_approval", "approved")]
        self.assertFalse(approval_entry["available"])
        self.assertEqual(approval_entry["blocked_reason"], "approval_already_resolved")
        self.assertEqual(approval_entry["recovery_reason"], "already_resolved")
        self.assertEqual(approval_entry["approval_status"], "denied")

    def test_denied_approval_in_new_process_discards_persisted_continuation_descriptors(self):
        store = _DurableTestWorkspaceStore()
        registry = InMemoryEmbeddedContinuationRegistry()

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
            tool_executor=lambda _run: {
                "tool_name": "filesystem_write",
                "args": {"path": "case.md"},
                "result": "不应该执行",
            },
        )

        reader = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)
        denied = reader.submit_approval(executed["approval_request"]["request_id"], "denied")
        replay = reader.submit_approval(executed["approval_request"]["request_id"], "approved")

        self.assertEqual(denied["approval_request"]["status"], "denied")
        self.assertEqual(replay["approval_request"]["status"], "denied")
        self.assertEqual(replay["approval_submission"]["status"], "ignored")
        self.assertEqual(replay["approval_submission"]["reason"], "approval_already_resolved")
        self.assertEqual(replay["approval_submission"]["original_decision"], "denied")
        self.assertEqual(replay["approval_submission"]["attempted_decision"], "approved")
        self.assertEqual(replay["run"]["tool_history"], [])
        self.assertEqual(replay["run"]["metadata"]["tool_approval_continuation"]["status"], "discarded")
        self.assertEqual(replay["run"]["metadata"]["loop_continuation"]["status"], "discarded")
        self.assertEqual(replay["run"]["metadata"]["loop_continuation"]["decision"], "denied")
        self.assertIsNone(store.get_tool_continuation_descriptor(executed["approval_request"]["request_id"]))
        self.assertIsNone(store.get_loop_continuation_descriptor(result["run"]["run_id"]))
        discarded_event = next(
            event
            for event in reader.stream_events(result["run"]["run_id"])
            if event["status_kind"] == "loop_continuation_discarded"
        )
        self.assertEqual(discarded_event["loop_continuation"]["status"], "discarded")
        ignored_event = next(
            event
            for event in reader.stream_events(result["run"]["run_id"])
            if event["status_kind"] == "approval_ignored"
        )
        self.assertEqual(ignored_event["original_decision"], "denied")
        self.assertEqual(ignored_event["attempted_decision"], "approved")
        self.assertFalse(any(event["type"] == "tool_result" for event in reader.stream_events(result["run"]["run_id"])))

    def test_workspace_store_persists_run_approval_and_continuation_descriptors(self):
        store = InMemoryEmbeddedRunWorkspaceStore()
        sdk = EmbeddedAgentRuntimeSDK(workspace_store=store)
        result = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
        })

        executed = sdk.execute_run(
            result["run"]["run_id"],
            tool_policy=lambda _run: {
                "status": "approval_required",
                "tool_name": "filesystem_write",
                "tool_args": {"path": "case.md"},
                "reason": "高风险写文件工具需要人工审批",
            },
            tool_executor=lambda _run: {
                "tool_name": "filesystem_write",
                "args": {"path": "case.md"},
                "result": "写入成功",
            },
        )

        persisted_run = store.get_run_snapshot(result["run"]["run_id"])
        persisted_events = store.get_events(result["run"]["run_id"])
        persisted_approval = store.get_approval_snapshot(executed["approval_request"]["request_id"])
        persisted_tool_continuation = store.get_tool_continuation_descriptor(executed["approval_request"]["request_id"])
        persisted_loop_continuation = store.get_loop_continuation_descriptor(result["run"]["run_id"])

        self.assertEqual(persisted_run["run_id"], result["run"]["run_id"])
        self.assertGreaterEqual(len(persisted_events), 1)
        self.assertEqual(persisted_approval["request_id"], executed["approval_request"]["request_id"])
        self.assertEqual(persisted_tool_continuation["status"], "pending")
        self.assertEqual(persisted_loop_continuation["resume_mode"], "observing_to_done")

    def test_workspace_store_can_rehydrate_run_events_and_approval_but_not_execute_missing_continuation(self):
        store = InMemoryEmbeddedRunWorkspaceStore()
        writer = EmbeddedAgentRuntimeSDK(workspace_store=store)
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
            tool_executor=lambda _run: {
                "tool_name": "filesystem_write",
                "args": {"path": "case.md"},
                "result": "写入成功",
            },
        )

        reader = EmbeddedAgentRuntimeSDK(workspace_store=store)
        events = list(reader.stream_events(result["run"]["run_id"]))
        self.assertTrue(any(event["status_kind"] == "approval_created" for event in events))

        with self.assertRaisesRegex(ValueError, "workspace_backend_not_durable"):
            reader.submit_approval(executed["approval_request"]["request_id"], "approved")

        persisted_run = store.get_run_snapshot(result["run"]["run_id"])
        persisted_tool_continuation = store.get_tool_continuation_descriptor(executed["approval_request"]["request_id"])
        self.assertEqual(
            persisted_run["metadata"]["tool_approval_continuation"]["recovery_reason"],
            "workspace_backend_not_durable",
        )
        self.assertEqual(
            persisted_tool_continuation["recovery_status"],
            "unrecoverable",
        )
        reader_events = list(reader.stream_events(result["run"]["run_id"]))
        failed_event = next(event for event in reader_events if event["status_kind"] == "recovery_failed_closed")
        self.assertEqual(failed_event["recovery"]["recovery_reason"], "workspace_backend_not_durable")
        self.assertEqual(failed_event["recovery_operation"]["operation_status"], "blocked")
        self.assertEqual(failed_event["recovery_operation"]["entrypoint"], "submit_approval.approved")
        self.assertEqual(
            failed_event["recovery_operation"]["persistence_posture"],
            "memory_preview",
        )
        self.assertFalse(failed_event["recovery_operation"]["worker_ownership"]["implemented"])

    def test_submit_approval_fail_closed_records_retry_attempt_evidence(self):
        store = InMemoryEmbeddedRunWorkspaceStore()
        writer = EmbeddedAgentRuntimeSDK(workspace_store=store)
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
            tool_executor=lambda _run: {
                "tool_name": "filesystem_write",
                "args": {"path": "case.md"},
                "result": "写入成功",
            },
        )

        reader = EmbeddedAgentRuntimeSDK(workspace_store=store)
        with self.assertRaisesRegex(ValueError, "workspace_backend_not_durable"):
            reader.submit_approval(
                executed["approval_request"]["request_id"],
                "approved",
                retry_attempt={
                    "attempt_number": 3,
                    "max_attempts": 3,
                    "previous_operation_id": "recovery_operation:run-1:submit:first",
                    "idempotency_key": "recovery:run-1:submit_approval.approved",
                },
            )

        failed_event = next(
            event for event in reader.stream_events(result["run"]["run_id"])
            if event["status_kind"] == "recovery_failed_closed"
        )
        retry = failed_event["recovery_operation"]["retry"]
        self.assertEqual(retry["attempt_number"], 3)
        self.assertEqual(retry["status"], "exhausted")
        self.assertTrue(retry["terminal"])
        self.assertEqual(retry["recovery_reason"], "workspace_backend_not_durable")
        self.assertEqual(retry["idempotency_key"], "recovery:run-1:submit_approval.approved")

        run_recovery = RuntimeRecoveryContractBuilder.build_run_recovery_contract(
            reader.probe_run_recovery(result["run"]["run_id"])
        )
        summary = run_recovery["recovery_audit_summary"]
        self.assertEqual(summary["latest_retry_status"], "exhausted")
        self.assertEqual(summary["latest_retry_terminal_reason"], "workspace_backend_not_durable")

    def test_resume_run_fail_closed_when_only_persisted_loop_continuation_exists(self):
        store = InMemoryEmbeddedRunWorkspaceStore()
        writer = EmbeddedAgentRuntimeSDK(workspace_store=store)
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
            tool_executor=lambda _run: {
                "tool_name": "filesystem_write",
                "args": {"path": "case.md"},
                "result": "写入成功",
            },
        )
        writer.submit_approval(executed["approval_request"]["request_id"], "approved")

        reader = EmbeddedAgentRuntimeSDK(workspace_store=store)
        with self.assertRaisesRegex(ValueError, "workspace_backend_not_durable"):
            reader.resume_run(result["run"]["run_id"], continue_loop=True)

        persisted_run = store.get_run_snapshot(result["run"]["run_id"])
        persisted_loop = store.get_loop_continuation_descriptor(result["run"]["run_id"])
        self.assertEqual(
            persisted_run["metadata"]["loop_continuation"]["recovery_status"],
            "unrecoverable",
        )
        self.assertEqual(
            persisted_loop["recovery_reason"],
            "workspace_backend_not_durable",
        )
        reader_events = list(reader.stream_events(result["run"]["run_id"]))
        failed_event = next(event for event in reader_events if event["status_kind"] == "recovery_failed_closed")
        self.assertEqual(failed_event["recovery"]["continuation_kind"], "loop")
        self.assertEqual(failed_event["recovery_operation"]["operation_status"], "blocked")
        self.assertEqual(failed_event["recovery_operation"]["entrypoint"], "resume_run.continue_loop")

    def test_resume_run_fail_closed_records_retry_attempt_evidence(self):
        store = InMemoryEmbeddedRunWorkspaceStore()
        writer = EmbeddedAgentRuntimeSDK(workspace_store=store)
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
            tool_executor=lambda _run: {
                "tool_name": "filesystem_write",
                "args": {"path": "case.md"},
                "result": "写入成功",
            },
        )
        writer.submit_approval(executed["approval_request"]["request_id"], "approved")

        reader = EmbeddedAgentRuntimeSDK(workspace_store=store)
        with self.assertRaisesRegex(ValueError, "workspace_backend_not_durable"):
            reader.resume_run(
                result["run"]["run_id"],
                continue_loop=True,
                retry_attempt={
                    "attempt_number": 2,
                    "max_attempts": 3,
                    "previous_operation_id": "recovery_operation:run-1:resume:first",
                    "idempotency_key": "recovery:run-1:resume_run.continue_loop",
                },
            )

        failed_event = next(
            event for event in reader.stream_events(result["run"]["run_id"])
            if event["status_kind"] == "recovery_failed_closed"
        )
        retry = failed_event["recovery_operation"]["retry"]
        self.assertEqual(retry["attempt_number"], 2)
        self.assertEqual(retry["status"], "not_retryable")
        self.assertFalse(retry["terminal"])
        self.assertEqual(retry["previous_operation_id"], "recovery_operation:run-1:resume:first")

        run_recovery = RuntimeRecoveryContractBuilder.build_run_recovery_contract(
            reader.probe_run_recovery(result["run"]["run_id"])
        )
        summary = run_recovery["recovery_audit_summary"]
        self.assertEqual(summary["latest_retry_status"], "not_retryable")
        self.assertEqual(summary["latest_retry_terminal_reason"], "")

    def test_probe_run_recovery_reports_recoverable_when_executable_continuation_is_still_in_process(self):
        store = _DurableTestWorkspaceStore()
        registry = InMemoryEmbeddedContinuationRegistry()

        def _tool_executor(_run):
            return {
                "tool_name": "filesystem_write",
                "args": {"path": "case.md"},
                "result": "写入成功",
            }

        registry.register("tool_executor.filesystem_write", _tool_executor)
        sdk = EmbeddedAgentRuntimeSDK(workspace_store=store)
        result = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
        })
        executed = sdk.execute_run(
            result["run"]["run_id"],
            tool_policy=lambda _run: {
                "status": "approval_required",
                "tool_name": "filesystem_write",
                "tool_args": {"path": "case.md"},
                "reason": "高风险写文件工具需要人工审批",
            },
            tool_executor=_tool_executor,
        )

        probe = sdk.probe_run_recovery(result["run"]["run_id"])

        self.assertTrue(probe["recoverable"])
        self.assertEqual(probe["persistence_interface"]["persistence_posture"], "durable_ready")
        self.assertTrue(probe["persistence_interface"]["cross_process_candidate"])
        self.assertEqual(probe["loop_continuation"]["recovery_status"], "recoverable")
        self.assertEqual(probe["tool_continuation"]["recovery_reason"], "ready_in_process")
        self.assertEqual(probe["tool_continuation"]["persistence_interface"]["persistence_posture"], "durable_ready")
        probe_entrypoints = {
            (item["method"], item.get("mode") or ""): item
            for item in probe["recovery_entrypoints"]
        }
        self.assertTrue(probe_entrypoints[("submit_approval", "approved")]["available"])
        self.assertEqual(probe_entrypoints[("submit_approval", "approved")]["recovery_reason"], "ready_in_process")
        self.assertFalse(probe_entrypoints[("resume_run", "continue_loop")]["available"])
        self.assertEqual(probe_entrypoints[("resume_run", "continue_loop")]["blocked_reason"], "run_not_observing")
        self.assertFalse(probe_entrypoints[("resume_run", "default")]["available"])
        self.assertEqual(probe_entrypoints[("resume_run", "default")]["blocked_reason"], "run_not_observing")
        persisted_loop = store.get_loop_continuation_descriptor(result["run"]["run_id"])
        persisted_tool = store.get_tool_continuation_descriptor(executed["approval_request"]["request_id"])
        self.assertEqual(persisted_loop["recovery_status"], "recoverable")
        self.assertEqual(persisted_tool["recovery_reason"], "ready_in_process")
        events = list(sdk.stream_events(result["run"]["run_id"]))
        probe_event = next(event for event in events if event["status_kind"] == "recovery_probe_evaluated")
        self.assertTrue(probe_event["recovery"]["recoverable"])

    def test_probe_run_recovery_durable_ready_without_descriptor_still_fails_closed(self):
        store = _DurableTestWorkspaceStore()
        sdk = EmbeddedAgentRuntimeSDK(workspace_store=store)
        result = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
        })

        probe = sdk.probe_run_recovery(result["run"]["run_id"])

        self.assertFalse(probe["recoverable"])
        self.assertEqual(probe["persistence_interface"]["persistence_posture"], "durable_ready")
        self.assertEqual(probe["checkpoint"]["status"], "missing")
        self.assertEqual(probe["checkpoint"]["recovery_reason"], "descriptor_missing")
        self.assertEqual(probe["resume_cursor"]["cursor_status"], "missing")
        self.assertEqual(probe["resume_cursor"]["recovery_reason"], "checkpoint_missing")

    def test_probe_run_recovery_blocks_cross_process_registry_recovery_when_workspace_backend_is_not_durable(self):
        store = InMemoryEmbeddedRunWorkspaceStore()
        registry = InMemoryEmbeddedContinuationRegistry()

        def _tool_executor(_run):
            return {
                "tool_name": "filesystem_write",
                "args": {"path": "case.md"},
                "result": "写入成功",
            }

        def _reviewer(_run):
            return {
                "reviewer": "quality_gate",
                "status": "approved",
                "summary": "工具结果可接受",
            }

        registry.register("tool_executor.filesystem_write", _tool_executor)
        registry.register("reviewer.quality_gate", _reviewer)

        writer = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)
        result = writer.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
        })
        writer.execute_run(
            result["run"]["run_id"],
            tool_policy=lambda _run: {
                "status": "approval_required",
                "tool_name": "filesystem_write",
                "tool_args": {"path": "case.md"},
                "reason": "高风险写文件工具需要人工审批",
            },
            tool_executor=_tool_executor,
            reviewer=_reviewer,
        )

        reader = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)
        probe = reader.probe_run_recovery(result["run"]["run_id"])

        self.assertFalse(probe["recoverable"])
        self.assertEqual(probe["persistence_interface"]["persistence_posture"], "memory_preview")
        self.assertEqual(
            probe["persistence_interface"]["cross_process_block_reason"],
            "workspace_backend_not_durable",
        )
        self.assertEqual(probe["checkpoint"]["status"], "blocked")
        self.assertEqual(probe["checkpoint"]["recovery_reason"], "workspace_backend_not_durable")
        self.assertEqual(probe["resume_cursor"]["cursor_status"], "blocked")
        self.assertEqual(probe["resume_cursor"]["recovery_reason"], "workspace_backend_not_durable")
        self.assertEqual(probe["tool_continuation"]["recovery_reason"], "workspace_backend_not_durable")
        self.assertEqual(probe["loop_continuation"]["recovery_reason"], "workspace_backend_not_durable")
        probe_entrypoints = {
            (item["method"], item.get("mode") or ""): item
            for item in probe["recovery_entrypoints"]
        }
        self.assertFalse(probe_entrypoints[("submit_approval", "approved")]["available"])
        self.assertEqual(
            probe_entrypoints[("submit_approval", "approved")]["blocked_reason"],
            "workspace_backend_not_durable",
        )
        self.assertFalse(probe_entrypoints[("resume_run", "continue_loop")]["available"])
        self.assertEqual(probe_entrypoints[("resume_run", "continue_loop")]["blocked_reason"], "run_not_observing")
        self.assertFalse(probe["tool_continuation"]["workspace_backend"]["durable"])
        self.assertEqual(probe["tool_continuation"]["persistence_interface"]["persistence_posture"], "memory_preview")

    def test_probe_run_recovery_blocks_cross_process_registry_recovery_when_workspace_backend_is_degraded(self):
        store = _DegradedDurableTestWorkspaceStore()
        registry = InMemoryEmbeddedContinuationRegistry()

        def _tool_executor(_run):
            return {
                "tool_name": "filesystem_write",
                "args": {"path": "case.md"},
                "result": "写入成功",
            }

        def _reviewer(_run):
            return {
                "reviewer": "quality_gate",
                "status": "approved",
                "summary": "工具结果可接受",
            }

        registry.register("tool_executor.filesystem_write", _tool_executor)
        registry.register("reviewer.quality_gate", _reviewer)
        writer = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)
        result = writer.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
        })
        writer.execute_run(
            result["run"]["run_id"],
            tool_policy=lambda _run: {
                "status": "approval_required",
                "tool_name": "filesystem_write",
                "tool_args": {"path": "case.md"},
                "reason": "高风险写文件工具需要人工审批",
            },
            tool_executor=_tool_executor,
            reviewer=_reviewer,
        )

        reader = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)
        probe = reader.probe_run_recovery(result["run"]["run_id"])

        self.assertFalse(probe["recoverable"])
        self.assertEqual(probe["persistence_interface"]["persistence_posture"], "durable_degraded")
        self.assertEqual(
            probe["persistence_interface"]["cross_process_block_reason"],
            "workspace_backend_fallback_active",
        )
        self.assertEqual(probe["checkpoint"]["status"], "blocked")
        self.assertEqual(probe["checkpoint"]["recovery_reason"], "workspace_backend_fallback_active")
        self.assertEqual(probe["resume_cursor"]["cursor_status"], "blocked")
        self.assertEqual(probe["resume_cursor"]["recovery_reason"], "workspace_backend_fallback_active")
        self.assertEqual(probe["tool_continuation"]["recovery_reason"], "workspace_backend_fallback_active")
        self.assertEqual(probe["loop_continuation"]["recovery_reason"], "workspace_backend_fallback_active")

    def test_probe_run_recovery_reports_recoverable_via_registry_in_new_process(self):
        store = _DurableTestWorkspaceStore()
        registry = InMemoryEmbeddedContinuationRegistry()

        def _tool_executor(_run):
            return {
                "tool_name": "filesystem_write",
                "args": {"path": "case.md"},
                "result": "写入成功",
            }

        def _reviewer(_run):
            return {
                "reviewer": "quality_gate",
                "status": "approved",
                "summary": "工具结果可接受",
            }

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
                "reason": "高风险写文件工具需要人工审批",
            },
            tool_executor=_tool_executor,
            reviewer=_reviewer,
        )

        reader = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)
        probe = reader.probe_run_recovery(result["run"]["run_id"])

        self.assertTrue(probe["recoverable"])
        self.assertEqual(probe["persistence_interface"]["persistence_posture"], "durable_ready")
        self.assertTrue(probe["persistence_interface"]["cross_process_candidate"])
        self.assertEqual(probe["checkpoint"]["contract_version"], "phase-ii-durable-runtime-checkpoint-v1")
        self.assertEqual(probe["checkpoint"]["status"], "ready")
        self.assertEqual(probe["checkpoint"]["checkpoint_kind"], "approval_waiting")
        self.assertEqual(probe["resume_cursor"]["contract_version"], "phase-ii-runtime-resume-cursor-v1")
        self.assertEqual(probe["resume_cursor"]["cursor_status"], "ready")
        self.assertEqual(probe["resume_cursor"]["entrypoint"], "submit_approval.approved")
        self.assertEqual(probe["resume_cursor"]["recovery_reason"], "ready_via_registry")
        self.assertEqual(probe["tool_continuation"]["recovery_reason"], "ready_via_registry")
        self.assertEqual(probe["loop_continuation"]["recovery_reason"], "ready_via_registry")
        probe_entrypoints = {
            (item["method"], item.get("mode") or ""): item
            for item in probe["recovery_entrypoints"]
        }
        self.assertTrue(probe_entrypoints[("submit_approval", "approved")]["available"])
        self.assertEqual(probe_entrypoints[("submit_approval", "approved")]["recovery_reason"], "ready_via_registry")
        self.assertFalse(probe_entrypoints[("resume_run", "continue_loop")]["available"])
        self.assertEqual(probe_entrypoints[("resume_run", "continue_loop")]["blocked_reason"], "run_not_observing")
        persisted_tool = store.get_tool_continuation_descriptor(executed["approval_request"]["request_id"])
        persisted_loop = store.get_loop_continuation_descriptor(result["run"]["run_id"])
        self.assertEqual(persisted_tool["tool_executor_binding_id"], "tool_executor.filesystem_write")
        self.assertEqual(persisted_loop["reviewer_binding_id"], "reviewer.quality_gate")

    def test_default_sdk_instances_can_share_workspace_and_registry_for_recovery(self):
        store = _DurableTestWorkspaceStore()
        registry = InMemoryEmbeddedContinuationRegistry()

        def _tool_executor(_run):
            return {
                "tool_name": "filesystem_write",
                "args": {"path": "case.md"},
                "result": "写入成功",
            }

        def _reviewer(_run):
            return {
                "reviewer": "quality_gate",
                "status": "approved",
                "summary": "工具结果可接受",
            }

        registry.register("tool_executor.filesystem_write", _tool_executor)
        registry.register("reviewer.quality_gate", _reviewer)

        with patch.object(adapters_module, "_embedded_workspace_store", store), patch.object(
            continuation_registry_module,
            "_embedded_continuation_registry_singleton",
            registry,
        ):
            writer = EmbeddedAgentRuntimeSDK()
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
                reviewer=_reviewer,
            )

            reader = EmbeddedAgentRuntimeSDK()
            probe = reader.probe_run_recovery(result["run"]["run_id"])
            approved = reader.submit_approval(executed["approval_request"]["request_id"], "approved")
            resumed = reader.resume_run(result["run"]["run_id"], continue_loop=True)

        self.assertTrue(probe["recoverable"])
        self.assertEqual(probe["tool_continuation"]["recovery_reason"], "ready_via_registry")
        self.assertIn("tool_executor.", probe["tool_continuation"]["binding_ids"]["tool_executor_binding_id"])
        self.assertIn("reviewer.", probe["loop_continuation"]["binding_ids"]["reviewer_binding_id"])
        self.assertEqual(approved["run"]["tool_history"][0]["result"], "写入成功")
        self.assertEqual(resumed["run"]["state"], "done")

    def test_registry_can_reattach_tool_and_loop_continuations_in_new_process(self):
        store = _DurableTestWorkspaceStore()
        registry = InMemoryEmbeddedContinuationRegistry()

        def _tool_executor(_run):
            return {
                "tool_name": "filesystem_write",
                "args": {"path": "case.md"},
                "result": "写入成功",
            }

        def _reviewer(_run):
            return {
                "reviewer": "quality_gate",
                "status": "approved",
                "summary": "工具结果可接受",
            }

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
                "reason": "高风险写文件工具需要人工审批",
            },
            tool_executor=_tool_executor,
            reviewer=_reviewer,
        )

        reader = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)
        approved = reader.submit_approval(executed["approval_request"]["request_id"], "approved")
        resumed = reader.resume_run(result["run"]["run_id"], continue_loop=True)

        self.assertEqual(approved["run"]["tool_history"][0]["result"], "写入成功")
        approved_operation = approved["run"]["metadata"]["latest_recovery_operation"]
        self.assertEqual(approved_operation["operation_status"], "recovered")
        self.assertEqual(approved_operation["entrypoint"], "submit_approval.approved")
        self.assertEqual(approved_operation["persistence_posture"], "durable_ready")
        self.assertEqual(
            approved_operation["continuation_ref"]["binding_ids"]["tool_executor_binding_id"],
            "tool_executor.filesystem_write",
        )
        self.assertFalse(approved_operation["worker_ownership"]["implemented"])
        self.assertEqual(resumed["run"]["state"], "done")
        loop_operation = resumed["run"]["metadata"]["latest_recovery_operation"]
        self.assertEqual(loop_operation["operation_status"], "recovered")
        self.assertEqual(loop_operation["entrypoint"], "resume_run.continue_loop")
        self.assertEqual(
            loop_operation["continuation_ref"]["binding_ids"]["reviewer_binding_id"],
            "reviewer.quality_gate",
        )
        self.assertEqual(resumed["run"]["metadata"]["execution_review"]["status"], "approved")
        post_recovery_probe = reader.probe_run_recovery(result["run"]["run_id"])
        self.assertEqual(
            post_recovery_probe["latest_recovery_operation"]["entrypoint"],
            "resume_run.continue_loop",
        )
        self.assertGreaterEqual(len(post_recovery_probe["recovery_operations"]), 2)

    def test_recovery_entry_auto_claims_worker_ownership_when_enabled(self):
        store = _DurableTestWorkspaceStore()
        registry = InMemoryEmbeddedContinuationRegistry()
        ownership_store = InMemoryRuntimeWorkerOwnershipStore()

        def _tool_executor(_run):
            return {
                "tool_name": "filesystem_write",
                "args": {"path": "case.md"},
                "result": "写入成功",
            }

        def _reviewer(_run):
            return {
                "reviewer": "quality_gate",
                "status": "approved",
                "summary": "工具结果可接受",
            }

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
                "reason": "高风险写文件工具需要人工审批",
            },
            tool_executor=_tool_executor,
            reviewer=_reviewer,
        )

        reader = EmbeddedAgentRuntimeSDK(
            workspace_store=store,
            continuation_registry=registry,
            worker_ownership_store=ownership_store,
            worker_ownership_auto_claim_enabled=True,
            worker_ownership_worker_id="worker-recovery-1",
        )
        approved = reader.submit_approval(executed["approval_request"]["request_id"], "approved")

        operation = approved["run"]["metadata"]["latest_recovery_operation"]
        ownership = operation["worker_ownership"]
        self.assertTrue(ownership["implemented"])
        self.assertEqual(ownership["worker_id"], "worker-recovery-1")
        self.assertEqual(ownership["lease_status"], "claimed")
        self.assertTrue(ownership["owned"])
        self.assertEqual(ownership_store.get_lease(result["run"]["run_id"])["worker_id"], "worker-recovery-1")

    def test_recovery_entry_gate_enforced_auto_claim_blocks_claim_when_gate_blocked(self):
        store = _DurableTestWorkspaceStore()
        registry = InMemoryEmbeddedContinuationRegistry()
        ownership_store = _DurableCountingWorkerOwnershipStore()

        def _tool_executor(_run):
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

        reader = EmbeddedAgentRuntimeSDK(
            workspace_store=store,
            continuation_registry=registry,
            worker_ownership_store=ownership_store,
            worker_ownership_auto_claim_enabled=True,
            worker_ownership_auto_claim_gate_enforced=True,
            worker_ownership_worker_id="worker-recovery-1",
        )
        with self.assertRaisesRegex(ValueError, "worker_ownership_lost"):
            reader.submit_approval(executed["approval_request"]["request_id"], "approved")

        self.assertEqual(ownership_store.claim_calls, 0)
        failed_event = next(
            event
            for event in reader.stream_events(result["run"]["run_id"])
            if event["status_kind"] == "recovery_failed_closed"
        )
        ownership = failed_event["recovery_operation"]["worker_ownership"]
        self.assertFalse(ownership["owned"])
        self.assertEqual(ownership["blocked_reason"], "auto_claim_enablement_gate_blocked")
        self.assertEqual(
            ownership["auto_claim_enablement_gate"]["blocked_reason"],
            "production_gate_ready_missing",
        )

    def test_recovery_entry_gate_enforced_auto_claim_blocks_non_allowlisted_entrypoint(self):
        store = _DurableTestWorkspaceStore()
        registry = InMemoryEmbeddedContinuationRegistry()
        ownership_store = _DurableCountingWorkerOwnershipStore()

        def _tool_executor(_run):
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

        reader = EmbeddedAgentRuntimeSDK(
            workspace_store=store,
            continuation_registry=registry,
            worker_ownership_store=ownership_store,
            worker_ownership_auto_claim_enabled=True,
            worker_ownership_auto_claim_gate_enforced=True,
            worker_ownership_auto_claim_production_gate_ready=True,
            worker_ownership_auto_claim_idempotency_evidence_ready=True,
            worker_ownership_auto_claim_audit_evidence_ready=True,
            worker_ownership_auto_claim_rollout_decision_recorded=True,
            worker_ownership_auto_claim_allowed_entrypoints=["resume_run.continue_loop"],
            worker_ownership_worker_id="worker-recovery-1",
        )
        with self.assertRaisesRegex(ValueError, "worker_ownership_lost"):
            reader.submit_approval(executed["approval_request"]["request_id"], "approved")

        self.assertEqual(ownership_store.claim_calls, 0)
        failed_event = next(
            event
            for event in reader.stream_events(result["run"]["run_id"])
            if event["status_kind"] == "recovery_failed_closed"
        )
        ownership = failed_event["recovery_operation"]["worker_ownership"]
        self.assertEqual(
            ownership["auto_claim_enablement_gate"]["blocked_reason"],
            "entrypoint_not_allowlisted",
        )

    def test_recovery_entry_gate_enforced_auto_claim_claims_when_gate_ready(self):
        store = _DurableTestWorkspaceStore()
        registry = InMemoryEmbeddedContinuationRegistry()
        ownership_store = _DurableCountingWorkerOwnershipStore()

        def _tool_executor(_run):
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

        reader = EmbeddedAgentRuntimeSDK(
            workspace_store=store,
            continuation_registry=registry,
            worker_ownership_store=ownership_store,
            worker_ownership_auto_claim_enabled=True,
            worker_ownership_auto_claim_gate_enforced=True,
            worker_ownership_auto_claim_production_gate_ready=True,
            worker_ownership_auto_claim_idempotency_evidence_ready=True,
            worker_ownership_auto_claim_audit_evidence_ready=True,
            worker_ownership_auto_claim_rollout_decision_recorded=True,
            worker_ownership_worker_id="worker-recovery-1",
        )
        approved = reader.submit_approval(executed["approval_request"]["request_id"], "approved")

        self.assertEqual(ownership_store.claim_calls, 1)
        ownership = approved["run"]["metadata"]["latest_recovery_operation"]["worker_ownership"]
        self.assertTrue(ownership["owned"])
        self.assertEqual(ownership["worker_id"], "worker-recovery-1")
        self.assertEqual(ownership["lease_status"], "claimed")

    def test_sqlalchemy_workspace_store_can_reattach_tool_and_loop_continuations_in_new_process(self):
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        try:
            store = SQLAlchemyEmbeddedRunWorkspaceStore(
                TestingSessionLocal,
                allow_operation_fallback=False,
                backend_mode="strict_sql",
            )
            registry = InMemoryEmbeddedContinuationRegistry()

            def _tool_executor(_run):
                return {
                    "tool_name": "filesystem_write",
                    "args": {"path": "case.md"},
                    "result": "写入成功",
                }

            def _reviewer(_run):
                return {
                    "reviewer": "quality_gate",
                    "status": "approved",
                    "summary": "工具结果可接受",
                }

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
                    "reason": "高风险写文件工具需要人工审批",
                },
                tool_executor=_tool_executor,
                reviewer=_reviewer,
            )

            reader = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)
            probe = reader.probe_run_recovery(result["run"]["run_id"])
            self.assertTrue(probe["recoverable"])
            self.assertEqual(probe["tool_continuation"]["recovery_reason"], "ready_via_registry")
            self.assertEqual(probe["loop_continuation"]["recovery_reason"], "ready_via_registry")

            approved = reader.submit_approval(executed["approval_request"]["request_id"], "approved")
            resumed = reader.resume_run(result["run"]["run_id"], continue_loop=True)

            self.assertEqual(approved["run"]["tool_history"][0]["result"], "写入成功")
            self.assertEqual(resumed["run"]["state"], "done")
            self.assertEqual(resumed["run"]["metadata"]["execution_review"]["status"], "approved")
            self.assertEqual(store.describe_backend()["backend_kind"], "sqlalchemy")
            self.assertTrue(store.describe_backend()["durable"])
            self.assertFalse(store.describe_backend()["fallback_active"])
        finally:
            Base.metadata.drop_all(bind=engine)
            engine.dispose()

    def test_registry_reattachment_is_blocked_when_workspace_backend_is_not_durable(self):
        store = InMemoryEmbeddedRunWorkspaceStore()
        registry = InMemoryEmbeddedContinuationRegistry()

        def _tool_executor(_run):
            return {
                "tool_name": "filesystem_write",
                "args": {"path": "case.md"},
                "result": "写入成功",
            }

        def _reviewer(_run):
            return {
                "reviewer": "quality_gate",
                "status": "approved",
                "summary": "工具结果可接受",
            }

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
                "reason": "高风险写文件工具需要人工审批",
            },
            tool_executor=_tool_executor,
            reviewer=_reviewer,
        )

        reader = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)
        with self.assertRaisesRegex(ValueError, "workspace_backend_not_durable"):
            reader.submit_approval(executed["approval_request"]["request_id"], "approved")

    def test_probe_run_recovery_reports_missing_registered_binding_when_binding_cannot_be_resolved(self):
        store = _DurableTestWorkspaceStore()
        registry = InMemoryEmbeddedContinuationRegistry()

        def _tool_executor(_run):
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
        writer.execute_run(
            result["run"]["run_id"],
            tool_policy=lambda _run: {
                "status": "approval_required",
                "tool_name": "filesystem_write",
                "tool_args": {"path": "case.md"},
                "reason": "高风险写文件工具需要人工审批",
            },
            tool_executor=_tool_executor,
        )

        reader = EmbeddedAgentRuntimeSDK(
            workspace_store=store,
            continuation_registry=InMemoryEmbeddedContinuationRegistry(),
        )
        probe = reader.probe_run_recovery(result["run"]["run_id"])

        self.assertFalse(probe["recoverable"])
        self.assertEqual(probe["checkpoint"]["status"], "blocked")
        self.assertEqual(probe["checkpoint"]["recovery_reason"], "missing_registered_binding")
        self.assertEqual(probe["resume_cursor"]["cursor_status"], "blocked")
        self.assertEqual(probe["resume_cursor"]["recovery_reason"], "missing_registered_binding")
        self.assertEqual(probe["tool_continuation"]["recovery_reason"], "missing_registered_binding")
        self.assertIn("tool_executor.filesystem_write", probe["tool_continuation"]["missing_binding_ids"])

    def test_sdk_tool_registration_rejects_empty_definition_after_preview_promotion(self):
        sdk = EmbeddedAgentRuntimeSDK()

        with self.assertRaises(ValueError):
            sdk.register_tool({})


if __name__ == "__main__":
    unittest.main()
