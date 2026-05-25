import unittest

from backend.agent_framework.external.langgraph_translators import (
    LangGraphRequestTranslator,
)


class LangGraphRequestTranslatorTests(unittest.TestCase):
    def test_translate_returns_stable_request_shape(self):
        translator = LangGraphRequestTranslator(
            adapter_id="langgraph_draft",
            framework_name="LangGraph",
            assistant_id="assistant-1",
            endpoint="https://example.test/langgraph",
        )

        payload = translator.translate(
            run_id="run-1",
            messages=[{"role": "user", "content": "hello"}],
            execution_context={
                "plan_id": "plan-1",
                "tenant_id": "tenant-ignored",
                "run_kind": "chat",
            },
        )

        self.assertEqual(
            payload,
            {
                "adapter_id": "langgraph_draft",
                "framework_name": "LangGraph",
                "run_id": "run-1",
                "assistant_id": "assistant-1",
                "endpoint": "https://example.test/langgraph",
                "messages": [{"role": "user", "content": "hello"}],
                "execution_context": {
                    "plan_id": "plan-1",
                    "run_kind": "chat",
                },
            },
        )

    def test_translate_normalizes_message_role_and_content(self):
        translator = LangGraphRequestTranslator(
            adapter_id="langgraph_draft",
            framework_name="LangGraph",
            assistant_id="assistant-1",
            endpoint="https://example.test/langgraph",
        )

        payload = translator.translate(
            run_id="run-2",
            messages=[
                {"role": " Assistant ", "content": "  hi  "},
                {"role": "", "content": None},
                {"content": 42},
            ],
        )

        self.assertEqual(
            payload["messages"],
            [
                {"role": "assistant", "content": "hi"},
                {"role": "user", "content": ""},
                {"role": "user", "content": "42"},
            ],
        )

    def test_translate_does_not_leak_empty_execution_context_fields(self):
        translator = LangGraphRequestTranslator(
            adapter_id="langgraph_draft",
            framework_name="LangGraph",
            assistant_id="assistant-1",
            endpoint="https://example.test/langgraph",
        )

        payload = translator.translate(
            run_id="run-3",
            messages=[{"content": "hello"}],
            execution_context={},
        )

        self.assertEqual(payload["execution_context"], {})


if __name__ == "__main__":
    unittest.main()
