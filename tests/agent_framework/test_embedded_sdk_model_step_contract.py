"""Focused tests for the Embedded SDK model-step contract.

Covers the five acceptance scenarios defined in the
embedded-sdk-model-step-contract delta spec:

1. Model step completes successfully (compact evidence + event).
2. No model step preserves existing behavior (no metadata / event).
3. Fallback handles model step failure (fallback_applied event, run continues).
4. Unhandled model step failure fails closed (loop_failed event, run → failed).
5. Unsafe model output fields are excluded by sanitization.

An additional SDK-level test verifies that execute_run passes model_step
through to the execution loop controller.
"""

import unittest

from backend.agent_framework.events import AgentEventFactory
from backend.agent_framework.execution_loop import (
    ExecutionFallbackResult,
    ExecutionLoopController,
    ExecutionModelStepResult,
    ExecutionReviewResult,
    _sanitize_model_step_payload,
)
from backend.agent_framework.runtime import AgentRunContext
from backend.agent_framework.sdk import EmbeddedAgentRuntimeSDK


class ModelStepContractTests(unittest.TestCase):
    """Scenario 1–4: ExecutionLoopController-level model_step behaviour."""

    def _run(self, *, model_step=None, reviewer=None, fallback_handler=None):
        """Helper: run the loop and return (result, events)."""
        run_context = AgentRunContext(conversation_id=42, user_id=7, model_name="doubao")
        events: list = []
        result = ExecutionLoopController(
            model_step=model_step,
            reviewer=reviewer,
            fallback_handler=fallback_handler,
        ).run_until_stop(
            run_context,
            event_factory=AgentEventFactory(run_context.run_id, conversation_id=42),
            append_event=lambda event: events.append(event),
        )
        return result, events

    # ------------------------------------------------------------------
    # Scenario 1: model step completes successfully
    # ------------------------------------------------------------------
    def test_model_step_success_emits_compact_evidence_and_event(self):
        def my_model_step(_run):
            return ExecutionModelStepResult(
                text="hello from model",
                summary="greeting",
                model_name="test-model",
                finish_reason="stop",
                usage={"prompt_tokens": 10, "completion_tokens": 5},
                metadata={"temperature": 0.7},
            )

        result, events = self._run(model_step=my_model_step)

        self.assertEqual(result["run"]["state"], "done")
        # Metadata stored
        evidence = result["run"]["metadata"]["execution_model_step"]
        self.assertEqual(evidence["text"], "hello from model")
        self.assertEqual(evidence["summary"], "greeting")
        self.assertEqual(evidence["model_name"], "test-model")
        self.assertEqual(evidence["finish_reason"], "stop")
        self.assertEqual(evidence["usage"]["prompt_tokens"], 10)
        # Event emitted
        model_event = next(
            e for e in events if e["status_kind"] == "execution_loop_model_step_completed"
        )
        self.assertEqual(model_event["model_step"]["text"], "hello from model")
        self.assertEqual(model_event["loop_step"], "generating")

    def test_model_step_accepts_plain_string(self):
        result, events = self._run(model_step=lambda _run: "plain text response")

        self.assertEqual(result["run"]["state"], "done")
        evidence = result["run"]["metadata"]["execution_model_step"]
        self.assertEqual(evidence["text"], "plain text response")
        model_event = next(
            e for e in events if e["status_kind"] == "execution_loop_model_step_completed"
        )
        self.assertIn("plain text response", model_event["model_step"]["summary"])

    def test_model_step_accepts_dict(self):
        result, events = self._run(
            model_step=lambda _run: {
                "text": "dict response",
                "summary": "from dict",
                "model_name": "dict-model",
            }
        )

        self.assertEqual(result["run"]["state"], "done")
        evidence = result["run"]["metadata"]["execution_model_step"]
        self.assertEqual(evidence["text"], "dict response")
        self.assertEqual(evidence["model_name"], "dict-model")

    # ------------------------------------------------------------------
    # Scenario 2: no model step preserves existing behavior
    # ------------------------------------------------------------------
    def test_no_model_step_preserves_default_behavior(self):
        result, events = self._run(model_step=None)

        self.assertEqual(result["run"]["state"], "done")
        self.assertNotIn("execution_model_step", result["run"]["metadata"])
        model_events = [
            e for e in events if e["status_kind"] == "execution_loop_model_step_completed"
        ]
        self.assertEqual(len(model_events), 0)

    # ------------------------------------------------------------------
    # Scenario 3: fallback handles model step failure
    # ------------------------------------------------------------------
    def test_model_step_failure_handled_by_fallback(self):
        def failing_model_step(_run):
            raise RuntimeError("model overloaded")

        def handler(_exc, _run):
            return ExecutionFallbackResult(
                strategy="retry",
                status="handled",
                summary="retried after transient failure",
            )

        result, events = self._run(
            model_step=failing_model_step,
            fallback_handler=handler,
        )

        self.assertEqual(result["run"]["state"], "done")
        fallback_event = next(
            e for e in events if e["status_kind"] == "execution_loop_fallback_applied"
        )
        self.assertIn("model overloaded", fallback_event["error"])
        self.assertEqual(fallback_event["fallback"]["strategy"], "retry")

    # ------------------------------------------------------------------
    # Scenario 4: unhandled model step failure fails closed
    # ------------------------------------------------------------------
    def test_model_step_unhandled_failure_fails_closed(self):
        def failing_model_step(_run):
            raise ValueError("catastrophic model error")

        def handler(_exc, _run):
            return ExecutionFallbackResult(
                strategy="abort",
                status="not_handled",
                summary="cannot recover",
            )

        result, events = self._run(
            model_step=failing_model_step,
            fallback_handler=handler,
        )

        self.assertEqual(result["run"]["state"], "failed")
        self.assertEqual(result["run"]["stop_reason"], "loop_exception")
        failed_event = next(
            e for e in events if e.get("status_kind") == "execution_loop_failed"
        )
        self.assertIn("catastrophic model error", failed_event["error"])

    def test_model_step_unhandled_failure_no_fallback_also_fails_closed(self):
        """When no fallback_handler is set, exception still fails closed."""
        def failing_model_step(_run):
            raise RuntimeError("no fallback registered")

        result, events = self._run(model_step=failing_model_step)

        self.assertEqual(result["run"]["state"], "failed")
        self.assertEqual(result["run"]["stop_reason"], "loop_exception")

    # ------------------------------------------------------------------
    # Scenario 5: model step with reviewer consumption
    # ------------------------------------------------------------------
    def test_reviewer_consumes_model_step_evidence(self):
        """Reviewer can read model_step evidence from run metadata."""
        seen_evidence = {}

        def my_model_step(_run):
            return ExecutionModelStepResult(
                text="reviewable output",
                summary="for review",
                model_name="test-model",
            )

        def my_reviewer(run):
            seen_evidence.update(run.metadata.get("execution_model_step", {}))
            return ExecutionReviewResult(
                reviewer="test_reviewer",
                status="approved",
                summary="model output reviewed",
            )

        result, events = self._run(model_step=my_model_step, reviewer=my_reviewer)

        self.assertEqual(result["run"]["state"], "done")
        self.assertEqual(seen_evidence.get("text"), "reviewable output")


