import unittest
from unittest.mock import patch

from backend.agent_framework.framework_adapters import (
    AgentFrameworkAdapterRegistry,
    LangGraphDraftAdapter,
    LocalFakeFrameworkAdapter,
    NoopFrameworkAdapter,
    get_framework_adapter_registry,
)


class FrameworkAdapterSpiTests(unittest.TestCase):
    def test_noop_adapter_declares_health_and_supported_contract(self):
        adapter = NoopFrameworkAdapter(
            adapter_id="deepagents_draft",
            framework_name="DeepAgents-style",
            supported_run_kinds=("chat", "background_task"),
            capability_requirements=("tool_runtime", "approval"),
        )

        health = adapter.health_check().to_dict()

        self.assertEqual(health["adapter_id"], "deepagents_draft")
        self.assertEqual(health["framework_name"], "DeepAgents-style")
        self.assertEqual(health["display_name"], "DeepAgents-style")
        self.assertEqual(health["adapter_type"], "agent_framework")
        self.assertEqual(health["status"], "not_configured")
        self.assertEqual(health["supported_run_kinds"], ["chat", "background_task"])
        self.assertEqual(health["capability_requirements"], ["tool_runtime", "approval"])
        self.assertEqual(health["execution_mode"], "placeholder")
        self.assertEqual(health["runtime_enabled"], False)
        self.assertEqual(health["package_installed"], False)
        self.assertEqual(health["configuration_status"], "not_configured")
        self.assertEqual(health["required_packages"], [])

    def test_noop_adapter_translates_input_and_output_to_platform_contracts(self):
        adapter = NoopFrameworkAdapter(
            adapter_id="crewai_draft",
            framework_name="CrewAI-style",
            capability_requirements=("command_runtime",),
        )

        translated_input = adapter.translate_input(
            run_id="run-1",
            messages=[{"role": "user", "content": "评估这个任务"}],
            execution_context={"tenant_id": "demo"},
        )
        translated_events = adapter.translate_output(
            run_id="run-1",
            output={"content": "adapter output"},
            execution_context={"tenant_id": "demo"},
        )

        self.assertEqual(translated_input["adapter_id"], "crewai_draft")
        self.assertEqual(translated_input["framework_name"], "CrewAI-style")
        self.assertEqual(translated_input["run_id"], "run-1")
        self.assertEqual(translated_input["messages"][0]["content"], "评估这个任务")
        self.assertEqual(translated_input["execution_context"]["tenant_id"], "demo")
        self.assertEqual(len(translated_events), 1)
        self.assertEqual(translated_events[0]["type"], "content")
        self.assertEqual(translated_events[0]["run_id"], "run-1")
        self.assertEqual(translated_events[0]["source"], "framework_adapter")
        self.assertEqual(translated_events[0]["payload"]["adapter_id"], "crewai_draft")
        self.assertEqual(translated_events[0]["payload"]["framework_name"], "CrewAI-style")
        self.assertEqual(translated_events[0]["payload"]["content"], "adapter output")

    def test_registry_builds_contract_and_health_entries(self):
        registry = AgentFrameworkAdapterRegistry()
        registry.register(NoopFrameworkAdapter(
            adapter_id="langgraph_draft",
            framework_name="LangGraph",
            supported_run_kinds=("workflow",),
        ))

        contract = registry.build_runtime_contract()
        health_entries = registry.build_health_entries()

        self.assertEqual(contract["contract_version"], "phase-b-framework-adapter-spi-v1")
        self.assertEqual(contract["adapter_count"], 1)
        self.assertEqual(contract["adapters"][0]["adapter_id"], "langgraph_draft")
        self.assertEqual(contract["adapters"][0]["framework_name"], "LangGraph")
        self.assertEqual(health_entries[0]["adapter_id"], "langgraph_draft")
        self.assertEqual(health_entries[0]["status"], "not_configured")

    def test_local_fake_adapter_pilot_covers_phase_c2_event_lifecycle(self):
        adapter = LocalFakeFrameworkAdapter()

        translated_input = adapter.translate_input(
            run_id="run-c2-1",
            messages=[{"role": "user", "content": "给我一个巡检计划"}],
            execution_context={"tenant_id": "demo"},
        )
        streamed_events = list(adapter.stream_events(
            translated_input=translated_input,
            execution_context={"trace_id": "trace-c2-1"},
        ))
        translated_output = adapter.translate_output(
            run_id="run-c2-1",
            output={"content": "已生成巡检计划草案"},
            execution_context={"tenant_id": "demo"},
        )
        health = adapter.health_check().to_dict()

        self.assertEqual(translated_input["adapter_id"], "local_fake_framework")
        self.assertEqual(translated_input["framework_name"], "LocalFakeFramework")
        self.assertEqual(translated_input["message_count"], 1)
        self.assertEqual(len(streamed_events), 2)
        self.assertEqual(streamed_events[0]["type"], "status")
        self.assertEqual(streamed_events[0]["payload"]["status"], "stream_started")
        self.assertEqual(streamed_events[0]["payload"]["execution_context"]["tenant_id"], "demo")
        self.assertEqual(streamed_events[0]["payload"]["execution_context"]["trace_id"], "trace-c2-1")
        self.assertEqual(streamed_events[1]["type"], "reasoning")
        self.assertEqual(len(translated_output), 1)
        self.assertEqual(translated_output[0]["type"], "content")
        self.assertEqual(translated_output[0]["payload"]["content"], "已生成巡检计划草案")
        self.assertEqual(health["status"], "healthy")
        self.assertEqual(health["adapter_type"], "agent_framework")
        self.assertEqual(health["execution_mode"], "local_fake_pilot")
        self.assertEqual(health["runtime_enabled"], True)
        self.assertEqual(health["package_installed"], True)
        self.assertEqual(health["configuration_status"], "ready")

    @patch("backend.agent_framework.framework_adapters.ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER", True)
    def test_registry_registers_local_fake_adapter_when_flag_enabled(self):
        from backend.agent_framework import framework_adapters as module

        previous_registry = module._framework_adapter_registry
        module._framework_adapter_registry = None
        try:
            registry = get_framework_adapter_registry()
            self.assertIn("local_fake_framework", {item.adapter_id for item in registry.list_adapters()})
        finally:
            module._framework_adapter_registry = previous_registry

    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_DRAFT_ADAPTER", True)
    def test_registry_registers_langgraph_draft_adapter_when_flag_enabled(self):
        from backend.agent_framework import framework_adapters as module

        previous_registry = module._framework_adapter_registry
        module._framework_adapter_registry = None
        try:
            registry = get_framework_adapter_registry()
            by_id = {item.adapter_id: item for item in registry.list_adapters()}
            self.assertIn("langgraph_draft", by_id)
            self.assertEqual(by_id["langgraph_draft"].framework_name, "LangGraph")
            self.assertIsInstance(by_id["langgraph_draft"], LangGraphDraftAdapter)
        finally:
            module._framework_adapter_registry = previous_registry

    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_RUNTIME_EXECUTION", False)
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_RUNTIME_ENDPOINT", "")
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_ASSISTANT_ID", "")
    @patch("backend.agent_framework.framework_adapters._is_python_package_available", return_value=False)
    def test_langgraph_draft_adapter_exposes_configuration_blockers(self, _mock_package_available):
        adapter = LangGraphDraftAdapter()

        health = adapter.health_check().to_dict()

        self.assertEqual(health["adapter_id"], "langgraph_draft")
        self.assertEqual(health["execution_mode"], "draft_external_runtime")
        self.assertEqual(health["configuration_status"], "missing_package")
        self.assertEqual(health["missing_packages"], ["langgraph"])
        self.assertEqual(health["required_packages"], ["langgraph"])
        self.assertEqual(health["missing_env"], ["LANGGRAPH_RUNTIME_ENDPOINT", "LANGGRAPH_ASSISTANT_ID"])
        self.assertEqual(health["required_env"], ["LANGGRAPH_RUNTIME_ENDPOINT", "LANGGRAPH_ASSISTANT_ID"])
        self.assertEqual(health["runtime_enabled"], False)

    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_RUNTIME_EXECUTION", False)
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_RUNTIME_ENDPOINT", "")
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_ASSISTANT_ID", "")
    @patch("backend.agent_framework.framework_adapters._is_python_package_available", return_value=True)
    def test_langgraph_draft_adapter_reports_missing_env_after_package_is_installed(self, _mock_package_available):
        adapter = LangGraphDraftAdapter()

        health = adapter.health_check().to_dict()

        self.assertEqual(health["configuration_status"], "missing_env")
        self.assertEqual(health["missing_packages"], [])
        self.assertEqual(health["missing_env"], ["LANGGRAPH_RUNTIME_ENDPOINT", "LANGGRAPH_ASSISTANT_ID"])
        self.assertEqual(health["execution_block_reason"], "missing required env: LANGGRAPH_RUNTIME_ENDPOINT, LANGGRAPH_ASSISTANT_ID")

    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_EXTERNAL_PILOT", False)
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_RUNTIME_EXECUTION", True)
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_RUNTIME_ENDPOINT", "http://localhost:8123/langgraph")
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_ASSISTANT_ID", "assistant-1")
    @patch("backend.agent_framework.framework_adapters._is_python_package_available", return_value=True)
    def test_langgraph_draft_adapter_ready_does_not_mean_external_pilot_allowed(self, _mock_package_available):
        adapter = LangGraphDraftAdapter()

        health = adapter.health_check().to_dict()
        can_execute, block_reason = adapter.can_execute()

        self.assertEqual(health["configuration_status"], "ready")
        self.assertEqual(health["status"], "healthy")
        self.assertFalse(can_execute)
        self.assertEqual(block_reason, "external pilot is not enabled")

    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_EXTERNAL_PILOT", True)
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_RUNTIME_EXECUTION", True)
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_RUNTIME_ENDPOINT", "http://localhost:8123/langgraph")
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_ASSISTANT_ID", "assistant-1")
    @patch("backend.agent_framework.framework_adapters._is_python_package_available", return_value=True)
    def test_langgraph_draft_adapter_allows_execution_only_when_external_pilot_enabled(self, _mock_package_available):
        adapter = LangGraphDraftAdapter()

        can_execute, block_reason = adapter.can_execute()

        self.assertTrue(can_execute)
        self.assertEqual(block_reason, "")


if __name__ == "__main__":
    unittest.main()
