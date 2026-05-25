import unittest
import time

from backend.agent_framework.tools import ToolRenderMode, ToolSpec
from backend.services.tool_runtime_service import ToolRuntimeService


class _FakeBaseTool:
    def __init__(self, name, description, permission_level="auto"):
        self.name = name
        self.description = description
        self.permission_level = type("PermissionLevel", (), {"value": permission_level})()
        self.parameters = {"query": {"type": "string"}}


class _FakeLangChainTool:
    def __init__(self, name, description):
        self.name = name
        self.description = description


class _FakeRegistry:
    def list_all(self):
        return [_FakeBaseTool("search", "搜索工具")]

    def get_langchain_tools(self):
        return [_FakeLangChainTool("weather_query", "天气查询")]

    def list_tool_specs(self):
        return [
            ToolSpec(
                name="weather_query",
                description="天气查询",
                permission_level="auto",
                render_mode=ToolRenderMode.STRUCTURED_CARD,
                tags=("mcp",),
            ),
            ToolSpec(
                name="mcp_filesystem_write",
                description="写文件",
                permission_level="high_risk",
                tags=("filesystem", "write"),
            ),
        ]

    def get_doubao_tool_definitions(self):
        return [{"type": "function", "function": {"name": "weather_query"}}]


class _FakeMcpRegistryService:
    def build_capability_catalog(self):
        return {
            "capabilities": [
                {"capability": "filesystem.read", "server_names": ["filesystem"]},
                {"capability": "search.query", "server_names": ["search"]},
            ]
        }


class _FakeFrameworkAdapterRegistry:
    def build_health_entries(self):
        return [
            {
                "adapter_id": "deepagents_draft",
                "display_name": "DeepAgents-style",
                "framework_name": "DeepAgents-style",
                "adapter_type": "agent_framework",
                "status": "not_configured",
                "detail": "Adapter SPI reserved; external framework package is not installed.",
                "supported_run_kinds": ["chat", "background_task"],
                "capability_requirements": ["tool_runtime", "approval"],
                "configuration_status": "not_configured",
                "package_installed": False,
                "runtime_enabled": False,
                "execution_mode": "placeholder",
                "required_env": [],
                "missing_env": [],
                "required_packages": [],
                "missing_packages": [],
                "execution_block_reason": "Adapter SPI reserved; external framework package is not installed.",
            }
        ]


class _FakePhaseDFrameworkAdapterRegistry:
    def build_health_entries(self):
        return [
            {
                "adapter_id": "langgraph_draft",
                "display_name": "LangGraph",
                "framework_name": "LangGraph",
                "adapter_type": "agent_framework",
                "status": "not_configured",
                "detail": "LangGraph draft adapter is registered as a Phase D-0 placeholder; runtime execution is not enabled.",
                "supported_run_kinds": ["chat", "workflow"],
                "capability_requirements": ["tool_runtime", "adapter_health", "audit", "runtime_trace"],
                "configuration_status": "missing_package",
                "package_installed": False,
                "runtime_enabled": False,
                "execution_mode": "draft_external_runtime",
                "required_env": ["LANGGRAPH_RUNTIME_ENDPOINT", "LANGGRAPH_ASSISTANT_ID"],
                "missing_env": ["LANGGRAPH_RUNTIME_ENDPOINT", "LANGGRAPH_ASSISTANT_ID"],
                "required_packages": ["langgraph"],
                "missing_packages": ["langgraph"],
                "execution_block_reason": "missing required package: langgraph",
            }
        ]


class _EmptyRegistry:
    def list_all(self):
        return []

    def get_langchain_tools(self):
        return []

    def list_tool_specs(self):
        return []

    def get_doubao_tool_definitions(self):
        return []


class _BrokenRegistry(_EmptyRegistry):
    def list_all(self):
        raise RuntimeError("registry unreadable")


class _BrokenMcpRegistryService:
    def build_capability_catalog(self):
        raise RuntimeError("mcp registry corrupted")


class _AskOnlyRegistry(_EmptyRegistry):
    def list_all(self):
        return [_FakeBaseTool("shell_command", "执行 shell", permission_level="ask")]


class _ExecutableTool:
    name = "risk_lookup"
    description = "风险查询"
    parameters = {"case_id": {"type": "string", "required": True}}

    def __init__(self):
        self.calls = []

    def invoke(self, args):
        self.calls.append(dict(args))
        return f"命中风险: {args['case_id']}"


