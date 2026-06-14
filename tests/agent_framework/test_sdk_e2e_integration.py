"""Deterministic end-to-end integration tests for the Embedded SDK path.

These tests exercise the full SDK loop:
  AgentHarnessFacade.execute()
    → model_step (mock)
    → tool_policy + tool_executor (mock)
    → reviewer (mock)
    → governance trace captured

No real LLM calls are made. All providers and tools are mocked.
"""

import unittest
from typing import Any, Dict

from backend.agent_framework.events import AgentEventFactory
from backend.agent_framework.execution_loop import (
    ExecutionLoopController,
    ExecutionModelStepResult,
    ExecutionReviewResult,
    ExecutionToolDecision,
    ExecutionToolResult,
)
from backend.agent_framework.harness import AgentHarnessFacade
from backend.agent_framework.runtime import AgentRunContext


class SDKFullLoopTests(unittest.TestCase):
    """Test the full SDK loop with model step, tool execution, and reviewer."""

    def test_full_loop_model_step_only_completes_to_done(self):
        """Simplest case: model generates text, no tools, reviewer approves."""
        facade = AgentHarnessFacade(name="test-agent", model_name="test-model")
        run = facade.run({"run_kind": "chat", "input": "hello"})
        run_id = run["run"]["run_id"]

        result = facade.execute(
            run_id,
            model_step=lambda _run: ExecutionModelStepResult(
                text="Hello! How can I help?",
                summary="greeting response",
                model_name="test-model",
            ),
        )

        self.assertEqual(result["run"]["state"], "done")
        self.assertEqual(result["run"]["stop_reason"], "loop_completed")
        # Model step evidence captured
        evidence = result["run"]["metadata"]["execution_model_step"]
        self.assertEqual(evidence["text"], "Hello! How can I help?")
        self.assertEqual(evidence["model_name"], "test-model")
        # Events include model step completion
        event_kinds = [e.get("status_kind") for e in result["events"]]
        self.assertIn("execution_loop_model_step_completed", event_kinds)
        self.assertIn("execution_loop_done", event_kinds)

    def test_full_loop_with_tool_execution(self):
        """Model generates text, tool is executed, reviewer approves."""
        facade = AgentHarnessFacade(name="test-agent", model_name="test-model")

        # Register a simple tool
        facade.register_tool(
            {"name": "get_time", "description": "Get current time"},
            handler=lambda args: "2026-06-14 12:00:00",
        )

        run = facade.run({"run_kind": "chat", "input": "what time is it?"})
        run_id = run["run"]["run_id"]

        tool_called = {"count": 0}

        def tool_policy(_run):
            tool_called["count"] += 1
            return ExecutionToolDecision(
                status="allowed",
                tool_name="get_time",
                tool_args={},
                reason="user asked for time",
            )

        result = facade.execute(
            run_id,
            model_step=lambda _run: ExecutionModelStepResult(
                text="Let me check the time for you.",
                summary="checking time",
                model_name="test-model",
            ),
            tool_policy=tool_policy,
        )

        self.assertEqual(result["run"]["state"], "done")
        # Tool was called
        self.assertGreater(tool_called["count"], 0)
        # Tool result in events
        event_kinds = [e.get("status_kind") for e in result["events"]]
        self.assertIn("tool_result", event_kinds)

    def test_full_loop_with_reviewer_consumption(self):
        """Reviewer reads model step evidence and approves."""
        seen_evidence = {}

        facade = AgentHarnessFacade(name="test-agent", model_name="test-model")
        run = facade.run({"run_kind": "chat", "input": "test"})
        run_id = run["run"]["run_id"]

        def reviewer(run_ctx):
            seen_evidence.update(run_ctx.metadata.get("execution_model_step", {}))
            return ExecutionReviewResult(
                reviewer="e2e_reviewer",
                status="approved",
                summary="model output looks good",
            )

        result = facade.execute(
            run_id,
            model_step=lambda _run: ExecutionModelStepResult(
                text="verified response",
                summary="for review",
                model_name="test-model",
            ),
            reviewer=reviewer,
        )

        self.assertEqual(result["run"]["state"], "done")
        self.assertEqual(seen_evidence.get("text"), "verified response")
        # Review event captured
        event_kinds = [e.get("status_kind") for e in result["events"]]
        self.assertIn("execution_loop_reviewed", event_kinds)

    def test_full_loop_model_name_auto_builds_model_step(self):
        """Facade accepts model_name and auto-builds model_step via provider."""
        facade = AgentHarnessFacade(name="test-agent", model_name="test-model")
        run = facade.run({"run_kind": "chat", "input": "hello"})
        run_id = run["run"]["run_id"]

        # Mock the provider to return a predictable model
        class MockModel:
            def invoke(self, messages):
                class Response:
                    content = "mock model response"
                    usage_metadata = None
                    response_metadata = None
                return Response()

        class MockProvider:
            def get_model(self, model_name, purpose="main"):
                return MockModel()
            def get_model_config(self, model_name):
                return {}

        import unittest.mock
        with unittest.mock.patch(
            "backend.agent_framework.provider_model_step._get_default_provider",
            return_value=MockProvider(),
        ):
            result = facade.execute(run_id, model_name="test-model")

        self.assertEqual(result["run"]["state"], "done")
        evidence = result["run"]["metadata"]["execution_model_step"]
        self.assertEqual(evidence["text"], "mock model response")

    def test_full_loop_governance_trace_captures_all_states(self):
        """Governance trace captures state transitions through the full loop."""
        facade = AgentHarnessFacade(name="test-agent", model_name="test-model")
        run = facade.run({"run_kind": "chat", "input": "test"})
        run_id = run["run"]["run_id"]

        result = facade.execute(
            run_id,
            model_step=lambda _run: "simple response",
        )

        # State history covers the full loop
        states = [h["state"] for h in result["run"]["state_history"]]
        self.assertIn("planning", states)
        self.assertIn("generating", states)
        self.assertIn("observing", states)
        self.assertIn("finalizing", states)
        self.assertIn("done", states)

        # Execution loop metadata present
        loop_meta = result["run"]["metadata"]["execution_loop"]
        self.assertTrue(loop_meta["completed"])
        self.assertIn("generating", loop_meta["steps"])


class SDKLoopWithFallbackTests(unittest.TestCase):
    """Test fallback handling in the SDK loop."""

    def test_model_step_failure_handled_by_fallback(self):
        """Model step exception is caught by fallback handler."""
        facade = AgentHarnessFacade(name="test-agent", model_name="test-model")
        run = facade.run({"run_kind": "chat", "input": "test"})
        run_id = run["run"]["run_id"]

        from backend.agent_framework.execution_loop import ExecutionFallbackResult

        def failing_model_step(_run):
            raise RuntimeError("model unavailable")

        def fallback(exc, _run):
            return ExecutionFallbackResult(
                strategy="degrade",
                status="handled",
                summary="degraded to fallback response",
            )

        result = facade.execute(
            run_id,
            model_step=failing_model_step,
            fallback_handler=fallback,
        )

        self.assertEqual(result["run"]["state"], "done")
        event_kinds = [e.get("status_kind") for e in result["events"]]
        self.assertIn("execution_loop_fallback_applied", event_kinds)


if __name__ == "__main__":
    unittest.main()
