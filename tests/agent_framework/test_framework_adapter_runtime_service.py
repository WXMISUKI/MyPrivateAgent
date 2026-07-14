import unittest
from unittest.mock import patch

from backend.agent_framework.framework_adapters import AgentFrameworkAdapterRegistry, LangGraphDraftAdapter, LocalFakeFrameworkAdapter, NoopFrameworkAdapter
from backend.services.framework_adapter_runtime_service import FrameworkAdapterRuntimeService


class _StubRunTraceService:
    trace_calls = []
    audit_calls = []
    snapshot_calls = []
    existing_runtime_trace_dedupe_keys = set()

    def append_runtime_trace(self, **kwargs):
        self.__class__.trace_calls.append(kwargs)
        payload = kwargs.get("payload") if isinstance(kwargs.get("payload"), dict) else {}
        if payload.get("dedupe_key"):
            self.__class__.existing_runtime_trace_dedupe_keys.add(payload["dedupe_key"])
        return True

    def append_runtime_audit(self, **kwargs):
        self.__class__.audit_calls.append(kwargs)
        return True

    def has_runtime_trace_dedupe_key(self, **kwargs):
        return kwargs.get("dedupe_key") in self.__class__.existing_runtime_trace_dedupe_keys

    def build_snapshot_ref(self, **kwargs):
        self.__class__.snapshot_calls.append(kwargs)
        return {
            "snapshot_id": "FRAM-FRAMEWORK_A-99-20260511000000",
            "generated_at": "2026-05-11T00:00:00Z",
            **kwargs,
        }


class _StubExternalPilotTransport:
    def probe(self, *, endpoint, timeout_seconds, headers, assistant_id=None):
        return {"status_code": 200, "assistant_exists": True, "assistant_id": assistant_id}

    def invoke(self, *, endpoint, payload, timeout_seconds, headers):
        return {
            "status": "completed",
            "output": {"content": "LangGraph external answer"},
        }

    def stream(self, *, endpoint, payload, timeout_seconds, headers):
        yield {"type": "status", "status": "accepted", "detail": "external runtime accepted"}
        yield {"type": "reasoning", "summary": "external runtime reasoning", "detail": "node=planner"}