class _ExecutableRegistry(_EmptyRegistry):
    def __init__(self):
        self.tool = _ExecutableTool()

    def list_all(self):
        return [self.tool]

    def get(self, name):
        if name == self.tool.name:
            return self.tool
        return None

    def get_tool_spec(self, name):
        if name == self.tool.name:
            return ToolSpec(
                name="risk_lookup",
                description="风险查询",
                permission_level="auto",
                render_mode=ToolRenderMode.PLAIN_TEXT,
                tags=("risk",),
            )
        return None


class _PermissionTool:
    name = "permission_probe"
    description = "权限探测"
    parameters = {"case_id": {"type": "string", "required": True}}

    def __init__(self, permission_level):
        self.permission_level = type("PermissionLevel", (), {"value": permission_level})()
        self.calls = []

    def invoke(self, args):
        self.calls.append(dict(args))
        return "executed"


class _PermissionRegistry(_EmptyRegistry):
    def __init__(self, permission_level):
        self.tool = _PermissionTool(permission_level=permission_level)
        self.permission_level = permission_level

    def list_all(self):
        return [self.tool]

    def get(self, name):
        if name == self.tool.name:
            return self.tool
        return None

    def get_tool_spec(self, name):
        if name == self.tool.name:
            return ToolSpec(
                name=self.tool.name,
                description=self.tool.description,
                permission_level=self.permission_level,
                render_mode=ToolRenderMode.PLAIN_TEXT,
                tags=(),
            )
        return None


class _FlakyTool:
    name = "flaky_lookup"
    description = "不稳定查询"
    parameters = {}

    def __init__(self, fail_times=1):
        self.fail_times = fail_times
        self.calls = 0

    def invoke(self, args):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError(f"temporary failure {self.calls}")
        return f"recovered:{args.get('case_id', 'unknown')}"


class _FlakyRegistry(_EmptyRegistry):
    def __init__(self, fail_times=1):
        self.tool = _FlakyTool(fail_times=fail_times)

    def list_all(self):
        return [self.tool]

    def get(self, name):
        if name == self.tool.name:
            return self.tool
        return None


class _SlowTool:
    name = "slow_lookup"
    description = "慢查询"
    parameters = {}

    def __init__(self):
        self.calls = 0

    def invoke(self, args):
        self.calls += 1
        time.sleep(0.02)
        return "slow result"


class _SlowRegistry(_EmptyRegistry):
    def __init__(self):
        self.tool = _SlowTool()

    def list_all(self):
        return [self.tool]

    def get(self, name):
        if name == self.tool.name:
            return self.tool
        return None


class _SchemaTool:
    name = "schema_lookup"
    description = "schema validated lookup"
    parameters = {
        "case_id": {"type": "string", "required": True},
        "mode": {"type": "string", "enum": ["quick", "deep"]},
        "filters": {
            "type": "object",
            "required": ["level"],
            "properties": {
                "level": {"type": "string"},
            },
        },
    }

    def __init__(self):
        self.calls = []

    def invoke(self, args):
        self.calls.append(dict(args))
        return "validated"


class _SchemaRegistry(_EmptyRegistry):
    def __init__(self):
        self.tool = _SchemaTool()

    def list_all(self):
        return [self.tool]

    def get(self, name):
        if name == self.tool.name:
            return self.tool
        return None


