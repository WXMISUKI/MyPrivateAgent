"""Focused tests for the provider model-step adapter.

Covers the four acceptance scenarios defined in the
embedded-sdk-provider-model-step-adapter delta spec:

1. Provider resolves model and returns ExecutionModelStepResult.
2. Provider not available raises exception (routed through fallback).
3. Messages constructed from run context metadata.
4. Adapter is opt-in — not used by default.
"""

import unittest
from typing import Any, Dict
from unittest.mock import MagicMock

from backend.agent_framework.execution_loop import ExecutionModelStepResult
from backend.agent_framework.provider_model_step import (
    _build_messages,
    _normalize_response,
    build_provider_model_step,
)
from backend.agent_framework.providers import ModelProvider
from backend.agent_framework.runtime import AgentRunContext


class _StubModel:
    """Minimal model mock that mimics LangChain AIMessage."""

    def __init__(self, content: str = "stub response", model_name: str = "stub"):
        self.content = content
        self.model_name = model_name

    def invoke(self, messages: list) -> Any:
        return self


class _StubProvider(ModelProvider):
    """Minimal provider that returns a stub model."""

    def __init__(self, model: _StubModel | None = None):
        self._model = model or _StubModel()

    def get_model(self, model_name: str, purpose: str = "main") -> Any:
        return self._model

    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        return {}


class _FailingProvider(ModelProvider):
    """Provider that raises on get_model to simulate unavailable model."""

    def get_model(self, model_name: str, purpose: str = "main") -> Any:
        raise ValueError(f"不支持的模型: {model_name}")

    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        return {}


class BuildProviderModelStepTests(unittest.TestCase):
    """Scenario 1 & 2: factory function and provider resolution."""

    def test_factory_returns_callable(self):
        provider = _StubProvider()
        model_step = build_provider_model_step("test-model", provider=provider)
        self.assertTrue(callable(model_step))

    def test_resolves_model_and_returns_execution_model_step_result(self):
        stub_model = _StubModel(content="hello from model", model_name="test-model")
        provider = _StubProvider(model=stub_model)
        model_step = build_provider_model_step("test-model", provider=provider)

        run_context = AgentRunContext(
            conversation_id=42, user_id=7, model_name="test-model"
        )
        run_context.metadata["user_message"] = "What is 2+2?"

        result = model_step(run_context)

        self.assertIsInstance(result, ExecutionModelStepResult)
        self.assertEqual(result.text, "hello from model")
        self.assertEqual(result.model_name, "test-model")
        self.assertEqual(result.summary, "hello from model")

    def test_provider_unavailable_raises_exception(self):
        provider = _FailingProvider()
        model_step = build_provider_model_step("nonexistent", provider=provider)

        run_context = AgentRunContext(
            conversation_id=42, user_id=7, model_name="nonexistent"
        )
        run_context.metadata["user_message"] = "test"

        with self.assertRaises(ValueError):
            model_step(run_context)

    def test_run_context_model_name_takes_precedence(self):
        stub_model = _StubModel(content="response", model_name="actual")
        provider = _StubProvider(model=stub_model)
        model_step = build_provider_model_step("default", provider=provider)

        run_context = AgentRunContext(
            conversation_id=42, user_id=7, model_name="overridden"
        )
        run_context.metadata["user_message"] = "test"

        result = model_step(run_context)
        self.assertEqual(result.model_name, "overridden")


class BuildMessagesTests(unittest.TestCase):
    """Scenario 3: messages constructed from run context metadata."""

    def test_user_message_from_metadata(self):
        run_context = AgentRunContext(conversation_id=42, user_id=7)
        run_context.metadata["user_message"] = "Hello world"

        messages = _build_messages(run_context)

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[0]["content"], "Hello world")

    def test_system_prompt_included_when_present(self):
        run_context = AgentRunContext(conversation_id=42, user_id=7)
        run_context.metadata["system_prompt"] = "You are a helpful assistant."
        run_context.metadata["user_message"] = "Hello"

        messages = _build_messages(run_context)

        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[0]["content"], "You are a helpful assistant.")
        self.assertEqual(messages[1]["role"], "user")

    def test_falls_back_to_input_key(self):
        run_context = AgentRunContext(conversation_id=42, user_id=7)
        run_context.metadata["input"] = "fallback message"

        messages = _build_messages(run_context)

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["content"], "fallback message")

    def test_empty_when_no_metadata(self):
        run_context = AgentRunContext(conversation_id=42, user_id=7)

        messages = _build_messages(run_context)

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["content"], "")


