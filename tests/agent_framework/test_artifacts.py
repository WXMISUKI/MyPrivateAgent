import unittest

from backend.agent_framework.adapters import InMemoryArtifactStore
from backend.agent_framework.card_schemas import SEARCH_SUMMARY_CARD_SCHEMA


class ArtifactStoreTests(unittest.TestCase):
    def test_create_artifact_preserves_schema_rendering_fields(self):
        store = InMemoryArtifactStore()
        card = {
            "kind": "search_summary",
            "schema": SEARCH_SUMMARY_CARD_SCHEMA,
            "query": "OpenAI",
            "status": "success",
            "summary": "一家人工智能公司。",
            "source": "knowledge_base",
            "source_label": "知识库",
            "source_count": 1,
        }

        artifact = store.create_artifact(
            conversation_id=42,
            kind="tool_result",
            content="关于'OpenAI'的信息：一家人工智能公司。",
            render_mode="structured_card",
            card_schema=SEARCH_SUMMARY_CARD_SCHEMA,
            card=card,
            metadata={"tool_name": "search"},
        )

        self.assertEqual(artifact.conversation_id, 42)
        self.assertEqual(artifact.kind, "tool_result")
        self.assertEqual(artifact.render_mode, "structured_card")
        self.assertEqual(artifact.card_schema, SEARCH_SUMMARY_CARD_SCHEMA)
        self.assertEqual(artifact.card, card)
        self.assertEqual(artifact.metadata["tool_name"], "search")


if __name__ == "__main__":
    unittest.main()
