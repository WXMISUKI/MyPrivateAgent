import unittest

from backend.services.query_control_event_mapper_service import QueryControlEventMapperService


class QueryControlEventMapperServiceTests(unittest.TestCase):
    def test_map_main_chat_events_to_query_lifecycle_stages(self):
        mapper = QueryControlEventMapperService()

        cases = [
            ({"type": "status", "status_kind": "main_chat_input_received"}, "input_received"),
            ({"type": "reasoning", "content": "planning..."}, "planning"),
            ({"type": "content", "content": "partial answer"}, "model_stream"),
            ({"type": "tool_permission_required", "tool_name": "shell"}, "tool_decision"),
            ({"type": "tool_result", "name": "shell", "status": "ok"}, "observation"),
            ({"type": "status", "status_kind": "execution_progress", "phase": "completion_retry"}, "review"),
            ({"type": "content", "content": "finalized", "completion_check": {"stage": "finalized"}}, "review"),
            ({"type": "done", "content": "complete"}, "final_output"),
        ]

        for event, expected_stage in cases:
            with self.subTest(expected_stage=expected_stage):
                mapping = mapper.map_main_chat_event(event)

                self.assertIsNotNone(mapping)
                self.assertEqual(mapping["stage"], expected_stage)
                self.assertEqual(mapping["channel"], "main_chat")

    def test_map_main_chat_event_returns_none_for_governance_or_non_lifecycle_events(self):
        mapper = QueryControlEventMapperService()

        self.assertIsNone(mapper.map_main_chat_event({"type": "status", "status_kind": "approval_created"}))
        self.assertIsNone(mapper.map_main_chat_event({"type": "tool_result", "status": "pending_permission"}))
        self.assertIsNone(mapper.map_main_chat_event({
            "type": "done",
            "content": "等待审批",
            "state": "waiting_approval",
            "stop_reason": "approval_required",
        }))

    def test_map_embedded_sdk_events_to_query_lifecycle_stages(self):
        mapper = QueryControlEventMapperService()

        cases = [
            ({"status_kind": "run_created"}, "input_received"),
            ({"status_kind": "execution_loop_step", "loop_step": "planning"}, "planning"),
            ({"status_kind": "execution_loop_step", "loop_step": "generating"}, "model_stream"),
            ({"status_kind": "tool_permission_required"}, "tool_decision"),
            ({"status_kind": "tool_call_started"}, "tool_execution"),
            ({"status_kind": "tool_result"}, "observation"),
            ({"status_kind": "execution_loop_reviewed"}, "review"),
            ({"status_kind": "execution_loop_done"}, "final_output"),
        ]

        for event, expected_stage in cases:
            with self.subTest(expected_stage=expected_stage):
                mapping = mapper.map_embedded_sdk_event(event)

                self.assertIsNotNone(mapping)
                self.assertEqual(mapping["stage"], expected_stage)
                self.assertEqual(mapping["channel"], "embedded_sdk")

    def test_map_embedded_sdk_event_returns_none_for_non_lifecycle_events(self):
        mapper = QueryControlEventMapperService()

        self.assertIsNone(mapper.map_embedded_sdk_event({"status_kind": "artifact_created"}))
        self.assertIsNone(mapper.map_embedded_sdk_event({"status_kind": "execution_loop_step", "loop_step": "unknown"}))

    def test_map_external_adapter_events_to_query_lifecycle_stages(self):
        mapper = QueryControlEventMapperService()

        cases = [
            ({"payload": {"framework_adapter_event_type": "framework_adapter_status"}}, "model_stream"),
            ({"payload": {"framework_adapter_event_type": "framework_adapter_reasoning"}}, "planning"),
            ({"payload": {"framework_adapter_event_type": "framework_adapter_output"}}, "final_output"),
            ({"payload": {"framework_adapter_event_type": "framework_adapter_external_error"}}, "final_output"),
        ]

        for event, expected_stage in cases:
            with self.subTest(expected_stage=expected_stage):
                mapping = mapper.map_external_adapter_event(event)

                self.assertIsNotNone(mapping)
                self.assertEqual(mapping["stage"], expected_stage)
                self.assertEqual(mapping["channel"], "external_adapter")

    def test_map_external_adapter_event_returns_none_for_unknown_events(self):
        mapper = QueryControlEventMapperService()

        self.assertIsNone(mapper.map_external_adapter_event({"payload": {"framework_adapter_event_type": "other"}}))

    def test_map_subagent_events_to_query_lifecycle_stages(self):
        mapper = QueryControlEventMapperService()

        cases = [
            ({"status_kind": "child_run_created"}, "input_received"),
            ({"status_kind": "subagent_spawned"}, "planning"),
            ({"status_kind": "subagent_collected"}, "observation"),
            ({"status_kind": "subagent_merged"}, "final_output"),
        ]

        for event, expected_stage in cases:
            with self.subTest(expected_stage=expected_stage):
                mapping = mapper.map_subagent_event(event)

                self.assertIsNotNone(mapping)
                self.assertEqual(mapping["stage"], expected_stage)
                self.assertEqual(mapping["channel"], "subagent_lane")

    def test_map_subagent_event_returns_none_for_unknown_events(self):
        mapper = QueryControlEventMapperService()

        self.assertIsNone(mapper.map_subagent_event({"status_kind": "run_created"}))

    def test_build_record_payload_preserves_event_identity_without_full_event_body(self):
        mapper = QueryControlEventMapperService()

        payload = mapper.build_record_payload({
            "id": "evt-1",
            "run_id": "run-1",
            "parent_run_id": "sched-1",
            "child_run_id": "child-run-1",
            "child_display_id": "child-run-1",
            "status_kind": "execution_loop_step",
            "type": "status",
            "loop_step": "planning",
            "summary": "Execution loop entered planning",
            "large_blob": "not included",
        })

        self.assertEqual(payload["source_event_id"], "evt-1")
        self.assertEqual(payload["source_run_id"], "run-1")
        self.assertEqual(payload["source_parent_run_id"], "sched-1")
        self.assertEqual(payload["source_child_run_id"], "child-run-1")
        self.assertEqual(payload["source_child_display_id"], "child-run-1")
        self.assertEqual(payload["source_status_kind"], "execution_loop_step")
        self.assertEqual(payload["source_event_type"], "status")
        self.assertEqual(payload["source_loop_step"], "planning")
        self.assertNotIn("large_blob", payload)

    def test_build_record_payload_includes_compact_tool_runtime_observation(self):
        mapper = QueryControlEventMapperService()

        payload = mapper.build_record_payload({
            "event_id": "evt-tool-1",
            "run_id": "run-1",
            "type": "tool_result",
            "status_kind": "tool_result",
            "tool_name": "risk_lookup",
            "result": "large result text should not be copied",
            "execution": {
                "executor": "tool_runtime_service",
                "schema_validation": {"status": "passed", "missing_required": []},
                "policy_decision": {
                    "status": "approval_required",
                    "permission_level": "ask",
                    "reason_code": "permission_level_requires_approval",
                    "reason": "registered tool permission_level requires approval before execution",
                },
                "retry": {
                    "status": "recovered",
                    "attempt_count": 2,
                    "max_attempts": 2,
                    "errors": ["temporary failure"],
                },
                "timeout": {
                    "status": "exceeded",
                    "timeout_seconds": 0.1,
                    "elapsed_seconds": 0.2,
                    "enforcement": "post_call_elapsed_check",
                },
                "observation": {
                    "status": "timeout",
                    "result_text": "large result text should not be copied",
                },
            },
        })

        observation = payload["tool_runtime_observation"]
        self.assertEqual(observation["tool_name"], "risk_lookup")
        self.assertEqual(observation["status"], "timeout")
        self.assertEqual(observation["executor"], "tool_runtime_service")
        self.assertEqual(observation["policy_status"], "approval_required")
        self.assertEqual(observation["policy_permission_level"], "ask")
        self.assertEqual(observation["policy_reason_code"], "permission_level_requires_approval")
        self.assertEqual(observation["schema_validation_status"], "passed")
        self.assertEqual(observation["retry_status"], "recovered")
        self.assertEqual(observation["retry_attempt_count"], 2)
        self.assertEqual(observation["retry_max_attempts"], 2)
        self.assertEqual(observation["timeout_status"], "exceeded")
        self.assertEqual(observation["timeout_seconds"], 0.1)
        self.assertEqual(observation["timeout_enforcement"], "post_call_elapsed_check")
        self.assertNotIn("result", observation)
        self.assertNotIn("result_text", observation)


if __name__ == "__main__":
    unittest.main()
