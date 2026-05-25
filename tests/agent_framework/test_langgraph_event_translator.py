import unittest

from backend.agent_framework.external.langgraph_translators import (
    LangGraphEventTranslator,
    LangGraphOutputTranslator,
)


class LangGraphEventTranslatorTests(unittest.TestCase):
    def test_translate_chunk_maps_status_to_platform_status_event(self):
        translator = LangGraphEventTranslator(
            adapter_id="langgraph_draft",
            framework_name="LangGraph",
        )

        events = translator.translate_chunk(
            run_id="run_1",
            chunk={"type": "status", "status": "accepted", "detail": "runtime accepted request"},
            execution_context={"plan_id": 101},
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "status")
        self.assertEqual(events[0]["source"], "framework_adapter")
        self.assertEqual(events[0]["payload"]["adapter_id"], "langgraph_draft")
        self.assertEqual(events[0]["payload"]["framework_name"], "LangGraph")
        self.assertEqual(events[0]["payload"]["status"], "accepted")
        self.assertEqual(events[0]["payload"]["framework_adapter_event_type"], "framework_adapter_status")

    def test_translate_chunk_maps_reasoning_to_platform_reasoning_event(self):
        translator = LangGraphEventTranslator(
            adapter_id="langgraph_draft",
            framework_name="LangGraph",
        )

        events = translator.translate_chunk(
            run_id="run_2",
            chunk={"type": "reasoning", "summary": "planning next step", "detail": "node=planner"},
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "reasoning")
        self.assertEqual(events[0]["payload"]["framework_adapter_event_type"], "framework_adapter_reasoning")

    def test_translate_chunk_maps_error_to_platform_error_event(self):
        translator = LangGraphEventTranslator(
            adapter_id="langgraph_draft",
            framework_name="LangGraph",
        )

        events = translator.translate_chunk(
            run_id="run_3",
            chunk={
                "type": "error",
                "error_type": "connectivity_error",
                "detail": "connect failed",
            },
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "error")
        self.assertEqual(events[0]["source"], "framework_adapter")
        self.assertEqual(events[0]["payload"]["error_type"], "connectivity_error")
        self.assertEqual(
            events[0]["payload"]["framework_adapter_event_type"],
            "framework_adapter_external_error",
        )

    def test_translate_final_maps_output_to_platform_content_event(self):
        translator = LangGraphOutputTranslator(
            adapter_id="langgraph_draft",
            framework_name="LangGraph",
        )

        events = translator.translate_final(
            run_id="run_4",
            output={"content": "final answer"},
            execution_context={"plan_item_id": 202},
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "content")
        self.assertEqual(events[0]["source"], "framework_adapter")
        self.assertEqual(events[0]["payload"]["content"], "final answer")
        self.assertEqual(events[0]["payload"]["framework_adapter_event_type"], "framework_adapter_output")


if __name__ == "__main__":
    unittest.main()
