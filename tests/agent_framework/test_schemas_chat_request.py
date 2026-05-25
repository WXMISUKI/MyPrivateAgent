import unittest

from pydantic import ValidationError

from backend.schemas import ChatRequest


class ChatRequestSchemaTests(unittest.TestCase):
    def test_chat_request_accepts_typed_execution_context(self):
        payload = ChatRequest(
            message="请总结今天进度",
            model_name="doubao",
            execution_context={
                "run_id": "manual-chat-1",
                "run_kind": "chat",
                "enable_main_chat_query_control_timeline": True,
            },
        )

        self.assertIsNotNone(payload.execution_context)
        self.assertEqual(payload.execution_context.run_id, "manual-chat-1")
        self.assertEqual(payload.execution_context.run_kind, "chat")
        self.assertTrue(payload.execution_context.enable_main_chat_query_control_timeline)

    def test_chat_request_rejects_unknown_execution_context_fields(self):
        with self.assertRaises(ValidationError):
            ChatRequest(
                message="请总结今天进度",
                execution_context={
                    "run_id": "manual-chat-1",
                    "unexpected_field": "should-fail",
                },
            )


if __name__ == "__main__":
    unittest.main()
