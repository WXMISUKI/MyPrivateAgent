import unittest

from backend.agent_framework.adapters import InMemoryArtifactStore


class ArtifactStoreTests(unittest.TestCase):
    def test_artifact_store_filters_by_conversation_and_kind(self):
        store = InMemoryArtifactStore()
        store.create_artifact(conversation_id=1, kind="reasoning_trace", content="a")
        store.create_artifact(conversation_id=1, kind="tool_output", content="b")
        store.create_artifact(conversation_id=2, kind="reasoning_trace", content="c")

        conversation_items = store.list_artifacts(conversation_id=1)
        self.assertEqual(len(conversation_items), 2)

        reasoning_items = store.list_artifacts(conversation_id=1, kind="reasoning_trace")
        self.assertEqual(len(reasoning_items), 1)
        self.assertEqual(reasoning_items[0].content, "a")


if __name__ == "__main__":
    unittest.main()
