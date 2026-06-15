"""Deterministic tests for domain agent SDK execution integration.

These tests validate that domain agents can be executed through the SDK path
via the DomainAgentExecutionService, without requiring a real LLM or network.
"""

import unittest
from unittest.mock import patch

from backend.services.domain_agent_execution_service import (
    DomainAgentExecutionService,
    get_domain_agent_execution_service,
)


class DomainAgentExecutionServiceTests(unittest.TestCase):
    """Test the DomainAgentExecutionService."""

    def setUp(self):
        self.service = DomainAgentExecutionService()
        # Clear cache between tests
        self.service._facade_cache.clear()

    def test_load_manifest_for_weather_assistant(self):
        """Service can load the weather assistant manifest."""
        manifest = self.service._load_manifest("weather_assistant")
        self.assertIsNotNone(manifest)
        self.assertEqual(manifest["id"], "weather_assistant")
        self.assertIn("query_weather", manifest["capabilities"]["tools"])

    def test_load_manifest_returns_none_for_unknown_agent(self):
        """Service returns None for unknown agent."""
        manifest = self.service._load_manifest("nonexistent_agent")
        self.assertIsNone(manifest)

    def test_create_facade_for_weather_assistant(self):
        """Service creates a facade with registered tools."""
        facade = self.service._get_or_create_facade("weather_assistant")
        self.assertIsNotNone(facade)
        self.assertEqual(facade.name, "weather_assistant")

        contract = facade.build_contract()
        tool_names = contract["tool_registry_bridge"]["registered_tool_names"]
        self.assertIn("query_weather", tool_names)
        self.assertIn("query_forecast", tool_names)

    def test_facade_is_cached(self):
        """Facade is cached after first creation."""
        facade1 = self.service._get_or_create_facade("weather_assistant")
        facade2 = self.service._get_or_create_facade("weather_assistant")
        self.assertIs(facade1, facade2)

    def test_execute_returns_none_for_unknown_agent(self):
        """Execute returns error for unknown agent."""
        result = self.service.execute("nonexistent", input_text="test")
        self.assertFalse(result["ok"])
        self.assertIn("not found", result["error"])

    def test_execute_weather_assistant_with_mock_provider(self):
        """Execute weather assistant with mock provider."""
        # Mock the provider to avoid real LLM calls
        class MockModel:
            def invoke(self, messages):
                class R:
                    content = "北京今天天气晴朗，气温28°C。"
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
            result = self.service.execute(
                "weather_assistant",
                input_text="北京天气怎么样？",
                model_name="doubao",
                metadata={"system_prompt": "你是一个天气助手。"},
            )

        self.assertTrue(result["ok"])
        self.assertIn("output", result)
        self.assertIn("events", result)
        self.assertIn("run", result)
        self.assertEqual(result["run"]["state"], "done")

    def test_execute_captures_governance_trace(self):
        """Execute captures full governance trace."""
        class MockModel:
            def invoke(self, messages):
                class R:
                    content = "mock response"
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
            result = self.service.execute(
                "weather_assistant",
                input_text="test",
            )

        self.assertTrue(result["ok"])

        # Governance trace captured
        event_kinds = [e.get("status_kind") for e in result["events"]]
        self.assertIn("execution_loop_model_step_completed", event_kinds)
        self.assertIn("execution_loop_done", event_kinds)

        # State history covers full loop
        states = [h["state"] for h in result["run"].get("state_history", [])]
        self.assertIn("generating", states)
        self.assertIn("done", states)


class SingletonServiceTests(unittest.TestCase):
    """Test the singleton accessor."""

    def test_get_service_returns_singleton(self):
        s1 = get_domain_agent_execution_service()
        s2 = get_domain_agent_execution_service()
        self.assertIs(s1, s2)


if __name__ == "__main__":
    unittest.main()
