import unittest

from backend.agent_framework.events import AgentEventFactory
from backend.agent_framework.execution_loop import (
    ExecutionFallbackResult,
    ExecutionLoopController,
    ExecutionReflectionResult,
    ExecutionReviewResult,
    ExecutionToolDecision,
    ExecutionToolResult,
)
from backend.agent_framework.runtime import AgentRunContext


class ExecutionLoopControllerTests(unittest.TestCase):
    def test_minimal_loop_drives_run_to_done_with_observable_events(self):
        run_context = AgentRunContext(conversation_id=42, user_id=7, model_name="doubao")
        events = []

        result = ExecutionLoopController().run_until_stop(
            run_context,
            event_factory=AgentEventFactory(run_context.run_id, conversation_id=42),
            append_event=lambda event: events.append(event),
        )

        self.assertEqual(result["run"]["state"], "done")
        self.assertEqual(result["run"]["iteration"], 1)
        self.assertEqual(result["run"]["stop_reason"], "loop_completed")
        self.assertEqual(
            [item["state"] for item in result["run"]["state_history"]],
            ["planning", "generating", "observing", "finalizing", "done"],
        )
        self.assertTrue(any(event["status_kind"] == "execution_loop_step" for event in events))
        self.assertEqual(events[-1]["type"], "done")
        self.assertEqual(events[-1]["status_kind"], "execution_loop_done")

    def test_review_hook_records_approved_review_before_done(self):
        run_context = AgentRunContext(conversation_id=42, user_id=7, model_name="doubao")
        events = []

        result = ExecutionLoopController(
            reviewer=lambda run: ExecutionReviewResult(
                reviewer="quality_gate",
                status="approved",
                summary=f"run {run.run_id} passed minimal review",
                findings=("structure_ok",),
            )
        ).run_until_stop(
            run_context,
            event_factory=AgentEventFactory(run_context.run_id, conversation_id=42),
            append_event=lambda event: events.append(event),
        )

        self.assertEqual(result["run"]["state"], "done")
        self.assertEqual(result["run"]["metadata"]["execution_review"]["status"], "approved")
        review_event = next(event for event in events if event["status_kind"] == "execution_loop_reviewed")
        self.assertEqual(review_event["review"]["reviewer"], "quality_gate")
        self.assertEqual(review_event["review"]["findings"], ["structure_ok"])
        self.assertEqual(events[-1]["status_kind"], "execution_loop_done")

    def test_rejected_review_fails_run_and_stops_before_done(self):
        run_context = AgentRunContext(conversation_id=42, user_id=7, model_name="doubao")
        events = []

        result = ExecutionLoopController(
            reviewer=lambda _run: {
                "reviewer": "quality_gate",
                "status": "rejected",
                "summary": "missing required evidence",
                "findings": ["缺少证据链"],
            }
        ).run_until_stop(
            run_context,
            event_factory=AgentEventFactory(run_context.run_id, conversation_id=42),
            append_event=lambda event: events.append(event),
        )

        self.assertEqual(result["run"]["state"], "failed")
        self.assertEqual(result["run"]["stop_reason"], "review_rejected")
        self.assertEqual(result["run"]["metadata"]["execution_review"]["status"], "rejected")
        self.assertTrue(any(event["status_kind"] == "execution_loop_review_rejected" for event in events))
        self.assertFalse(any(event["status_kind"] == "execution_loop_done" for event in events))

    def test_reviewer_exception_without_fallback_fails_run(self):
        run_context = AgentRunContext(conversation_id=42, user_id=7, model_name="doubao")
        events = []

        def broken_reviewer(_run):
            raise RuntimeError("review service unavailable")

        result = ExecutionLoopController(reviewer=broken_reviewer).run_until_stop(
            run_context,
            event_factory=AgentEventFactory(run_context.run_id, conversation_id=42),
            append_event=lambda event: events.append(event),
        )

        self.assertEqual(result["run"]["state"], "failed")
        self.assertEqual(result["run"]["stop_reason"], "loop_exception")
        self.assertEqual(result["run"]["metadata"]["execution_fallback"]["status"], "failed")
        self.assertTrue(any(event["status_kind"] == "execution_loop_failed" for event in events))
        self.assertFalse(any(event["status_kind"] == "execution_loop_done" for event in events))

    def test_fallback_handler_can_degrade_reviewer_exception_and_continue(self):
        run_context = AgentRunContext(conversation_id=42, user_id=7, model_name="doubao")
        events = []

        def broken_reviewer(_run):
            raise RuntimeError("review service unavailable")

        def fallback_handler(error, run):
            return ExecutionFallbackResult(
                strategy="skip_reviewer",
                status="handled",
                summary=f"{run.run_id} skipped reviewer: {error}",
                metadata={"reason": "reviewer_unavailable"},
            )

        result = ExecutionLoopController(
            reviewer=broken_reviewer,
            fallback_handler=fallback_handler,
        ).run_until_stop(
            run_context,
            event_factory=AgentEventFactory(run_context.run_id, conversation_id=42),
            append_event=lambda event: events.append(event),
        )

        self.assertEqual(result["run"]["state"], "done")
        self.assertEqual(result["run"]["metadata"]["execution_fallback"]["status"], "handled")
        self.assertEqual(result["run"]["metadata"]["execution_fallback"]["strategy"], "skip_reviewer")
        fallback_event = next(event for event in events if event["status_kind"] == "execution_loop_fallback_applied")
        self.assertEqual(fallback_event["fallback"]["metadata"]["reason"], "reviewer_unavailable")
        self.assertEqual(events[-1]["status_kind"], "execution_loop_done")

    def test_reflector_records_accepted_reflection_after_observing(self):
        run_context = AgentRunContext(conversation_id=42, user_id=7, model_name="doubao")
        events = []

        result = ExecutionLoopController(
            reflector=lambda run: ExecutionReflectionResult(
                reflector="self_check",
                status="accepted",
                summary=f"iteration {run.iteration} accepted",
                observations=("answer_is_complete",),
            )
        ).run_until_stop(
            run_context,
            event_factory=AgentEventFactory(run_context.run_id, conversation_id=42),
            append_event=lambda event: events.append(event),
        )

        self.assertEqual(result["run"]["state"], "done")
        self.assertEqual(result["run"]["metadata"]["execution_reflections"][0]["status"], "accepted")
        reflection_event = next(event for event in events if event["status_kind"] == "execution_loop_reflected")
        self.assertEqual(reflection_event["reflection"]["reflector"], "self_check")
        self.assertEqual(reflection_event["reflection"]["observations"], ["answer_is_complete"])

    def test_reflector_can_request_revision_iteration_before_finalizing(self):
        run_context = AgentRunContext(conversation_id=42, user_id=7, model_name="doubao")
        events = []

        def reflector(run):
            if run.iteration == 1:
                return {
                    "reflector": "self_check",
                    "status": "revise",
                    "summary": "need one more pass",
                    "observations": ["缺少结论"],
                }
            return {
                "reflector": "self_check",
                "status": "accepted",
                "summary": "second pass accepted",
            }

        result = ExecutionLoopController(
            reflector=reflector,
            max_iterations=2,
        ).run_until_stop(
            run_context,
            event_factory=AgentEventFactory(run_context.run_id, conversation_id=42),
            append_event=lambda event: events.append(event),
        )

        self.assertEqual(result["run"]["state"], "done")
        self.assertEqual(result["run"]["iteration"], 2)
        self.assertEqual(len(result["run"]["metadata"]["execution_reflections"]), 2)
        self.assertEqual(result["run"]["metadata"]["execution_reflections"][0]["status"], "revise")
        self.assertEqual(result["run"]["metadata"]["execution_reflections"][1]["status"], "accepted")
        self.assertEqual(
            [event["loop_step"] for event in events if event.get("status_kind") == "execution_loop_revision_requested"],
            ["observing"],
        )

    def test_tool_executor_records_tool_call_events_and_history(self):
        run_context = AgentRunContext(conversation_id=42, user_id=7, model_name="doubao")
        events = []

        result = ExecutionLoopController(
            tool_executor=lambda run: ExecutionToolResult(
                tool_name="risk_lookup",
                args={"case_id": "case-1"},
                result="命中黑名单手机号",
                tool_call_id=f"tool-{run.iteration}",
                execution={"status": "success"},
            )
        ).run_until_stop(
            run_context,
            event_factory=AgentEventFactory(run_context.run_id, conversation_id=42),
            append_event=lambda event: events.append(event),
        )

        self.assertEqual(result["run"]["state"], "done")
        self.assertEqual(result["run"]["tool_history"][0]["tool_name"], "risk_lookup")
        self.assertEqual(result["run"]["tool_history"][0]["result"], "命中黑名单手机号")
        self.assertTrue(any(event["type"] == "tool_call_start" for event in events))
        tool_result_event = next(event for event in events if event["type"] == "tool_result")
        self.assertEqual(tool_result_event["tool_name"], "risk_lookup")
        self.assertEqual(tool_result_event["result"], "命中黑名单手机号")
        self.assertIn("tool_calling", [item["state"] for item in result["run"]["state_history"]])

    def test_tool_policy_can_pause_run_for_approval_before_tool_execution(self):
        run_context = AgentRunContext(conversation_id=42, user_id=7, model_name="doubao")
        events = []

        result = ExecutionLoopController(
            tool_policy=lambda run: ExecutionToolDecision(
                status="approval_required",
                tool_name="risk_lookup",
                reason="高风险工具需要审批",
                metadata={"permission_level": "ask", "run_id": run.run_id},
            ),
            tool_executor=lambda _run: ExecutionToolResult(
                tool_name="risk_lookup",
                args={"case_id": "case-1"},
                result="不应该执行",
            ),
        ).run_until_stop(
            run_context,
            event_factory=AgentEventFactory(run_context.run_id, conversation_id=42),
            append_event=lambda event: events.append(event),
        )

        self.assertEqual(result["run"]["state"], "waiting_approval")
        self.assertEqual(result["run"]["stop_reason"], "tool_approval_required")
        self.assertEqual(result["run"]["metadata"]["execution_tool_decision"]["status"], "approval_required")
        self.assertEqual(result["run"]["tool_history"], [])
        permission_event = next(event for event in events if event["type"] == "tool_permission_required")
        self.assertEqual(permission_event["tool_name"], "risk_lookup")
        self.assertFalse(any(event["type"] == "tool_result" for event in events))
        self.assertFalse(any(event["status_kind"] == "execution_loop_done" for event in events))

    def test_tool_policy_denied_fails_closed_before_tool_execution(self):
        run_context = AgentRunContext(conversation_id=42, user_id=7, model_name="doubao")
        events = []

        result = ExecutionLoopController(
            tool_policy=lambda _run: ExecutionToolDecision(
                status="denied",
                tool_name="filesystem_write",
                tool_args={"path": "case.md"},
                reason="子智能体工具白名单不允许调用",
                metadata={"reason_code": "subagent_tool_allowlist_block"},
            ),
            tool_executor=lambda _run: ExecutionToolResult(
                tool_name="filesystem_write",
                args={"path": "case.md"},
                result="不应该执行",
            ),
        ).run_until_stop(
            run_context,
            event_factory=AgentEventFactory(run_context.run_id, conversation_id=42),
            append_event=lambda event: events.append(event),
        )

        self.assertEqual(result["run"]["state"], "failed")
        self.assertEqual(result["run"]["stop_reason"], "tool_policy_denied")
        self.assertEqual(result["run"]["metadata"]["execution_tool_decision"]["status"], "denied")
        self.assertEqual(result["run"]["tool_history"], [])
        denied_event = next(event for event in events if event["status_kind"] == "tool_permission_denied")
        self.assertEqual(denied_event["tool_decision"]["tool_args"], {"path": "case.md"})
        self.assertFalse(any(event["type"] == "tool_result" for event in events))
        self.assertFalse(any(event["status_kind"] == "execution_loop_done" for event in events))


if __name__ == "__main__":
    unittest.main()