class FrameworkAdapterRuntimeServiceTests(unittest.TestCase):
    def setUp(self):
        _StubRunTraceService.trace_calls = []
        _StubRunTraceService.audit_calls = []
        _StubRunTraceService.snapshot_calls = []
        _StubRunTraceService.existing_runtime_trace_dedupe_keys = set()
        self.service = FrameworkAdapterRuntimeService(
            framework_adapter_registry=AgentFrameworkAdapterRegistry([LocalFakeFrameworkAdapter()])
        )

    @patch("backend.services.framework_adapter_runtime_service.get_run_trace_service", return_value=_StubRunTraceService())
    def test_execute_adapter_run_appends_trace_and_audit_events(self, _mock_trace_service):
        result = self.service.execute_adapter_run(
            adapter_id="local_fake_framework",
            run_id="run-c2-service-1",
            messages=[{"role": "user", "content": "生成巡检计划"}],
            execution_context={
                "plan_id": 10,
                "plan_item_id": 24,
                "run_kind": "framework_adapter",
                "child_run_id": "backend-run-1",
                "child_display_id": "backend-run-1",
            },
            db=object(),
            user_id=1,
            conversation_id=99,
        )

        self.assertEqual(result["adapter_id"], "local_fake_framework")
        self.assertEqual(len(result["events"]), 3)
        self.assertEqual(result["final_output"], "Local fake adapter processed: 生成巡检计划")
        self.assertEqual(len(_StubRunTraceService.trace_calls), 3)
        self.assertEqual(_StubRunTraceService.trace_calls[0]["event_type"], "framework_adapter_status")
        self.assertEqual(_StubRunTraceService.trace_calls[1]["event_type"], "framework_adapter_reasoning")
        self.assertEqual(_StubRunTraceService.trace_calls[2]["event_type"], "framework_adapter_output")
        self.assertEqual(_StubRunTraceService.trace_calls[2]["payload"]["adapter_id"], "local_fake_framework")
        self.assertEqual(_StubRunTraceService.trace_calls[0]["payload"]["child_run_id"], "backend-run-1")
        self.assertEqual(_StubRunTraceService.trace_calls[0]["payload"]["child_display_id"], "backend-run-1")
        self.assertEqual(
            _StubRunTraceService.trace_calls[2]["payload"]["snapshot_ref"]["snapshot_id"],
            "FRAM-FRAMEWORK_A-99-20260511000000",
        )
        self.assertEqual(len(_StubRunTraceService.audit_calls), 1)
        self.assertEqual(_StubRunTraceService.audit_calls[0]["event_type"], "framework_adapter_run_completed")
        self.assertEqual(_StubRunTraceService.audit_calls[0]["payload"]["child_display_id"], "backend-run-1")
        self.assertEqual(
            _StubRunTraceService.audit_calls[0]["payload"]["snapshot_ref"]["snapshot_id"],
            "FRAM-FRAMEWORK_A-99-20260511000000",
        )
        self.assertEqual(result["snapshot_ref"]["snapshot_id"], "FRAM-FRAMEWORK_A-99-20260511000000")

    def test_execute_adapter_run_raises_when_adapter_is_missing(self):
        with self.assertRaises(ValueError):
            self.service.execute_adapter_run(
                adapter_id="missing_adapter",
                run_id="run-c2-missing",
                messages=[{"role": "user", "content": "test"}],
            )

    def test_adapter_authoring_checklist_reports_ready_pilot_candidate(self):
        result = self.service.build_adapter_authoring_checklist(
            adapter_id="local_fake_framework",
        )

        self.assertEqual(result["contract_version"], "framework-adapter-authoring-checklist-v1")
        self.assertEqual(result["adapter_id"], "local_fake_framework")
        self.assertEqual(result["checklist_status"], "ready")
        self.assertEqual(result["promotion_review"]["status"], "pilot_candidate")
        self.assertEqual(result["promotion_review"]["will_execute"], False)
        self.assertEqual(result["promotion_review"]["default_chat_entry"], "disabled")
        self.assertEqual(result["authoring_sections"]["lifecycle_mapping"]["query_control_channel"], "external_adapter")
        self.assertIn("framework_adapter_status", result["authoring_sections"]["lifecycle_mapping"]["required_events"])
        self.assertEqual(
            result["authoring_template"]["template_version"],
            "framework-adapter-authoring-template-v1",
        )
        self.assertEqual(result["authoring_template"]["adapter_id"], "local_fake_framework")
        self.assertEqual(result["authoring_template"]["registration_status"], "registered")
        self.assertEqual(result["authoring_template"]["boundaries"]["default_chat_entry"], "disabled")
        self.assertEqual(result["boundary"]["adapter_execution"], "not_performed")
        self.assertEqual(result["boundary"]["trace_write"], "not_performed")
        self.assertEqual(result["boundary"]["audit_write"], "not_performed")
        self.assertFalse(_StubRunTraceService.trace_calls)
        self.assertFalse(_StubRunTraceService.audit_calls)

    def test_adapter_authoring_template_maps_runtime_plane_proof_to_projection_profile(self):
        result = self.service.build_adapter_authoring_checklist(
            adapter_id="local_fake_framework",
        )

        template = result["authoring_template"]
        proof_slices = {
            mapping["proof_slice"]: mapping
            for mapping in template["runtime_plane_mapping"]
        }
        required_contract_names = {
            contract["name"]
            for contract in template["required_contracts"]
        }

        self.assertEqual(
            set(proof_slices),
            {"simple_agent", "tool_agent", "approval_agent"},
        )
        self.assertIn("request/event/result envelope", proof_slices["simple_agent"]["validates"])
        self.assertIn("controlled read-only tool", proof_slices["tool_agent"]["validates"])
        self.assertIn("approval_pending", proof_slices["approval_agent"]["validates"])
        self.assertIn("AgentFrameworkAdapter", required_contract_names)
        self.assertIn("ExecutionRequest", required_contract_names)
        self.assertIn("ExecutionEvent", required_contract_names)
        self.assertIn("ExecutionResult", required_contract_names)
        self.assertIn("runtime_plane_governance_profile", required_contract_names)
        self.assertEqual(
            template["projection_mapping"]["runtime_surface_profile"],
            "runtime_plane_governance_profile",
        )
        self.assertTrue(template["projection_mapping"]["read_model_only"])
        self.assertIn(
            "checklist_generation_does_not_write_trace_or_audit",
            template["minimum_smoke_tests"],
        )
        self.assertIn(
            "default_chat_entry_remains_disabled",
            template["promotion_gate_requirements"],
        )

    @patch("backend.agent_framework.framework_adapters._is_python_package_available", return_value=False)
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_RUNTIME_ENDPOINT", "")
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_ASSISTANT_ID", "")
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_RUNTIME_EXECUTION", False)
    def test_adapter_authoring_checklist_blocks_on_precheck_evidence(self, *_mocks):
        service = FrameworkAdapterRuntimeService(
            framework_adapter_registry=AgentFrameworkAdapterRegistry([LangGraphDraftAdapter()])
        )

        result = service.build_adapter_authoring_checklist(adapter_id="langgraph_draft")

        self.assertEqual(result["checklist_status"], "blocked")
        self.assertEqual(result["promotion_review"]["status"], "blocked")
        self.assertEqual(result["promotion_review"]["default_chat_entry"], "disabled")
        self.assertEqual(result["authoring_template"]["adapter_id"], "langgraph_draft")
        self.assertEqual(result["authoring_template"]["target_framework"], "LangGraph")
        self.assertEqual(result["authoring_template"]["registration_status"], "registered")
        self.assertEqual(result["authoring_template"]["boundaries"]["will_execute"], False)
        self.assertIn("langgraph", result["precheck_summary"]["missing_packages"])
        self.assertIn("LANGGRAPH_RUNTIME_ENDPOINT", result["precheck_summary"]["missing_env"])
        self.assertIn(
            {
                "component": "readiness",
                "status": "blocked",
                "reason_code": "missing_package",
                "detail": "langgraph",
            },
            result["promotion_review"]["blockers"],
        )

    def test_adapter_authoring_checklist_blocks_unknown_adapter(self):
        result = self.service.build_adapter_authoring_checklist(adapter_id="missing_adapter")

        self.assertEqual(result["checklist_status"], "blocked")
        self.assertEqual(result["promotion_review"]["status"], "blocked")
        self.assertEqual(result["promotion_review"]["will_execute"], False)
        self.assertEqual(result["promotion_review"]["default_chat_entry"], "disabled")
        self.assertEqual(result["authoring_template"]["adapter_id"], "missing_adapter")
        self.assertEqual(result["authoring_template"]["registration_status"], "missing")
        self.assertEqual(
            result["authoring_template"]["next_action"],
            "register_adapter_before_authoring_review",
        )
        self.assertEqual(result["authoring_template"]["boundaries"]["external_framework_call"], "not_performed")
        self.assertIn(
            "adapter_registered",
            result["authoring_template"]["promotion_gate_requirements"],
        )
        self.assertIn(
            {
                "component": "adapter_registry",
                "status": "blocked",
                "reason_code": "adapter_not_registered",
                "detail": "missing_adapter",
            },
            result["promotion_review"]["blockers"],
        )
        self.assertEqual(result["boundary"]["external_framework_call"], "not_performed")
        self.assertFalse(_StubRunTraceService.trace_calls)
        self.assertFalse(_StubRunTraceService.audit_calls)

    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_EXTERNAL_PILOT", True)
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_RUNTIME_EXECUTION", True)
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_RUNTIME_ENDPOINT", "http://localhost:8123/langgraph")
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_ASSISTANT_ID", "assistant-1")
    @patch("backend.agent_framework.framework_adapters._is_python_package_available", return_value=True)
    def test_langgraph_controlled_pilot_readiness_reports_ready_without_execution(self, *_mocks):
        service = FrameworkAdapterRuntimeService(
            framework_adapter_registry=AgentFrameworkAdapterRegistry([LangGraphDraftAdapter()])
        )

        result = service.build_langgraph_controlled_pilot_readiness()

        self.assertEqual(result["contract_version"], "langgraph-controlled-pilot-readiness-v1")
        self.assertEqual(result["adapter_id"], "langgraph_draft")
        self.assertEqual(result["framework_name"], "LangGraph")
        self.assertEqual(result["readiness_status"], "ready")
        self.assertEqual(result["can_start_controlled_pilot"], True)
        self.assertEqual(result["next_allowed_action"], "run_explicit_controlled_pilot_smoke")
        self.assertEqual(result["pilot_target"]["run_kind"], "framework_adapter_external_pilot")
        self.assertEqual(result["precheck_summary"]["ready"], True)
        self.assertEqual(result["authoring_template_summary"]["runtime_surface_profile"], "runtime_plane_governance_profile")
        self.assertEqual(
            set(result["authoring_template_summary"]["stage_1_proof_mapping"]),
            {"simple_agent", "tool_agent", "approval_agent"},
        )
        self.assertIn("langgraph_external_pilot_enabled", result["required_gates"])
        self.assertEqual(result["blockers"], [])
        self.assertEqual(result["boundaries"]["will_execute"], False)
        self.assertEqual(result["boundaries"]["external_framework_call"], "not_performed")
        self.assertEqual(result["boundaries"]["trace_write"], "not_performed")
        self.assertEqual(result["boundaries"]["audit_write"], "not_performed")
        self.assertEqual(result["boundaries"]["default_chat_entry"], "disabled")
        self.assertFalse(_StubRunTraceService.trace_calls)
        self.assertFalse(_StubRunTraceService.audit_calls)

    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_EXTERNAL_PILOT", False)
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_RUNTIME_EXECUTION", True)
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_RUNTIME_ENDPOINT", "http://localhost:8123/langgraph")
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_ASSISTANT_ID", "assistant-1")
    @patch("backend.agent_framework.framework_adapters._is_python_package_available", return_value=True)
    def test_langgraph_controlled_pilot_readiness_blocks_when_external_pilot_disabled(self, *_mocks):
        service = FrameworkAdapterRuntimeService(
            framework_adapter_registry=AgentFrameworkAdapterRegistry([LangGraphDraftAdapter()])
        )

        result = service.build_langgraph_controlled_pilot_readiness()

        self.assertEqual(result["readiness_status"], "blocked")
        self.assertEqual(result["can_start_controlled_pilot"], False)
        self.assertEqual(result["next_allowed_action"], "resolve_controlled_pilot_blockers")
        self.assertEqual(result["precheck_summary"]["execution_block_reason"], "external pilot is not enabled")
        self.assertIn(
            {
                "component": "execution_gate",
                "status": "blocked",
                "reason_code": "execution_blocked",
                "detail": "external pilot is not enabled",
            },
            result["blockers"],
        )
        self.assertEqual(result["boundaries"]["external_framework_call"], "not_performed")
        self.assertFalse(_StubRunTraceService.trace_calls)
        self.assertFalse(_StubRunTraceService.audit_calls)

    def test_langgraph_controlled_pilot_readiness_blocks_unknown_adapter(self):
        result = self.service.build_langgraph_controlled_pilot_readiness(adapter_id="missing_adapter")

        self.assertEqual(result["readiness_status"], "blocked")
        self.assertEqual(result["can_start_controlled_pilot"], False)
        self.assertIn(
            {
                "component": "adapter_registry",
                "status": "blocked",
                "reason_code": "adapter_not_registered",
                "detail": "missing_adapter",
            },
            result["blockers"],
        )
        self.assertEqual(result["boundaries"]["will_execute"], False)
        self.assertEqual(result["boundaries"]["trace_write"], "not_performed")
        self.assertFalse(_StubRunTraceService.trace_calls)
        self.assertFalse(_StubRunTraceService.audit_calls)

    def test_langgraph_controlled_pilot_readiness_blocks_registered_non_langgraph_adapter(self):
        result = self.service.build_langgraph_controlled_pilot_readiness(adapter_id="local_fake_framework")

        self.assertEqual(result["readiness_status"], "blocked")
        self.assertEqual(result["can_start_controlled_pilot"], False)
        self.assertIn(
            {
                "component": "pilot_target",
                "status": "blocked",
                "reason_code": "unsupported_controlled_pilot_target",
                "detail": "LangGraph controlled pilot readiness only supports `langgraph_draft`",
            },
            result["blockers"],
        )
        self.assertEqual(result["boundaries"]["default_chat_entry"], "disabled")
        self.assertFalse(_StubRunTraceService.trace_calls)
        self.assertFalse(_StubRunTraceService.audit_calls)

    def test_execute_adapter_run_rejects_registered_placeholder_adapter(self):
        service = FrameworkAdapterRuntimeService(
            framework_adapter_registry=AgentFrameworkAdapterRegistry([
                NoopFrameworkAdapter(
                    adapter_id="langgraph_draft",
                    framework_name="LangGraph",
                    required_env=("LANGGRAPH_RUNTIME_ENDPOINT",),
                    detail="LangGraph draft adapter is registered as a Phase D-0 placeholder; runtime execution is not enabled.",
                )
            ])
        )

        with self.assertRaises(ValueError) as ctx:
            service.execute_adapter_run(
                adapter_id="langgraph_draft",
                run_id="run-d0-langgraph",
                messages=[{"role": "user", "content": "test"}],
            )

        self.assertIn("runtime execution is not enabled", str(ctx.exception))

    @patch("backend.services.framework_adapter_runtime_service.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_EXTERNAL_PILOT", True)
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_RUNTIME_EXECUTION", True)
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_RUNTIME_ENDPOINT", "http://localhost:8123/langgraph")
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_ASSISTANT_ID", "assistant-1")
    @patch("backend.agent_framework.framework_adapters._is_python_package_available", return_value=True)
    def test_execute_external_adapter_run_appends_trace_and_audit_events(self, *_mocks):
        service = FrameworkAdapterRuntimeService(
            framework_adapter_registry=AgentFrameworkAdapterRegistry([LangGraphDraftAdapter()]),
            external_pilot_transport=_StubExternalPilotTransport(),
        )

        result = service.execute_external_adapter_run(
            adapter_id="langgraph_draft",
            run_id="run-external-2",
            messages=[{"role": "user", "content": "生成总结"}],
            execution_context={
                "plan_id": 10,
                "plan_item_id": 24,
                "run_kind": "framework_adapter_external_pilot",
                "child_run_id": "backend-run-2",
                "child_display_id": "backend-run-2",
            },
            db=object(),
            user_id=1,
            conversation_id=99,
        )

        self.assertEqual(result["adapter_id"], "langgraph_draft")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["final_output"], "LangGraph external answer")
        self.assertTrue(result["events"])
        self.assertEqual(len(_StubRunTraceService.trace_calls), 3)
        self.assertEqual(_StubRunTraceService.trace_calls[0]["event_type"], "framework_adapter_status")
        self.assertEqual(_StubRunTraceService.trace_calls[1]["event_type"], "framework_adapter_reasoning")
        self.assertEqual(_StubRunTraceService.trace_calls[2]["event_type"], "framework_adapter_output")
        self.assertEqual(_StubRunTraceService.trace_calls[0]["payload"]["child_display_id"], "backend-run-2")
        self.assertEqual(_StubRunTraceService.audit_calls[0]["event_type"], "framework_adapter_external_pilot_completed")
        self.assertEqual(_StubRunTraceService.audit_calls[0]["payload"]["child_display_id"], "backend-run-2")
        self.assertEqual(result["snapshot_ref"]["snapshot_id"], "FRAM-FRAMEWORK_A-99-20260511000000")

    @patch("backend.agent_framework.framework_adapters._is_python_package_available", return_value=False)
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_RUNTIME_ENDPOINT", "")
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_ASSISTANT_ID", "")
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_RUNTIME_EXECUTION", False)
    def test_precheck_adapter_returns_readiness_without_execution(self, *_mocks):
        service = FrameworkAdapterRuntimeService(
            framework_adapter_registry=AgentFrameworkAdapterRegistry([LangGraphDraftAdapter()])
        )

        result = service.precheck_adapter(adapter_id="langgraph_draft")

        self.assertEqual(result["adapter_id"], "langgraph_draft")
        self.assertEqual(result["framework_name"], "LangGraph")
        self.assertEqual(result["ready"], False)
        self.assertEqual(result["configuration_status"], "missing_package")
        self.assertEqual(result["missing_packages"], ["langgraph"])
        self.assertEqual(result["missing_env"], ["LANGGRAPH_RUNTIME_ENDPOINT", "LANGGRAPH_ASSISTANT_ID"])

    @patch("backend.services.framework_adapter_runtime_service.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.agent_framework.framework_adapters._is_python_package_available", return_value=False)
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_RUNTIME_ENDPOINT", "")
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_ASSISTANT_ID", "")
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_RUNTIME_EXECUTION", False)
    def test_precheck_adapter_appends_timeline_records(self, *_mocks):
        _StubRunTraceService.trace_calls = []
        _StubRunTraceService.audit_calls = []
        service = FrameworkAdapterRuntimeService(
            framework_adapter_registry=AgentFrameworkAdapterRegistry([LangGraphDraftAdapter()])
        )

        result = service.precheck_adapter(
            adapter_id="langgraph_draft",
            db=object(),
            user_id=1,
            conversation_id=99,
            execution_context={"plan_id": 10, "plan_item_id": 24},
        )

        self.assertIn("timeline_recording", result)
        self.assertEqual(result["timeline_recording"]["snapshot_ref"]["snapshot_id"], "FRAM-FRAMEWORK_A-99-20260511000000")
        self.assertEqual(len(_StubRunTraceService.trace_calls), 1)
        self.assertEqual(_StubRunTraceService.trace_calls[0]["event_type"], "framework_adapter_precheck_completed")
        self.assertTrue(
            _StubRunTraceService.trace_calls[0]["payload"]["dedupe_key"].startswith(
                "framework_adapter_precheck_completed:99:langgraph_draft:"
            )
        )
        self.assertEqual(len(_StubRunTraceService.audit_calls), 1)
        self.assertEqual(_StubRunTraceService.audit_calls[0]["event_type"], "framework_adapter_precheck_completed")

    @patch("backend.services.framework_adapter_runtime_service.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.agent_framework.framework_adapters._is_python_package_available", return_value=False)
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_RUNTIME_ENDPOINT", "")
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_ASSISTANT_ID", "")
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_RUNTIME_EXECUTION", False)
    def test_precheck_adapter_dedupes_repeated_timeline_records(self, *_mocks):
        service = FrameworkAdapterRuntimeService(
            framework_adapter_registry=AgentFrameworkAdapterRegistry([LangGraphDraftAdapter()])
        )

        first_result = service.precheck_adapter(
            adapter_id="langgraph_draft",
            db=object(),
            user_id=1,
            conversation_id=99,
            execution_context={"plan_id": 10, "plan_item_id": 24},
        )
        second_result = service.precheck_adapter(
            adapter_id="langgraph_draft",
            db=object(),
            user_id=1,
            conversation_id=99,
            execution_context={"plan_id": 10, "plan_item_id": 24},
        )

        self.assertEqual(first_result["timeline_recording"]["trace_written"], True)
        self.assertEqual(second_result["timeline_recording"]["trace_written"], False)
        self.assertEqual(
            second_result["timeline_recording"]["dedupe_source"],
            "persisted_trace",
        )
        self.assertEqual(len(_StubRunTraceService.trace_calls), 1)
        self.assertEqual(len(_StubRunTraceService.audit_calls), 1)

    @patch("backend.services.framework_adapter_runtime_service.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_EXTERNAL_PILOT", False)
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_RUNTIME_EXECUTION", True)
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_RUNTIME_ENDPOINT", "http://localhost:8123/langgraph")
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_ASSISTANT_ID", "assistant-1")
    @patch("backend.agent_framework.framework_adapters._is_python_package_available", return_value=True)
    def test_execute_external_adapter_run_rejects_when_gate_disabled(self, *_mocks):
        service = FrameworkAdapterRuntimeService(
            framework_adapter_registry=AgentFrameworkAdapterRegistry([LangGraphDraftAdapter()])
        )

        with self.assertRaises(ValueError) as ctx:
            service.execute_external_adapter_run(
                adapter_id="langgraph_draft",
                run_id="run-external-1",
                messages=[{"role": "user", "content": "hello"}],
                execution_context={},
                db=object(),
                user_id=1,
                conversation_id=99,
            )

        self.assertEqual(str(ctx.exception), "external pilot is not enabled")


if __name__ == "__main__":
    unittest.main()