class NormalizeResponseTests(unittest.TestCase):
    """Response normalization."""

    def test_normalizes_string_content(self):
        response = MagicMock()
        response.content = "model output"
        response.usage_metadata = None
        response.response_metadata = None

        result = _normalize_response(response, "test-model")

        self.assertEqual(result.text, "model output")
        self.assertEqual(result.model_name, "test-model")
        self.assertEqual(result.summary, "model output")

    def test_normalizes_usage_metadata(self):
        response = MagicMock()
        response.content = "output"
        response.usage_metadata = {
            "input_tokens": 10,
            "output_tokens": 5,
            "total_tokens": 15,
        }
        response.response_metadata = {"finish_reason": "stop"}

        result = _normalize_response(response, "test-model")

        self.assertEqual(result.usage["prompt_tokens"], 10)
        self.assertEqual(result.usage["completion_tokens"], 5)
        self.assertEqual(result.finish_reason, "stop")

    def test_falls_back_to_str_for_non_aimessage(self):
        result = _normalize_response("plain string", "test-model")

        self.assertEqual(result.text, "plain string")
        self.assertEqual(result.model_name, "test-model")


class FacadeModelNamePassthroughTests(unittest.TestCase):
    """Scenario 4: facade accepts model_name and auto-builds model_step."""

    def test_facade_execute_accepts_model_name(self):
        from backend.agent_framework.harness import AgentHarnessFacade

        facade = AgentHarnessFacade(name="test-agent", model_name="test-model")
        run = facade.sdk.create_run({"run_kind": "chat"})
        run_id = run["run"]["run_id"]

        # Mock the provider to avoid real LLM calls
        stub_model = _StubModel(content="facade response")
        stub_provider = _StubProvider(model=stub_model)

        with unittest.mock.patch(
            "backend.agent_framework.provider_model_step._get_default_provider",
            return_value=stub_provider,
        ):
            result = facade.execute(run_id, model_name="test-model")

        self.assertEqual(result["run"]["state"], "done")
        evidence = result["run"]["metadata"].get("execution_model_step")
        self.assertIsNotNone(evidence)
        self.assertEqual(evidence["text"], "facade response")

    def test_explicit_model_step_takes_precedence_over_model_name(self):
        from backend.agent_framework.harness import AgentHarnessFacade

        facade = AgentHarnessFacade(name="test-agent", model_name="test-model")
        run = facade.sdk.create_run({"run_kind": "chat"})
        run_id = run["run"]["run_id"]

        def explicit_step(_run):
            return ExecutionModelStepResult(text="explicit", summary="explicit")

        result = facade.execute(
            run_id, model_step=explicit_step, model_name="should-be-ignored"
        )

        self.assertEqual(result["run"]["state"], "done")
        evidence = result["run"]["metadata"]["execution_model_step"]
        self.assertEqual(evidence["text"], "explicit")

    def test_no_model_step_no_model_name_preserves_default(self):
        from backend.agent_framework.harness import AgentHarnessFacade

        facade = AgentHarnessFacade(name="test-agent", model_name="test-model")
        run = facade.sdk.create_run({"run_kind": "chat"})
        run_id = run["run"]["run_id"]

        result = facade.execute(run_id)

        self.assertEqual(result["run"]["state"], "done")
        self.assertNotIn("execution_model_step", result["run"]["metadata"])


if __name__ == "__main__":
    unittest.main()