class ToolRuntimeServiceTests(unittest.TestCase):
    def test_build_runtime_contract_summarizes_registered_tool_surface(self):
        service = ToolRuntimeService(
            tool_registry=_FakeRegistry(),
            mcp_registry_service=_FakeMcpRegistryService(),
        )

        contract = service.build_runtime_contract()

        self.assertEqual(contract["contract_version"], "phase-b-tool-runtime-v1")
        self.assertEqual(contract["execution_adapter"]["schema_validation"], "lightweight_schema_v1")
        self.assertEqual(contract["execution_adapter"]["schema_validation_keywords"], ["required", "type", "enum", "object.required"])
        self.assertEqual(contract["execution_adapter"]["timeout_enforcement"], "post_call_elapsed_check")
        self.assertEqual(contract["execution_adapter"]["retry_policy"], "sync_exception_retry")
        self.assertEqual(contract["execution_adapter"]["policy_coordination"], "permission_level_gate_v1")
        self.assertEqual(contract["execution_adapter"]["policy_decision_statuses"], ["allowed", "approval_required", "denied"])
        self.assertEqual(contract["total_tools"], 3)
        self.assertEqual(contract["base_tool_count"], 1)
        self.assertEqual(contract["langchain_tool_count"], 1)
        self.assertEqual(contract["tool_spec_count"], 2)
        self.assertEqual(contract["doubao_definition_count"], 1)
        self.assertEqual(contract["mcp_capability_count"], 2)
        self.assertEqual(contract["high_risk_tool_count"], 1)
        self.assertEqual(contract["tools"][0]["name"], "mcp_filesystem_write")
        self.assertEqual(contract["tools"][0]["risk_level"], "high")

    def test_build_adapter_health_degrades_cleanly_without_external_adapters(self):
        service = ToolRuntimeService(
            tool_registry=_FakeRegistry(),
            mcp_registry_service=_FakeMcpRegistryService(),
        )

        health = service.build_adapter_health_contract()

        self.assertEqual(health["contract_version"], "phase-b-adapter-health-v1")
        self.assertEqual(health["overall_status"], "not_configured")
        self.assertEqual(health["adapter_count"], 3)
        self.assertEqual(health["unavailable_count"], 0)
        self.assertEqual(health["not_configured_count"], 1)
        self.assertIn("tool_registry", {item["adapter_id"] for item in health["adapters"]})
        self.assertIn("external_frameworks", {item["adapter_id"] for item in health["adapters"]})

    def test_build_adapter_health_includes_framework_adapter_registry_entries(self):
        service = ToolRuntimeService(
            tool_registry=_FakeRegistry(),
            mcp_registry_service=_FakeMcpRegistryService(),
            framework_adapter_registry=_FakeFrameworkAdapterRegistry(),
        )

        health = service.build_adapter_health_contract()

        by_id = {item["adapter_id"]: item for item in health["adapters"]}
        self.assertEqual(health["adapter_count"], 3)
        self.assertEqual(health["overall_status"], "not_configured")
        self.assertIn("deepagents_draft", by_id)
        self.assertNotIn("external_frameworks", by_id)
        self.assertEqual(by_id["deepagents_draft"]["framework_name"], "DeepAgents-style")
        self.assertEqual(by_id["deepagents_draft"]["adapter_type"], "agent_framework")
        self.assertEqual(by_id["deepagents_draft"]["status"], "not_configured")
        self.assertEqual(by_id["deepagents_draft"]["supported_run_kinds"], ["chat", "background_task"])
        self.assertEqual(by_id["deepagents_draft"]["configuration_status"], "not_configured")

    def test_build_adapter_health_includes_phase_d_langgraph_draft_placeholder(self):
        service = ToolRuntimeService(
            tool_registry=_FakeRegistry(),
            mcp_registry_service=_FakeMcpRegistryService(),
            framework_adapter_registry=_FakePhaseDFrameworkAdapterRegistry(),
        )

        health = service.build_adapter_health_contract()

        by_id = {item["adapter_id"]: item for item in health["adapters"]}
        self.assertIn("langgraph_draft", by_id)
        self.assertEqual(health["overall_status"], "not_configured")
        self.assertEqual(by_id["langgraph_draft"]["framework_name"], "LangGraph")
        self.assertEqual(by_id["langgraph_draft"]["status"], "not_configured")
        self.assertEqual(by_id["langgraph_draft"]["supported_run_kinds"], ["chat", "workflow"])
        self.assertEqual(by_id["langgraph_draft"]["configuration_status"], "missing_package")
        self.assertEqual(by_id["langgraph_draft"]["missing_packages"], ["langgraph"])
        self.assertEqual(by_id["langgraph_draft"]["missing_env"], ["LANGGRAPH_RUNTIME_ENDPOINT", "LANGGRAPH_ASSISTANT_ID"])

    def test_registry_and_mcp_errors_surface_as_unavailable_health(self):
        service = ToolRuntimeService(
            tool_registry=_BrokenRegistry(),
            mcp_registry_service=_BrokenMcpRegistryService(),
        )

        contract = service.build_runtime_contract()
        health = service.build_adapter_health_contract()

        self.assertEqual(contract["tool_registry_status"], "unavailable")
        self.assertEqual(contract["mcp_registry_status"], "unavailable")
        self.assertIn("registry unreadable", contract["tool_registry_error"])
        self.assertIn("mcp registry corrupted", contract["mcp_registry_error"])
        self.assertEqual(health["overall_status"], "degraded")
        self.assertEqual(health["unavailable_count"], 2)
        by_id = {item["adapter_id"]: item for item in health["adapters"]}
        self.assertEqual(by_id["tool_registry"]["status"], "unavailable")
        self.assertEqual(by_id["mcp_runtime"]["status"], "unavailable")

    def test_base_tool_permission_level_contributes_to_high_risk_count(self):
        service = ToolRuntimeService(
            tool_registry=_AskOnlyRegistry(),
            mcp_registry_service=_FakeMcpRegistryService(),
        )

        contract = service.build_runtime_contract()

        self.assertEqual(contract["high_risk_tool_count"], 1)
        self.assertEqual(contract["tools"][0]["name"], "shell_command")
        self.assertEqual(contract["tools"][0]["risk_level"], "high")

    def test_execute_tool_returns_action_observation_envelope(self):
        registry = _ExecutableRegistry()
        service = ToolRuntimeService(
            tool_registry=registry,
            mcp_registry_service=_FakeMcpRegistryService(),
        )

        result = service.execute_tool("risk_lookup", {"case_id": "case-1"})

        self.assertEqual(result["contract_version"], "phase-ii-tool-runtime-execution-v1")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["tool_name"], "risk_lookup")
        self.assertEqual(result["result_text"], "命中风险: case-1")
        self.assertEqual(result["execution"]["executor"], "tool_runtime_service")
        self.assertEqual(result["execution"]["action"]["args"], {"case_id": "case-1"})
        self.assertEqual(result["execution"]["observation"]["status"], "ok")
        self.assertEqual(result["execution"]["tool_spec"]["permission_level"], "auto")
        self.assertEqual(result["execution"]["policy_decision"]["status"], "allowed")
        self.assertTrue(result["execution"]["policy_decision"]["allowed"])
        self.assertEqual(result["execution"]["schema_validation"]["status"], "passed")
        self.assertEqual(registry.tool.calls, [{"case_id": "case-1"}])

    def test_execute_tool_pauses_ask_permission_before_schema_validation_or_invocation(self):
        registry = _PermissionRegistry(permission_level="ask")
        service = ToolRuntimeService(
            tool_registry=registry,
            mcp_registry_service=_FakeMcpRegistryService(),
        )

        result = service.execute_tool("permission_probe", {})

        self.assertEqual(result["status"], "approval_required")
        self.assertEqual(result["execution"]["observation"]["status"], "approval_required")
        self.assertEqual(result["execution"]["policy_decision"]["status"], "approval_required")
        self.assertFalse(result["execution"]["policy_decision"]["allowed"])
        self.assertTrue(result["execution"]["policy_decision"]["requires_approval"])
        self.assertEqual(result["execution"]["policy_decision"]["permission_level"], "ask")
        self.assertEqual(result["execution"]["policy_decision"]["reason_code"], "permission_level_requires_approval")
        self.assertEqual(result["execution"]["schema_validation"]["status"], "skipped")
        self.assertEqual(registry.tool.calls, [])

    def test_evaluate_tool_policy_reports_ask_without_invoking_tool(self):
        registry = _PermissionRegistry(permission_level="ask")
        service = ToolRuntimeService(
            tool_registry=registry,
            mcp_registry_service=_FakeMcpRegistryService(),
        )

        decision = service.evaluate_tool_policy("permission_probe")

        self.assertEqual(decision["status"], "approval_required")
        self.assertEqual(decision["policy"], "permission_level_gate_v1")
        self.assertEqual(decision["permission_level"], "ask")
        self.assertEqual(decision["reason_code"], "permission_level_requires_approval")
        self.assertEqual(registry.tool.calls, [])

    def test_execute_tool_allows_ask_permission_with_approved_policy_override(self):
        registry = _PermissionRegistry(permission_level="ask")
        service = ToolRuntimeService(
            tool_registry=registry,
            mcp_registry_service=_FakeMcpRegistryService(),
        )

        result = service.execute_tool(
            "permission_probe",
            {"case_id": "case-1"},
            execution_options={
                "policy_override": {
                    "status": "approved",
                    "approval_request_id": "apr-1",
                    "source": "embedded_sdk_tool_continuation",
                }
            },
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["execution"]["policy_decision"]["status"], "allowed")
        self.assertEqual(result["execution"]["policy_decision"]["original_status"], "approval_required")
        self.assertEqual(result["execution"]["policy_decision"]["override"]["status"], "approved")
        self.assertEqual(result["execution"]["policy_decision"]["override"]["approval_request_id"], "apr-1")
        self.assertEqual(registry.tool.calls, [{"case_id": "case-1"}])

    def test_execute_tool_does_not_allow_deny_permission_with_approved_policy_override(self):
        registry = _PermissionRegistry(permission_level="deny")
        service = ToolRuntimeService(
            tool_registry=registry,
            mcp_registry_service=_FakeMcpRegistryService(),
        )

        result = service.execute_tool(
            "permission_probe",
            {"case_id": "case-1"},
            execution_options={"policy_override": {"status": "approved", "approval_request_id": "apr-1"}},
        )

        self.assertEqual(result["status"], "policy_denied")
        self.assertEqual(result["execution"]["policy_decision"]["status"], "denied")
        self.assertEqual(registry.tool.calls, [])

    def test_execute_tool_pauses_high_risk_permission_before_invocation(self):
        registry = _PermissionRegistry(permission_level="high_risk")
        service = ToolRuntimeService(
            tool_registry=registry,
            mcp_registry_service=_FakeMcpRegistryService(),
        )

        result = service.execute_tool("permission_probe", {"case_id": "case-1"})

        self.assertEqual(result["status"], "approval_required")
        self.assertEqual(result["execution"]["policy_decision"]["status"], "approval_required")
        self.assertEqual(result["execution"]["policy_decision"]["permission_level"], "high_risk")
        self.assertEqual(result["execution"]["policy_decision"]["reason_code"], "permission_level_requires_approval")
        self.assertEqual(registry.tool.calls, [])

    def test_execute_tool_denies_deny_permission_before_invocation(self):
        registry = _PermissionRegistry(permission_level="deny")
        service = ToolRuntimeService(
            tool_registry=registry,
            mcp_registry_service=_FakeMcpRegistryService(),
        )

        result = service.execute_tool("permission_probe", {"case_id": "case-1"})

        self.assertEqual(result["status"], "policy_denied")
        self.assertEqual(result["execution"]["observation"]["status"], "policy_denied")
        self.assertEqual(result["execution"]["policy_decision"]["status"], "denied")
        self.assertFalse(result["execution"]["policy_decision"]["allowed"])
        self.assertFalse(result["execution"]["policy_decision"]["requires_approval"])
        self.assertEqual(result["execution"]["policy_decision"]["permission_level"], "deny")
        self.assertEqual(result["execution"]["policy_decision"]["reason_code"], "permission_level_denied")
        self.assertEqual(result["execution"]["schema_validation"]["status"], "skipped")
        self.assertEqual(registry.tool.calls, [])

    def test_execute_tool_fails_closed_when_required_args_are_missing(self):
        registry = _ExecutableRegistry()
        service = ToolRuntimeService(
            tool_registry=registry,
            mcp_registry_service=_FakeMcpRegistryService(),
        )

        result = service.execute_tool("risk_lookup", {})

        self.assertEqual(result["status"], "validation_failed")
        self.assertEqual(result["execution"]["schema_validation"]["status"], "failed")
        self.assertEqual(result["execution"]["schema_validation"]["missing_required"], ["case_id"])
        self.assertEqual(registry.tool.calls, [])

    def test_execute_tool_retries_transient_errors_and_records_recovery(self):
        registry = _FlakyRegistry(fail_times=1)
        service = ToolRuntimeService(
            tool_registry=registry,
            mcp_registry_service=_FakeMcpRegistryService(),
        )

        result = service.execute_tool(
            "flaky_lookup",
            {"case_id": "case-1"},
            execution_options={"max_attempts": 2},
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["result_text"], "recovered:case-1")
        self.assertEqual(result["execution"]["retry"]["status"], "recovered")
        self.assertEqual(result["execution"]["retry"]["attempt_count"], 2)
        self.assertEqual(result["execution"]["retry"]["max_attempts"], 2)
        self.assertEqual(len(result["execution"]["retry"]["errors"]), 1)
        self.assertEqual(registry.tool.calls, 2)

    def test_execute_tool_reports_exhausted_retry_metadata(self):
        registry = _FlakyRegistry(fail_times=3)
        service = ToolRuntimeService(
            tool_registry=registry,
            mcp_registry_service=_FakeMcpRegistryService(),
        )

        result = service.execute_tool(
            "flaky_lookup",
            {"case_id": "case-1"},
            execution_options={"max_attempts": 2},
        )

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["execution"]["retry"]["status"], "exhausted")
        self.assertEqual(result["execution"]["retry"]["attempt_count"], 2)
        self.assertEqual(result["execution"]["observation"]["status"], "error")
        self.assertEqual(registry.tool.calls, 2)

    def test_execute_tool_reports_post_call_timeout_metadata(self):
        registry = _SlowRegistry()
        service = ToolRuntimeService(
            tool_registry=registry,
            mcp_registry_service=_FakeMcpRegistryService(),
        )

        result = service.execute_tool(
            "slow_lookup",
            {},
            execution_options={"timeout_seconds": 0.001},
        )

        self.assertEqual(result["status"], "timeout")
        self.assertEqual(result["execution"]["timeout"]["status"], "exceeded")
        self.assertEqual(result["execution"]["timeout"]["timeout_seconds"], 0.001)
        self.assertGreaterEqual(result["execution"]["timeout"]["elapsed_seconds"], 0.001)
        self.assertEqual(result["execution"]["retry"]["status"], "not_needed")
        self.assertEqual(registry.tool.calls, 1)

    def test_execute_tool_fails_closed_on_invalid_primitive_type(self):
        registry = _SchemaRegistry()
        service = ToolRuntimeService(
            tool_registry=registry,
            mcp_registry_service=_FakeMcpRegistryService(),
        )

        result = service.execute_tool(
            "schema_lookup",
            {"case_id": 123, "mode": "quick", "filters": {"level": "high"}},
        )

        self.assertEqual(result["status"], "validation_failed")
        self.assertEqual(result["execution"]["schema_validation"]["status"], "failed")
        self.assertEqual(
            result["execution"]["schema_validation"]["invalid_types"],
            [{"path": "case_id", "expected": "string", "actual": "integer"}],
        )
        self.assertEqual(registry.tool.calls, [])

    def test_execute_tool_fails_closed_on_invalid_enum_value(self):
        registry = _SchemaRegistry()
        service = ToolRuntimeService(
            tool_registry=registry,
            mcp_registry_service=_FakeMcpRegistryService(),
        )

        result = service.execute_tool(
            "schema_lookup",
            {"case_id": "case-1", "mode": "other", "filters": {"level": "high"}},
        )

        self.assertEqual(result["status"], "validation_failed")
        self.assertEqual(
            result["execution"]["schema_validation"]["invalid_enum"],
            [{"path": "mode", "allowed": ["quick", "deep"], "actual": "other"}],
        )
        self.assertEqual(registry.tool.calls, [])

    def test_execute_tool_fails_closed_on_nested_object_required_missing(self):
        registry = _SchemaRegistry()
        service = ToolRuntimeService(
            tool_registry=registry,
            mcp_registry_service=_FakeMcpRegistryService(),
        )

        result = service.execute_tool(
            "schema_lookup",
            {"case_id": "case-1", "mode": "quick", "filters": {}},
        )

        self.assertEqual(result["status"], "validation_failed")
        self.assertEqual(result["execution"]["schema_validation"]["missing_required"], ["filters.level"])
        self.assertEqual(registry.tool.calls, [])

    def test_execute_tool_allows_valid_lightweight_schema_payload(self):
        registry = _SchemaRegistry()
        service = ToolRuntimeService(
            tool_registry=registry,
            mcp_registry_service=_FakeMcpRegistryService(),
        )

        result = service.execute_tool(
            "schema_lookup",
            {"case_id": "case-1", "mode": "quick", "filters": {"level": "high"}},
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["execution"]["schema_validation"]["status"], "passed")
        self.assertEqual(registry.tool.calls, [{"case_id": "case-1", "mode": "quick", "filters": {"level": "high"}}])


if __name__ == "__main__":
    unittest.main()