class ModelStepSanitizationTests(unittest.TestCase):
    """Scenario 5: unsafe fields are excluded from model step evidence."""

    def test_callable_values_excluded_from_metadata(self):
        payload = {
            "text": "safe text",
            "my_callable": lambda: "should be excluded",
            "nested": {
                "safe_key": 42,
                "another_callable": lambda x: x,
            },
        }
        sanitized = _sanitize_model_step_payload(payload)

        self.assertEqual(sanitized["text"], "safe text")
        self.assertNotIn("my_callable", sanitized)
        self.assertIn("safe_key", sanitized["nested"])
        self.assertNotIn("another_callable", sanitized["nested"])

    def test_unsafe_runtime_objects_excluded(self):
        class _FakeProviderClient:
            def __init__(self):
                self.api_key = "secret"

        class _FakeStream:
            def __iter__(self):
                yield "chunk"

        payload = {
            "text": "response",
            "provider_client": _FakeProviderClient(),
            "stream": _FakeStream(),
            "safe_int": 42,
        }
        sanitized = _sanitize_model_step_payload(payload)

        self.assertEqual(sanitized["text"], "response")
        self.assertEqual(sanitized["safe_int"], 42)
        self.assertNotIn("provider_client", sanitized)
        self.assertNotIn("stream", sanitized)

    def test_primitive_types_preserved(self):
        payload = {
            "str_val": "hello",
            "int_val": 42,
            "float_val": 3.14,
            "bool_val": True,
            "none_val": None,
            "list_val": [1, 2, 3],
        }
        sanitized = _sanitize_model_step_payload(payload)

        self.assertEqual(sanitized["str_val"], "hello")
        self.assertEqual(sanitized["int_val"], 42)
        self.assertEqual(sanitized["float_val"], 3.14)
        self.assertTrue(sanitized["bool_val"])
        self.assertIsNone(sanitized["none_val"])
        self.assertEqual(sanitized["list_val"], [1, 2, 3])

    def test_tuple_converted_to_list(self):
        sanitized = _sanitize_model_step_payload({"items": (1, 2, 3)})
        self.assertEqual(sanitized["items"], [1, 2, 3])


class ModelStepSDKPassthroughTests(unittest.TestCase):
    """Verify that EmbeddedAgentRuntimeSDK.execute_run passes model_step through."""

    def test_execute_run_passes_model_step_to_loop(self):
        sdk = EmbeddedAgentRuntimeSDK()
        run = sdk.create_run({"run_kind": "chat"})
        run_id = run["run"]["run_id"]

        result = sdk.execute_run(
            run_id,
            model_step=lambda _run: ExecutionModelStepResult(
                text="sdk-level model output",
                summary="sdk test",
                model_name="sdk-model",
            ),
        )

        self.assertEqual(result["run"]["state"], "done")
        evidence = result["run"]["metadata"]["execution_model_step"]
        self.assertEqual(evidence["text"], "sdk-level model output")
        self.assertEqual(evidence["model_name"], "sdk-model")

    def test_execute_run_no_model_step_preserves_default(self):
        sdk = EmbeddedAgentRuntimeSDK()
        run = sdk.create_run({"run_kind": "chat"})
        run_id = run["run"]["run_id"]

        result = sdk.execute_run(run_id)

        self.assertEqual(result["run"]["state"], "done")
        self.assertNotIn("execution_model_step", result["run"]["metadata"])


if __name__ == "__main__":
    unittest.main()
