import unittest

from unittest.mock import Mock, patch

import backend.agent_framework.adapters as adapters_module
import backend.agent_framework.continuation_registry as continuation_registry_module
from backend.agent_framework.continuation_registry import InMemoryEmbeddedContinuationRegistry
from backend.agent_framework.persistence import InMemoryEmbeddedRunWorkspaceStore
from backend.agent_framework.harness import create_agent
from backend.agent_framework.runtime_dependencies import EmbeddedRuntimeDependencies, EmbeddedRuntimeFactory
from backend.agent_framework.sdk import EmbeddedAgentRuntimeSDK, validate_embedded_sdk_event_payloads
from backend.agent_framework.tool_policy import build_policy_engine_tool_policy
from backend.agent_framework.tools import ToolSpec
from backend.harness.tool_registry import ToolRegistry
from backend.services.tool_runtime_service import ToolRuntimeService


class AgentHarnessFacadeTests(unittest.TestCase):
    def test_create_agent_runs_through_embedded_runtime_defaults(self):
        sdk = EmbeddedAgentRuntimeSDK()
        agent = create_agent(
            name="fraud_assistant",
            model_name="doubao",
            sdk=sdk,
            default_user_id=7,
            default_conversation_id=42,
        )

        result = agent.run("评估这条交易是否存在诈骗风险")

        run = result["run"]
        self.assertTrue(run["runtime_core"])
        self.assertEqual(run["model_name"], "doubao")
        self.assertEqual(run["run_kind"], "chat")
        self.assertEqual(run["user_id"], 7)
        self.assertEqual(run["conversation_id"], 42)
        self.assertEqual(run["metadata"]["agent_name"], "fraud_assistant")
        self.assertEqual(run["metadata"]["input"], "评估这条交易是否存在诈骗风险")

        events = list(agent.stream(run["run_id"]))
        self.assertEqual(events[0]["status_kind"], "run_created")
        self.assertEqual(events[0]["payload"]["run"]["metadata"]["agent_name"], "fraud_assistant")

    def test_create_agent_default_sdk_uses_shared_continuation_registry(self):
        agent = create_agent(
            name="fraud_assistant",
            model_name="doubao",
            default_user_id=7,
            default_conversation_id=42,
        )

        catalog = agent.sdk.list_continuation_bindings()

        self.assertEqual(catalog["registry_type"], "InMemoryEmbeddedContinuationRegistry")
        self.assertGreaterEqual(catalog["total_bindings"], 0)
        self.assertIsInstance(catalog["bindings"], list)

    @patch("backend.agent_framework.harness.create_default_embedded_runtime_sdk")
    def test_create_agent_without_sdk_uses_default_runtime_factory(self, mock_factory):
        stub_sdk = Mock()
        stub_sdk.list_continuation_bindings.return_value = {
            "registry_type": "InMemoryEmbeddedContinuationRegistry",
            "total_bindings": 0,
            "bindings": [],
        }
        mock_factory.return_value = stub_sdk

        agent = create_agent(
            name="fraud_assistant",
            model_name="doubao",
            default_user_id=7,
            default_conversation_id=42,
        )

        mock_factory.assert_called_once()
        self.assertIs(agent.sdk, stub_sdk)

    def test_create_agent_can_use_runtime_factory(self):
        store = InMemoryEmbeddedRunWorkspaceStore()
        registry = InMemoryEmbeddedContinuationRegistry()
        factory = EmbeddedRuntimeFactory(
            dependencies=EmbeddedRuntimeDependencies(
                workspace_store=store,
                continuation_registry=registry,
            )
        )

        agent = create_agent(
            name="fraud_assistant",
            model_name="doubao",
            runtime_factory=factory,
            default_user_id=7,
            default_conversation_id=42,
        )

        self.assertIs(agent.sdk._workspace_store, store)
        self.assertIs(agent.sdk._continuation_registry, registry)

    def test_facade_can_list_continuation_bindings(self):
        registry = InMemoryEmbeddedContinuationRegistry()

        def _tool_executor(_run):
            return None

        registry.register(
            "tool_executor.filesystem_write",
            _tool_executor,
            binding_kind="tool_executor",
            metadata={"tool_name": "filesystem_write"},
        )
        sdk = EmbeddedAgentRuntimeSDK(continuation_registry=registry)
        agent = create_agent(
            name="fraud_assistant",
            model_name="doubao",
            sdk=sdk,
            default_user_id=7,
            default_conversation_id=42,
        )

        catalog = agent.list_continuation_bindings()

        self.assertEqual(catalog["registry_type"], "InMemoryEmbeddedContinuationRegistry")
        self.assertEqual(catalog["total_bindings"], 1)
        self.assertEqual(catalog["bindings"][0]["binding_id"], "tool_executor.filesystem_write")

    def test_create_agent_can_accept_runtime_dependencies_bundle(self):
        store = InMemoryEmbeddedRunWorkspaceStore()
        registry = InMemoryEmbeddedContinuationRegistry()
        dependencies = EmbeddedRuntimeDependencies(
            workspace_store=store,
            continuation_registry=registry,
        )

        agent = create_agent(
            name="fraud_assistant",
            model_name="doubao",
            runtime_dependencies=dependencies,
            default_user_id=7,
            default_conversation_id=42,
        )

        self.assertIs(agent.sdk._workspace_store, store)
        self.assertIs(agent.sdk._continuation_registry, registry)

    def test_run_payload_can_override_defaults_and_approval_can_be_submitted(self):
        sdk = EmbeddedAgentRuntimeSDK()
        agent = create_agent(name="review_agent", model_name="qwen", sdk=sdk)

        result = agent.run({
            "user_id": 9,
            "conversation_id": 11,
            "run_kind": "child",
            "approval_request": {
                "request_id": "approval_1",
                "tool_name": "mcp_filesystem_write",
                "tool_args": {"path": "README.md"},
                "reason": "需要确认写入。",
            },
        })

        self.assertEqual(result["run"]["state"], "waiting_approval")
        self.assertEqual(result["run"]["run_kind"], "child")
        self.assertEqual(result["run"]["user_id"], 9)
        self.assertEqual(result["run"]["conversation_id"], 11)
        self.assertEqual(result["approval_request"]["request_id"], "approval_1")

        approved = agent.approve("approval_1")

        self.assertEqual(approved["approval_request"]["status"], "approved")
        self.assertEqual(approved["run"]["state"], "observing")

        resumed = agent.resume(approved["run"]["run_id"])

        self.assertEqual(resumed["run"]["state"], "generating")
        self.assertEqual(resumed["run"]["iteration"], 1)
        self.assertEqual(list(agent.stream(approved["run"]["run_id"]))[-1]["state"], "generating")

    def test_delegate_creates_child_run_with_agent_metadata(self):
        sdk = EmbeddedAgentRuntimeSDK()
        agent = create_agent(
            name="fraud_assistant",
            model_name="doubao",
            sdk=sdk,
            default_user_id=7,
            default_conversation_id=42,
        )
        parent = agent.run("初步评估交易")

        child = agent.delegate(
            parent["run"]["run_id"],
            "复核交易风险",
            name="risk_reviewer",
        )

        self.assertEqual(child["run"]["run_kind"], "child")
        self.assertEqual(child["run"]["parent_run_id"], parent["run"]["run_id"])
        self.assertEqual(child["run"]["metadata"]["agent_name"], "risk_reviewer")
        self.assertEqual(child["run"]["metadata"]["delegated_by_agent"], "fraud_assistant")
        self.assertEqual(child["run"]["metadata"]["input"], "复核交易风险")
        self.assertEqual(child["child_executor_preflight"]["status"], "relationship_only")
        self.assertFalse(child["child_executor_preflight"]["real_child_executor_ready"])
        self.assertTrue(
            any(event["status_kind"] == "child_run_created" for event in agent.stream(parent["run"]["run_id"]))
        )

    def test_probe_recovery_can_surface_sdk_recovery_contract(self):
        store = InMemoryEmbeddedRunWorkspaceStore()
        registry = InMemoryEmbeddedContinuationRegistry()

        def _tool_executor(_run):
            return {
                "tool_name": "filesystem_write",
                "args": {"path": "case.md"},
                "result": "写入成功",
            }

        registry.register("tool_executor.filesystem_write", _tool_executor)
        sdk = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)
        agent = create_agent(
            name="fraud_assistant",
            model_name="doubao",
            sdk=sdk,
            default_user_id=7,
            default_conversation_id=42,
        )
        run = agent.run("评估交易风险")
        agent.execute(
            run["run"]["run_id"],
            tool_policy=lambda _run: {
                "status": "approval_required",
                "tool_name": "filesystem_write",
                "tool_args": {"path": "case.md"},
                "reason": "高风险写文件工具需要人工审批",
            },
            tool_executor=_tool_executor,
        )

        probe = agent.probe_recovery(run["run"]["run_id"])

        self.assertTrue(probe["recoverable"])
        self.assertEqual(probe["tool_continuation"]["recovery_reason"], "ready_in_process")

    def test_default_agents_can_share_workspace_and_registry_for_recovery(self):
        class _DurableFacadeWorkspaceStore(InMemoryEmbeddedRunWorkspaceStore):
            def describe_backend(self):
                return {
                    "backend_kind": "test_durable",
                    "durable": True,
                    "fallback_active": False,
                    "fallback_reason": "",
                    "last_error": "",
                }

        store = _DurableFacadeWorkspaceStore()
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
            writer = create_agent(
                name="fraud_assistant",
                model_name="doubao",
                default_user_id=7,
                default_conversation_id=42,
            )
            run = writer.run("评估交易风险")
            executed = writer.execute(
                run["run"]["run_id"],
                tool_policy=lambda _run: {
                    "status": "approval_required",
                    "tool_name": "filesystem_write",
                    "tool_args": {"path": "case.md"},
                    "reason": "高风险写文件工具需要人工审批",
                },
                tool_executor=_tool_executor,
                reviewer=_reviewer,
            )

            reader = create_agent(
                name="fraud_assistant",
                model_name="doubao",
                default_user_id=7,
                default_conversation_id=42,
            )
            probe = reader.probe_recovery(run["run"]["run_id"])
            approved = reader.approve(executed["approval_request"]["request_id"], "approved")
            resumed = reader.resume(run["run"]["run_id"], continue_loop=True)

        self.assertTrue(probe["recoverable"])
        self.assertEqual(probe["tool_continuation"]["recovery_reason"], "ready_via_registry")
        self.assertEqual(approved["run"]["tool_history"][0]["result"], "写入成功")
        self.assertEqual(resumed["run"]["state"], "done")

    def test_evaluate_delegate_preflight_can_surface_executor_binding_readiness(self):
        sdk = EmbeddedAgentRuntimeSDK()
        agent = create_agent(
            name="fraud_assistant",
            model_name="doubao",
            sdk=sdk,
            default_user_id=7,
            default_conversation_id=42,
        )
        parent = agent.run("初步评估交易")

        preflight = agent.evaluate_delegate_preflight(
            parent["run"]["run_id"],
            {
                "input": "复核交易风险",
                "merge_strategy": "append_summary",
                "metadata": {
                    "scheduler_policy": {"timeout_seconds": 45},
                    "worker_runtime_backend": "embedded_sdk_worker",
                },
            },
            name="risk_reviewer",
        )

        self.assertEqual(preflight["status"], "promotion_candidate")
        self.assertTrue(preflight["promotion_ready"])
        self.assertEqual(preflight["executor_binding_status"], "ready")
        self.assertEqual(preflight["recommended_next_step"], "wire_executor_backend")

    def test_evaluate_delegate_gate_can_surface_blocked_and_passed_gate_status(self):
        sdk = EmbeddedAgentRuntimeSDK()
        agent = create_agent(
            name="fraud_assistant",
            model_name="doubao",
            sdk=sdk,
            default_user_id=7,
            default_conversation_id=42,
        )
        parent = agent.run("初步评估交易")

        blocked = agent.evaluate_delegate_gate(
            parent["run"]["run_id"],
            "复核交易风险",
            name="risk_reviewer",
        )
        self.assertEqual(blocked["gate_status"], "blocked")
        self.assertFalse(blocked["allowed"])
        self.assertIn("child_context_budget_defined", blocked["blockers"])

        passed = agent.evaluate_delegate_gate(
            parent["run"]["run_id"],
            {
                "input": "复核交易风险",
                "merge_strategy": "append_summary",
                "metadata": {
                    "scheduler_policy": {"timeout_seconds": 45},
                    "worker_runtime_backend": "embedded_sdk_worker",
                },
            },
            name="risk_reviewer",
        )
        self.assertEqual(passed["gate_status"], "passed")
        self.assertTrue(passed["allowed"])
        self.assertEqual(passed["executor_path"], "embedded_sdk_worker_candidate")

    def test_evaluate_delegate_routing_can_surface_blocked_and_routed_status(self):
        sdk = EmbeddedAgentRuntimeSDK()
        agent = create_agent(
            name="fraud_assistant",
            model_name="doubao",
            sdk=sdk,
            default_user_id=7,
            default_conversation_id=42,
        )
        parent = agent.run("初步评估交易")

        blocked = agent.evaluate_delegate_routing(
            parent["run"]["run_id"],
            "复核交易风险",
            name="risk_reviewer",
        )
        self.assertEqual(blocked["route_status"], "blocked")
        self.assertFalse(blocked["will_execute"])
        self.assertEqual(blocked["recommended_action"], "keep_relationship_only")

        routed = agent.evaluate_delegate_routing(
            parent["run"]["run_id"],
            {
                "input": "复核交易风险",
                "merge_strategy": "append_summary",
                "metadata": {
                    "scheduler_policy": {"timeout_seconds": 45},
                    "worker_runtime_backend": "embedded_sdk_worker",
                },
            },
            name="risk_reviewer",
        )
        self.assertEqual(routed["route_status"], "routed")
        self.assertFalse(routed["will_execute"])
        self.assertEqual(routed["executor_path"], "embedded_sdk_worker_candidate")
        self.assertEqual(routed["recommended_action"], "bind_embedded_sdk_worker_executor")

    def test_execute_delegate_stub_can_surface_blocked_and_recorded_stub_status(self):
        sdk = EmbeddedAgentRuntimeSDK()
        agent = create_agent(
            name="fraud_assistant",
            model_name="doubao",
            sdk=sdk,
            default_user_id=7,
            default_conversation_id=42,
        )
        parent = agent.run("初步评估交易")

        blocked = agent.execute_delegate_stub(
            parent["run"]["run_id"],
            "复核交易风险",
            name="risk_reviewer",
        )
        self.assertEqual(blocked["stub_status"], "blocked")
        self.assertEqual(blocked["recommended_action"], "keep_relationship_only")

        recorded = agent.execute_delegate_stub(
            parent["run"]["run_id"],
            {
                "input": "复核交易风险",
                "merge_strategy": "append_summary",
                "metadata": {
                    "scheduler_policy": {"timeout_seconds": 45},
                    "worker_runtime_backend": "embedded_sdk_worker",
                },
            },
            name="risk_reviewer",
        )
        self.assertEqual(recorded["stub_status"], "recorded")
        self.assertFalse(recorded["will_execute"])
        self.assertEqual(recorded["executor_path"], "embedded_sdk_worker_candidate")

    def test_execute_delegate_can_surface_blocked_and_executed_status(self):
        sdk = EmbeddedAgentRuntimeSDK()
        agent = create_agent(
            name="fraud_assistant",
            model_name="doubao",
            sdk=sdk,
            default_user_id=7,
            default_conversation_id=42,
        )
        parent = agent.run("初步评估交易")

        blocked = agent.execute_delegate(
            parent["run"]["run_id"],
            "复核交易风险",
            name="risk_reviewer",
        )
        self.assertEqual(blocked["execution_status"], "blocked")

        executed = agent.execute_delegate(
            parent["run"]["run_id"],
            {
                "input": "复核交易风险",
                "merge_strategy": "append_summary",
                "metadata": {
                    "scheduler_policy": {"timeout_seconds": 45},
                    "worker_runtime_backend": "embedded_sdk_worker",
                },
            },
            name="risk_reviewer",
        )
        self.assertEqual(executed["execution_status"], "executed")
        self.assertTrue(executed["will_execute"])
        self.assertEqual(executed["execution_mode"], "embedded_sdk_worker_skeleton")
        self.assertIn("risk_reviewer", executed["output_summary"])
        self.assertIn("风险复核结论", executed["output_text"])
        self.assertEqual(executed["output_envelope"]["merge_hint"], "append_summary")
        self.assertTrue(executed["output_envelope"]["merge_ready"])
        self.assertEqual(executed["output_payload"]["intent_label"], "risk_review")
        self.assertIn("交易", executed["output_payload"]["entities"])
        self.assertGreaterEqual(len(executed["output_payload"]["focus_points"]), 3)
        self.assertEqual(executed["output_payload"]["business_result"]["result_type"], "risk_assessment")

    def test_execute_delegate_supports_planning_intent_structure(self):
        sdk = EmbeddedAgentRuntimeSDK()
        agent = create_agent(
            name="fraud_assistant",
            model_name="doubao",
            sdk=sdk,
            default_user_id=7,
            default_conversation_id=42,
        )
        parent = agent.run("初步评估交易")

        executed = agent.execute_delegate(
            parent["run"]["run_id"],
            {
                "input": "生成巡检计划",
                "merge_strategy": "append_summary",
                "metadata": {
                    "scheduler_policy": {"timeout_seconds": 45},
                    "worker_runtime_backend": "embedded_sdk_worker",
                },
            },
            name="planner_agent",
        )

        self.assertEqual(executed["output_payload"]["intent_label"], "planning")
        self.assertEqual(executed["output_payload"]["business_result"]["result_type"], "plan_outline")
        self.assertIn("巡检", executed["output_payload"]["entities"])
        self.assertEqual(len(executed["output_envelope"]["sections"]), 3)

    def test_execute_delegate_supports_general_analysis_semantics(self):
        sdk = EmbeddedAgentRuntimeSDK()
        agent = create_agent(
            name="fraud_assistant",
            model_name="doubao",
            sdk=sdk,
            default_user_id=7,
            default_conversation_id=42,
        )
        parent = agent.run("初步评估交易")

        executed = agent.execute_delegate(
            parent["run"]["run_id"],
            {
                "input": "整理合并摘要并补充结果报告",
                "merge_strategy": "append_summary",
                "metadata": {
                    "scheduler_policy": {"timeout_seconds": 45},
                    "worker_runtime_backend": "embedded_sdk_worker",
                },
            },
            name="analysis_agent",
        )

        self.assertEqual(executed["output_payload"]["intent_label"], "general_analysis")
        self.assertEqual(executed["output_payload"]["business_result"]["result_type"], "analysis_summary")
        self.assertIn("合并", executed["output_payload"]["entities"])
        self.assertEqual(len(executed["output_envelope"]["sections"]), 2)

    def test_merge_delegate_output_can_surface_blocked_and_merged_status(self):
        sdk = EmbeddedAgentRuntimeSDK()
        agent = create_agent(
            name="fraud_assistant",
            model_name="doubao",
            sdk=sdk,
            default_user_id=7,
            default_conversation_id=42,
        )
        parent = agent.run("初步评估交易")

        blocked = agent.merge_delegate_output(
            parent["run"]["run_id"],
            "复核交易风险",
            name="risk_reviewer",
        )
        self.assertEqual(blocked["merge_status"], "blocked")

        merged = agent.merge_delegate_output(
            parent["run"]["run_id"],
            {
                "input": "复核交易风险",
                "merge_strategy": "append_summary",
                "metadata": {
                    "scheduler_policy": {"timeout_seconds": 45},
                    "worker_runtime_backend": "embedded_sdk_worker",
                },
            },
            name="risk_reviewer",
        )
        self.assertEqual(merged["merge_status"], "merged")
        self.assertTrue(merged["merge_ready"])
        self.assertIn("risk_reviewer", merged["merged_summary"])

    def test_merge_delegate_output_supports_role_sections_strategy(self):
        sdk = EmbeddedAgentRuntimeSDK()
        agent = create_agent(
            name="fraud_assistant",
            model_name="doubao",
            sdk=sdk,
            default_user_id=7,
            default_conversation_id=42,
        )
        parent = agent.run("初步评估交易")

        merged = agent.merge_delegate_output(
            parent["run"]["run_id"],
            {
                "input": "复核交易风险",
                "merge_strategy": "role_sections",
                "metadata": {
                    "scheduler_policy": {"timeout_seconds": 45},
                    "worker_runtime_backend": "embedded_sdk_worker",
                },
            },
            name="risk_reviewer",
        )

        self.assertEqual(merged["merge_strategy"], "role_sections")
        self.assertIn("[risk_reviewer 已完成风险复核]", merged["merged_output"])

    def test_list_delegate_outputs_can_replay_child_execution_records(self):
        sdk = EmbeddedAgentRuntimeSDK()
        agent = create_agent(
            name="fraud_assistant",
            model_name="doubao",
            sdk=sdk,
            default_user_id=7,
            default_conversation_id=42,
        )
        parent = agent.run("初步评估交易")
        merged = agent.merge_delegate_output(
            parent["run"]["run_id"],
            {
                "input": "复核交易风险",
                "merge_strategy": "append_summary",
                "metadata": {
                    "scheduler_policy": {"timeout_seconds": 45},
                    "worker_runtime_backend": "embedded_sdk_worker",
                },
            },
            name="risk_reviewer",
        )

        replay = agent.list_delegate_outputs(parent["run"]["run_id"])

        self.assertEqual(replay["record_count"], 1)
        self.assertEqual(replay["records"][0]["execution_status"], "executed")
        self.assertEqual(replay["records"][0]["merge_status"], "merged")
        self.assertEqual(replay["records"][0]["result_type"], "risk_assessment")
        self.assertIn("交易", replay["records"][0]["entities"])
        self.assertEqual(replay["latest_merged_output"], merged["merged_output"])

    def test_summarize_delegate_outputs_can_return_compact_artifact_summary(self):
        sdk = EmbeddedAgentRuntimeSDK()
        agent = create_agent(
            name="fraud_assistant",
            model_name="doubao",
            sdk=sdk,
            default_user_id=7,
            default_conversation_id=42,
        )
        parent = agent.run("初步评估交易")
        merged = agent.merge_delegate_output(
            parent["run"]["run_id"],
            {
                "input": "复核交易风险",
                "merge_strategy": "append_summary",
                "metadata": {
                    "scheduler_policy": {"timeout_seconds": 45},
                    "worker_runtime_backend": "embedded_sdk_worker",
                },
            },
            name="risk_reviewer",
        )

        summary = agent.summarize_delegate_outputs(parent["run"]["run_id"])

        self.assertEqual(summary["record_count"], 1)
        self.assertEqual(summary["latest_merge_strategy"], "append_summary")
        self.assertEqual(summary["latest_result_type"], "risk_assessment")
        self.assertIn("交易", summary["latest_entities"])
        self.assertGreaterEqual(len(summary["latest_focus_points"]), 3)
        self.assertEqual(summary["latest_merged_output"], merged["merged_output"])

    def test_delegate_can_surface_promotion_candidate_preflight_when_inputs_are_defined(self):
        sdk = EmbeddedAgentRuntimeSDK()
        agent = create_agent(
            name="fraud_assistant",
            model_name="doubao",
            sdk=sdk,
            default_user_id=7,
            default_conversation_id=42,
        )
        parent = agent.run("初步评估交易")

        child = agent.delegate(
            parent["run"]["run_id"],
            {
                "input": "复核交易风险",
                "merge_strategy": "append_summary",
                "metadata": {
                    "scheduler_policy": {"timeout_seconds": 45},
                    "worker_runtime_backend": "embedded_sdk_worker",
                },
            },
            name="risk_reviewer",
        )

        self.assertEqual(child["child_executor_preflight"]["status"], "promotion_candidate")
        self.assertTrue(child["child_executor_preflight"]["promotion_ready"])
        self.assertEqual(child["child_executor_preflight"]["missing_requirements"], [])

    def test_create_artifact_uses_agent_metadata_and_runtime_events(self):
        sdk = EmbeddedAgentRuntimeSDK()
        agent = create_agent(
            name="fraud_assistant",
            model_name="doubao",
            sdk=sdk,
            default_conversation_id=42,
        )
        run = agent.run("初步评估交易")

        artifact_result = agent.create_artifact(
            run["run"]["run_id"],
            kind="assessment_report",
            content="风险评分：高",
            metadata={"case_id": "case-1"},
        )

        artifact = artifact_result["artifact"]
        self.assertEqual(artifact["kind"], "assessment_report")
        self.assertEqual(artifact["metadata"]["case_id"], "case-1")
        self.assertEqual(artifact["metadata"]["agent_name"], "fraud_assistant")
        self.assertTrue(
            any(event["status_kind"] == "artifact_created" for event in agent.stream(run["run"]["run_id"]))
        )

        replay = agent.list_artifacts(run["run"]["run_id"])

        self.assertEqual(len(replay["artifacts"]), 1)
        self.assertEqual(replay["artifacts"][0]["artifact_id"], artifact["artifact_id"])
        self.assertEqual(replay["artifacts"][0]["content"], "风险评分：高")

    def test_execute_runs_minimal_loop_through_facade(self):
        sdk = EmbeddedAgentRuntimeSDK()
        agent = create_agent(
            name="fraud_assistant",
            model_name="doubao",
            sdk=sdk,
            default_conversation_id=42,
        )
        run = agent.run("初步评估交易")

        executed = agent.execute(run["run"]["run_id"])

        self.assertEqual(executed["run"]["state"], "done")
        self.assertEqual(executed["run"]["metadata"]["agent_name"], "fraud_assistant")
        self.assertEqual(executed["run"]["metadata"]["execution_loop"]["controller"], "minimal")
        self.assertEqual(list(agent.stream(run["run"]["run_id"]))[-1]["status_kind"], "execution_loop_done")

    def test_execute_accepts_reviewer_and_can_fail_quality_gate(self):
        sdk = EmbeddedAgentRuntimeSDK()
        agent = create_agent(name="fraud_assistant", model_name="doubao", sdk=sdk)
        run = agent.run("初步评估交易")

        executed = agent.execute(
            run["run"]["run_id"],
            reviewer=lambda _run: {
                "reviewer": "risk_quality_gate",
                "status": "rejected",
                "summary": "证据链不足",
                "findings": ["missing_evidence"],
            },
        )

        self.assertEqual(executed["run"]["state"], "failed")
        self.assertEqual(executed["run"]["stop_reason"], "review_rejected")
        self.assertEqual(executed["run"]["metadata"]["execution_review"]["reviewer"], "risk_quality_gate")
        events = list(agent.stream(run["run"]["run_id"]))
        self.assertEqual(events[-1]["status_kind"], "execution_loop_review_rejected")
        self.assertTrue(validate_embedded_sdk_event_payloads(events)["valid"])

    def test_execute_accepts_fallback_handler_for_reviewer_failures(self):
        sdk = EmbeddedAgentRuntimeSDK()
        agent = create_agent(name="fraud_assistant", model_name="doubao", sdk=sdk)
        run = agent.run("初步评估交易")

        def broken_reviewer(_run):
            raise RuntimeError("review backend timeout")

        executed = agent.execute(
            run["run"]["run_id"],
            reviewer=broken_reviewer,
            fallback_handler=lambda error, _run: {
                "strategy": "skip_reviewer",
                "status": "handled",
                "summary": f"降级跳过评审：{error}",
                "metadata": {"reason": "review_backend_timeout"},
            },
        )

        self.assertEqual(executed["run"]["state"], "done")
        self.assertEqual(executed["run"]["metadata"]["execution_fallback"]["status"], "handled")
        events = list(agent.stream(run["run"]["run_id"]))
        self.assertTrue(
            any(
                event["status_kind"] == "execution_loop_fallback_applied"
                for event in events
            )
        )
        self.assertTrue(validate_embedded_sdk_event_payloads(events)["valid"])

    def test_execute_fail_closes_when_reviewer_fallback_is_unhandled(self):
        sdk = EmbeddedAgentRuntimeSDK()
        agent = create_agent(name="fraud_assistant", model_name="doubao", sdk=sdk)
        run = agent.run("初步评估交易")

        def broken_reviewer(_run):
            raise RuntimeError("review backend timeout")

        executed = agent.execute(
            run["run"]["run_id"],
            reviewer=broken_reviewer,
            fallback_handler=lambda error, _run: {
                "strategy": "fail_closed",
                "status": "failed",
                "summary": f"评审降级失败：{error}",
                "metadata": {"reason": "review_backend_timeout"},
            },
        )

        events = list(agent.stream(run["run"]["run_id"]))
        self.assertEqual(executed["run"]["state"], "failed")
        self.assertEqual(executed["run"]["stop_reason"], "loop_exception")
        self.assertEqual(events[-1]["status_kind"], "execution_loop_failed")
        self.assertEqual(executed["run"]["metadata"]["execution_fallback"]["status"], "failed")
        self.assertTrue(validate_embedded_sdk_event_payloads(events)["valid"])

    def test_execute_accepts_reflector_and_can_request_revision(self):
        sdk = EmbeddedAgentRuntimeSDK()
        agent = create_agent(name="fraud_assistant", model_name="doubao", sdk=sdk)
        run = agent.run("初步评估交易")

        def reflector(run_context):
            if run_context.iteration == 1:
                return {"reflector": "risk_self_check", "status": "revise", "summary": "补充证据链"}
            return {"reflector": "risk_self_check", "status": "accepted", "summary": "证据链完整"}

        executed = agent.execute(
            run["run"]["run_id"],
            reflector=reflector,
            max_iterations=2,
        )

        self.assertEqual(executed["run"]["state"], "done")
        self.assertEqual(executed["run"]["iteration"], 2)
        self.assertEqual(len(executed["run"]["metadata"]["execution_reflections"]), 2)
        self.assertTrue(
            any(
                event["status_kind"] == "execution_loop_revision_requested"
                for event in agent.stream(run["run"]["run_id"])
            )
        )

    def test_execute_accepts_tool_executor_and_records_tool_history(self):
        sdk = EmbeddedAgentRuntimeSDK()
        agent = create_agent(name="fraud_assistant", model_name="doubao", sdk=sdk)
        run = agent.run("初步评估交易")

        executed = agent.execute(
            run["run"]["run_id"],
            tool_executor=lambda _run: {
                "tool_name": "risk_lookup",
                "args": {"case_id": "case-1"},
                "result": "命中黑名单手机号",
                "tool_call_id": "tool-1",
            },
        )

        self.assertEqual(executed["run"]["state"], "done")
        self.assertEqual(executed["run"]["tool_history"][0]["tool_name"], "risk_lookup")
        self.assertTrue(any(event["type"] == "tool_result" for event in agent.stream(run["run"]["run_id"])))

    def test_register_tool_enables_default_facade_tool_execution_trace(self):
        sdk = EmbeddedAgentRuntimeSDK()
        agent = create_agent(name="fraud_assistant", model_name="doubao", sdk=sdk)

        registered = agent.register_tool(
            ToolSpec(
                name="risk_lookup",
                description="Lookup risk indicators for a case.",
                permission_level="auto",
                deterministic=True,
                tags=("risk",),
            ),
            handler=lambda args: f"命中风险标签: {args['case_id']}",
        )
        run = agent.run("初步评估交易")

        executed = agent.execute(
            run["run"]["run_id"],
            tool_policy=lambda _run: {
                "status": "allowed",
                "tool_name": "risk_lookup",
                "tool_args": {"case_id": "case-1"},
            },
        )

        tool_history = executed["run"]["tool_history"]
        self.assertEqual(registered["tool_spec"]["name"], "risk_lookup")
        self.assertEqual(tool_history[0]["tool_name"], "risk_lookup")
        self.assertEqual(tool_history[0]["result"], "命中风险标签: case-1")
        self.assertEqual(tool_history[0]["execution"]["executor"], "agent_harness_facade_registered_tool")
        self.assertEqual(tool_history[0]["execution"]["action"]["tool_name"], "risk_lookup")
        self.assertEqual(tool_history[0]["execution"]["action"]["args"], {"case_id": "case-1"})
        self.assertEqual(tool_history[0]["execution"]["observation"]["status"], "ok")
        self.assertEqual(tool_history[0]["execution"]["observation"]["result_text"], "命中风险标签: case-1")
        self.assertEqual(tool_history[0]["execution"]["tool_spec"]["permission_level"], "auto")
        tool_events = list(agent.stream(run["run"]["run_id"]))
        result_events = [event for event in tool_events if event["type"] == "tool_result"]
        self.assertEqual(result_events[0]["payload"]["execution"]["action"]["tool_name"], "risk_lookup")
        self.assertEqual(result_events[0]["payload"]["execution"]["observation"]["status"], "ok")

    def test_register_tool_updates_facade_contract_and_tool_runtime_registry(self):
        tool_registry = ToolRegistry()
        tool_runtime_service = ToolRuntimeService(
            tool_registry=tool_registry,
            mcp_registry_service=Mock(build_capability_catalog=Mock(return_value={"capabilities": []})),
            framework_adapter_registry=Mock(build_health_entries=Mock(return_value=[])),
        )
        agent = create_agent(
            name="fraud_assistant",
            model_name="doubao",
            sdk=EmbeddedAgentRuntimeSDK(),
            tool_runtime_service=tool_runtime_service,
        )

        registered = agent.register_tool(
            {
                "name": "risk_lookup",
                "description": "Lookup risk indicators for a case.",
                "permission_level": "auto",
                "deterministic": True,
                "render_mode": "plain_text",
                "tags": ["risk"],
            },
            handler=lambda args: args["case_id"],
        )
        contract = agent.build_contract()
        runtime_contract = tool_runtime_service.build_runtime_contract()

        self.assertEqual(registered["status"], "registered")
        self.assertEqual(contract["facade_runtime_posture"], "embedded_harness_v1_candidate")
        self.assertTrue(contract["tool_registry_bridge"]["local_tool_spec_registry"])
        self.assertEqual(contract["tool_registry_bridge"]["registered_tool_count"], 1)
        self.assertEqual(contract["tool_registry_bridge"]["registered_tool_names"], ["risk_lookup"])
        self.assertTrue(contract["default_tool_executor"]["available"])
        self.assertEqual(runtime_contract["tool_spec_count"], 1)
        self.assertEqual(runtime_contract["tools"][0]["name"], "risk_lookup")

    def test_execute_can_use_tool_runtime_service_when_no_local_handler_exists(self):
        class _RuntimeTool:
            name = "risk_lookup"
            description = "Lookup risk indicators."
            parameters = {"case_id": {"type": "string", "required": True}}

            def invoke(self, args):
                return f"命中风险标签: {args['case_id']}"

        class _RuntimeRegistry(ToolRegistry):
            def __init__(self):
                super().__init__()
                self.tool = _RuntimeTool()

            def list_all(self):
                return [self.tool]

            def get(self, name):
                if name == self.tool.name:
                    return self.tool
                return None

        tool_registry = _RuntimeRegistry()
        tool_registry.register_tool_spec(
            ToolSpec(
                name="risk_lookup",
                description="Lookup risk indicators.",
                permission_level="auto",
                deterministic=True,
                tags=("risk",),
            )
        )
        tool_runtime_service = ToolRuntimeService(
            tool_registry=tool_registry,
            mcp_registry_service=Mock(build_capability_catalog=Mock(return_value={"capabilities": []})),
            framework_adapter_registry=Mock(build_health_entries=Mock(return_value=[])),
        )
        agent = create_agent(
            name="fraud_assistant",
            model_name="doubao",
            sdk=EmbeddedAgentRuntimeSDK(),
            tool_runtime_service=tool_runtime_service,
        )
        run = agent.run("初步评估交易")

        executed = agent.execute(
            run["run"]["run_id"],
            tool_policy=lambda _run: {
                "status": "allowed",
                "tool_name": "risk_lookup",
                "tool_args": {"case_id": "case-1"},
            },
        )

        history = executed["run"]["tool_history"]
        self.assertEqual(history[0]["tool_name"], "risk_lookup")
        self.assertEqual(history[0]["result"], "命中风险标签: case-1")
        self.assertEqual(history[0]["execution"]["executor"], "tool_runtime_service")
        self.assertEqual(history[0]["execution"]["schema_validation"]["status"], "passed")
        self.assertEqual(history[0]["execution"]["observation"]["status"], "ok")
        self.assertTrue(any(event["type"] == "tool_result" for event in agent.stream(run["run"]["run_id"])))

    def test_execute_maps_tool_runtime_ask_policy_to_sdk_approval_before_invocation(self):
        class _RuntimeTool:
            name = "filesystem_write"
            description = "Write file."
            parameters = {"path": {"type": "string", "required": True}}

            def __init__(self):
                self.calls = []

            def invoke(self, args):
                self.calls.append(dict(args))
                return "written"

        class _RuntimeRegistry(ToolRegistry):
            def __init__(self):
                super().__init__()
                self.tool = _RuntimeTool()

            def list_all(self):
                return [self.tool]

            def get(self, name):
                if name == self.tool.name:
                    return self.tool
                return None

        tool_registry = _RuntimeRegistry()
        tool_registry.register_tool_spec(
            ToolSpec(
                name="filesystem_write",
                description="Write file.",
                permission_level="ask",
                deterministic=False,
                tags=("filesystem", "write"),
            )
        )
        tool_runtime_service = ToolRuntimeService(
            tool_registry=tool_registry,
            mcp_registry_service=Mock(build_capability_catalog=Mock(return_value={"capabilities": []})),
            framework_adapter_registry=Mock(build_health_entries=Mock(return_value=[])),
        )
        agent = create_agent(
            name="fraud_assistant",
            model_name="doubao",
            sdk=EmbeddedAgentRuntimeSDK(),
            tool_runtime_service=tool_runtime_service,
        )
        run = agent.run("写入报告")

        executed = agent.execute(
            run["run"]["run_id"],
            tool_policy=lambda _run: {
                "status": "allowed",
                "tool_name": "filesystem_write",
                "tool_args": {"path": "case.md"},
            },
        )

        self.assertEqual(executed["run"]["state"], "waiting_approval")
        self.assertEqual(executed["run"]["stop_reason"], "tool_approval_required")
        self.assertEqual(executed["approval_request"]["tool_name"], "filesystem_write")
        self.assertEqual(executed["approval_request"]["permission_level"], "ask")
        self.assertEqual(executed["approval_request"]["reason_code"], "permission_level_requires_approval")
        self.assertEqual(tool_registry.tool.calls, [])
        self.assertFalse(any(event["type"] == "tool_result" for event in agent.stream(run["run"]["run_id"])))

    def test_approved_tool_runtime_ask_policy_resumes_and_executes_tool_once(self):
        class _RuntimeTool:
            name = "filesystem_write"
            description = "Write file."
            parameters = {"path": {"type": "string", "required": True}}

            def __init__(self):
                self.calls = []

            def invoke(self, args):
                self.calls.append(dict(args))
                return f"written:{args['path']}"

        class _RuntimeRegistry(ToolRegistry):
            def __init__(self):
                super().__init__()
                self.tool = _RuntimeTool()

            def list_all(self):
                return [self.tool]

            def get(self, name):
                if name == self.tool.name:
                    return self.tool
                return None

        tool_registry = _RuntimeRegistry()
        tool_registry.register_tool_spec(
            ToolSpec(
                name="filesystem_write",
                description="Write file.",
                permission_level="ask",
                deterministic=False,
                tags=("filesystem", "write"),
            )
        )
        tool_runtime_service = ToolRuntimeService(
            tool_registry=tool_registry,
            mcp_registry_service=Mock(build_capability_catalog=Mock(return_value={"capabilities": []})),
            framework_adapter_registry=Mock(build_health_entries=Mock(return_value=[])),
        )
        agent = create_agent(
            name="fraud_assistant",
            model_name="doubao",
            sdk=EmbeddedAgentRuntimeSDK(),
            tool_runtime_service=tool_runtime_service,
        )
        run = agent.run("写入报告")
        executed = agent.execute(
            run["run"]["run_id"],
            tool_policy=lambda _run: {
                "status": "allowed",
                "tool_name": "filesystem_write",
                "tool_args": {"path": "case.md"},
            },
        )

        approved = agent.approve(executed["approval_request"]["request_id"], "approved")

        self.assertEqual(approved["approval_request"]["status"], "approved")
        self.assertEqual(tool_registry.tool.calls, [{"path": "case.md"}])
        self.assertEqual(approved["run"]["tool_history"][0]["tool_name"], "filesystem_write")
        self.assertEqual(approved["run"]["tool_history"][0]["result"], "written:case.md")
        policy_decision = approved["run"]["tool_history"][0]["execution"]["policy_decision"]
        self.assertEqual(policy_decision["status"], "allowed")
        self.assertEqual(policy_decision["original_status"], "approval_required")
        self.assertEqual(policy_decision["override"]["status"], "approved")

    def test_execute_maps_tool_runtime_deny_policy_to_failed_run_before_invocation(self):
        class _RuntimeTool:
            name = "dangerous_delete"
            description = "Delete file."
            parameters = {"path": {"type": "string", "required": True}}

            def __init__(self):
                self.calls = []

            def invoke(self, args):
                self.calls.append(dict(args))
                return "deleted"

        class _RuntimeRegistry(ToolRegistry):
            def __init__(self):
                super().__init__()
                self.tool = _RuntimeTool()

            def list_all(self):
                return [self.tool]

            def get(self, name):
                if name == self.tool.name:
                    return self.tool
                return None

        tool_registry = _RuntimeRegistry()
        tool_registry.register_tool_spec(
            ToolSpec(
                name="dangerous_delete",
                description="Delete file.",
                permission_level="deny",
                deterministic=False,
                tags=("filesystem", "delete"),
            )
        )
        tool_runtime_service = ToolRuntimeService(
            tool_registry=tool_registry,
            mcp_registry_service=Mock(build_capability_catalog=Mock(return_value={"capabilities": []})),
            framework_adapter_registry=Mock(build_health_entries=Mock(return_value=[])),
        )
        agent = create_agent(
            name="fraud_assistant",
            model_name="doubao",
            sdk=EmbeddedAgentRuntimeSDK(),
            tool_runtime_service=tool_runtime_service,
        )
        run = agent.run("删除报告")

        executed = agent.execute(
            run["run"]["run_id"],
            tool_policy=lambda _run: {
                "status": "allowed",
                "tool_name": "dangerous_delete",
                "tool_args": {"path": "case.md"},
            },
        )

        self.assertEqual(executed["run"]["state"], "failed")
        self.assertEqual(executed["run"]["stop_reason"], "tool_policy_denied")
        self.assertEqual(executed["run"]["tool_history"], [])
        self.assertEqual(tool_registry.tool.calls, [])
        denied_events = [
            event
            for event in agent.stream(run["run"]["run_id"])
            if event.get("status_kind") == "tool_permission_denied"
        ]
        self.assertEqual(denied_events[0]["tool_decision"]["metadata"]["reason_code"], "permission_level_denied")

    def test_execute_accepts_tool_policy_and_pauses_before_tool_execution(self):
        sdk = EmbeddedAgentRuntimeSDK()
        agent = create_agent(name="fraud_assistant", model_name="doubao", sdk=sdk)
        run = agent.run("初步评估交易")

        executed = agent.execute(
            run["run"]["run_id"],
            tool_policy=lambda _run: {
                "status": "approval_required",
                "tool_name": "risk_lookup",
                "reason": "高风险工具需要审批",
                "metadata": {"permission_level": "ask"},
            },
            tool_executor=lambda _run: {
                "tool_name": "risk_lookup",
                "result": "不应该执行",
            },
        )

        self.assertEqual(executed["run"]["state"], "waiting_approval")
        self.assertEqual(executed["run"]["stop_reason"], "tool_approval_required")
        self.assertEqual(executed["run"]["tool_history"], [])
        self.assertTrue(
            any(event["type"] == "tool_permission_required" for event in agent.stream(run["run"]["run_id"]))
        )
        self.assertFalse(any(event["type"] == "tool_result" for event in agent.stream(run["run"]["run_id"])))

    def test_execute_tool_policy_approval_can_be_submitted_through_facade(self):
        sdk = EmbeddedAgentRuntimeSDK()
        agent = create_agent(
            name="fraud_assistant",
            model_name="doubao",
            sdk=sdk,
            default_user_id=7,
            default_conversation_id=42,
        )
        run = agent.run("初步评估交易", metadata={"agent_role": "fraud_assistant"})

        executed = agent.execute(
            run["run"]["run_id"],
            tool_policy=lambda _run: {
                "status": "approval_required",
                "tool_name": "filesystem_write",
                "tool_args": {"path": "case.md"},
                "reason": "高风险写文件工具需要人工审批",
                "metadata": {"reason_code": "high_risk_tool_requires_approval"},
            },
            tool_executor=lambda _run: {
                "tool_name": "filesystem_write",
                "args": {"path": "case.md"},
                "result": "写入成功",
                "tool_call_id": "tool-after-approval",
            },
        )

        approval = executed["approval_request"]
        self.assertEqual(executed["run"]["state"], "waiting_approval")
        self.assertEqual(approval["tool_name"], "filesystem_write")
        self.assertEqual(approval["tool_args"], {"path": "case.md"})

        approved = agent.approve(approval["request_id"], "approved")

        self.assertEqual(approved["approval_request"]["status"], "approved")
        self.assertEqual(approved["run"]["state"], "observing")
        self.assertEqual(approved["run"]["tool_history"][0]["tool_name"], "filesystem_write")
        self.assertEqual(approved["run"]["tool_history"][0]["result"], "写入成功")
        self.assertTrue(
            any(event["status_kind"] == "approval_resolved" for event in agent.stream(run["run"]["run_id"]))
        )
        self.assertTrue(
            any(event["status_kind"] == "tool_approval_continued" for event in agent.stream(run["run"]["run_id"]))
        )

    def test_resume_can_continue_loop_after_tool_approval(self):
        sdk = EmbeddedAgentRuntimeSDK()
        agent = create_agent(name="fraud_assistant", model_name="doubao", sdk=sdk)
        run = agent.run("写入风险报告")

        executed = agent.execute(
            run["run"]["run_id"],
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
        agent.approve(executed["approval_request"]["request_id"], "approved")

        resumed = agent.resume(run["run"]["run_id"], continue_loop=True)

        self.assertEqual(resumed["run"]["state"], "done")
        self.assertEqual(resumed["run"]["metadata"]["execution_review"]["status"], "approved")
        self.assertEqual(list(agent.stream(run["run"]["run_id"]))[-1]["status_kind"], "execution_loop_done")

    def test_execute_can_use_policy_engine_tool_policy_adapter(self):
        sdk = EmbeddedAgentRuntimeSDK()
        agent = create_agent(name="fraud_assistant", model_name="doubao", sdk=sdk)
        run = agent.run("写入风险报告")

        executed = agent.execute(
            run["run"]["run_id"],
            tool_policy=build_policy_engine_tool_policy(
                tool_name="mcp_filesystem_write",
                tool_args={"path": "case.md"},
            ),
            tool_executor=lambda _run: {
                "tool_name": "mcp_filesystem_write",
                "result": "不应该执行",
            },
        )

        self.assertEqual(executed["run"]["state"], "waiting_approval")
        self.assertEqual(executed["approval_request"]["tool_name"], "mcp_filesystem_write")
        self.assertEqual(executed["approval_request"]["reason_code"], "high_risk_tool_requires_approval")
        self.assertFalse(any(event["type"] == "tool_result" for event in agent.stream(run["run"]["run_id"])))


if __name__ == "__main__":
    unittest.main()
