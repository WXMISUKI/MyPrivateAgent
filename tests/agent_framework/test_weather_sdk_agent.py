"""Deterministic tests for the weather SDK reference agent.

These tests validate that the reference domain agent pattern works
with mock providers, without requiring a real LLM or network access.
"""

import unittest
from typing import Any, Dict
from unittest.mock import patch

from backend.agent_framework.execution_loop import (
    ExecutionModelStepResult,
    ExecutionToolDecision,
)
from backend.agent_framework.harness import AgentHarnessFacade


class _StubModel:
    """Mock model that returns predictable output."""

    def __init__(self, content: str = "mock response"):
        self.content = content

    def invoke(self, messages: list) -> Any:
        return self


class _StubProvider:
    """Mock provider that returns a stub model."""

    def __init__(self, model=None):
        self._model = model or _StubModel()

    def get_model(self, model_name: str, purpose: str = "main") -> Any:
        return self._model

    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        return {}


class WeatherAgentPatternTests(unittest.TestCase):
    """Test the reference agent pattern: facade + tools + model step."""

    def _create_agent(self):
        """Create a weather agent with registered tools."""
        facade = AgentHarnessFacade(name="weather-agent", model_name="doubao")

        facade.register_tool(
            {"name": "query_weather", "description": "Query weather for a city"},
            handler=lambda args: '{"city": "Beijing", "temp": "28°C", "condition": "Sunny"}',
        )

        facade.register_tool(
            {"name": "query_forecast", "description": "Query weather forecast"},
            handler=lambda args: '{"city": "Beijing", "forecast": [{"date": "2026-06-15", "temp": "30°C"}]}',
        )

        return facade

    def test_agent_creation_and_tool_registration(self):
        """Agent can be created with tools registered."""
        facade = self._create_agent()
        contract = facade.build_contract()

        self.assertEqual(contract["agent_name"], "weather-agent")
        self.assertIn("query_weather", contract["tool_registry_bridge"]["registered_tool_names"])
        self.assertIn("query_forecast", contract["tool_registry_bridge"]["registered_tool_names"])

    def test_full_loop_with_mock_provider(self):
        """Agent completes full loop with mock provider and tool execution."""
        facade = self._create_agent()

        # Create a run with system prompt
        run = facade.run({
            "run_kind": "chat",
            "input": "北京天气怎么样？",
            "metadata": {
                "system_prompt": "你是一个天气助手，请用中文回答。",
            },
        })
        run_id = run["run"]["run_id"]

        # Execute with mock model step
        result = facade.execute(
            run_id,
            model_step=lambda _run: ExecutionModelStepResult(
                text="北京今天天气晴朗，气温28°C。",
                summary="Beijing weather response",
                model_name="doubao",
            ),
        )

        # Assertions
        self.assertEqual(result["run"]["state"], "done")

        # Governance trace captured
        event_kinds = [e.get("status_kind") for e in result["events"]]
        self.assertIn("execution_loop_model_step_completed", event_kinds)
        self.assertIn("execution_loop_done", event_kinds)

        # State history covers full loop
        states = [h["state"] for h in result["run"]["state_history"]]
        self.assertIn("generating", states)
        self.assertIn("done", states)

    def test_system_prompt_passed_through_metadata(self):
        """System prompt from metadata is available in run context."""
        facade = self._create_agent()

        run = facade.run({
            "run_kind": "chat",
            "input": "test",
            "metadata": {
                "system_prompt": "你是一个天气助手。",
            },
        })

        self.assertEqual(run["run"]["metadata"]["system_prompt"], "你是一个天气助手。")

    def test_multiple_tools_registered(self):
        """Multiple tools can be registered and are all listed."""
        facade = self._create_agent()
        contract = facade.build_contract()

        tool_names = contract["tool_registry_bridge"]["registered_tool_names"]
        self.assertEqual(len(tool_names), 2)
        self.assertIn("query_weather", tool_names)
        self.assertIn("query_forecast", tool_names)


class WeatherAgentWithModelNameTests(unittest.TestCase):
    """Test the agent with model_name auto-build."""

    def test_model_name_auto_builds_model_step(self):
        """Facade accepts model_name and auto-builds model_step."""
        facade = AgentHarnessFacade(name="weather-agent", model_name="doubao")
        facade.register_tool(
            {"name": "query_weather", "description": "Query weather"},
            handler=lambda args: '{"temp": "25°C"}',
        )

        run = facade.run({"run_kind": "chat", "input": "天气"})
        run_id = run["run"]["run_id"]

        # Mock the provider
        class MockModel:
            def invoke(self, messages):
                class R:
                    content = "今天天气不错！"
                    usage_metadata = None
                    response_metadata = None
                return R()

        class MockProvider:
            def get_model(self, model_name, purpose="main"):
                return MockModel()
            def get_model_config(self, model_name):
                return {}

        with patch(
            "backend.agent_framework.provider_model_step._get_default_provider",
            return_value=MockProvider(),
        ):
            result = facade.execute(run_id, model_name="doubao")

        self.assertEqual(result["run"]["state"], "done")
        evidence = result["run"]["metadata"]["execution_model_step"]
        self.assertEqual(evidence["text"], "今天天气不错！")


if __name__ == "__main__":
    unittest.main()
