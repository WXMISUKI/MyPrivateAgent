import unittest
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from backend.services.context_compaction_service import ContextCompactionService


class TestContextCompaction(unittest.TestCase):
    def setUp(self):
        self.service = ContextCompactionService(max_tokens=200)

    def test_short_conversation_unchanged(self):
        messages = [
            SystemMessage(content="You are helpful."),
            HumanMessage(content="Hi"),
            AIMessage(content="Hello!"),
        ]
        result = self.service.compact(messages)
        self.assertEqual(len(result), 3)

    def test_long_conversation_truncated(self):
        messages = [SystemMessage(content="System prompt.")]
        for i in range(50):
            messages.append(HumanMessage(content=f"Question {i} " * 20))
            messages.append(AIMessage(content=f"Answer {i} " * 20))
        result = self.service.compact(messages)
        self.assertLess(len(result), len(messages))
        self.assertIsInstance(result[0], SystemMessage)

    def test_system_messages_preserved(self):
        messages = [
            SystemMessage(content="System 1"),
            SystemMessage(content="System 2"),
            HumanMessage(content="Old question " * 100),
            AIMessage(content="Old answer " * 100),
            HumanMessage(content="Recent question"),
            AIMessage(content="Recent answer"),
        ]
        result = self.service.compact(messages)
        system_msgs = [m for m in result if isinstance(m, SystemMessage)]
        self.assertGreaterEqual(len(system_msgs), 1)

    def test_count_tokens_returns_int(self):
        count = self.service.count_tokens("Hello world")
        self.assertIsInstance(count, int)
        self.assertGreater(count, 0)


if __name__ == "__main__":
    unittest.main()
