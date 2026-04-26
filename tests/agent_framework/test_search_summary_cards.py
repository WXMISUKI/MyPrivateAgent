import unittest

from backend.agent_framework.card_schemas import SEARCH_SUMMARY_CARD_SCHEMA, build_search_summary_card


class SearchSummaryCardTests(unittest.TestCase):
    def test_build_search_summary_card_success(self):
        card = build_search_summary_card("OpenAI", "关于'OpenAI'的信息：一家人工智能公司。")
        self.assertIsNotNone(card)
        self.assertEqual(card["schema"], SEARCH_SUMMARY_CARD_SCHEMA)
        self.assertEqual(card["kind"], "search_summary")
        self.assertEqual(card["query"], "OpenAI")
        self.assertEqual(card["status"], "success")
        self.assertEqual(card["summary"], "一家人工智能公司。")
        self.assertEqual(card["source"], "search_tool")
        self.assertEqual(card["source_label"], "搜索工具")
        self.assertEqual(card["source_count"], 1)

    def test_build_search_summary_card_not_found(self):
        card = build_search_summary_card("未知词条", "关于'未知词条'的信息：我在知识库中未找到相关内容。")
        self.assertEqual(card["status"], "not_found")
        self.assertEqual(card["source"], "knowledge_base")
        self.assertEqual(card["source_label"], "知识库")
        self.assertEqual(card["source_count"], 0)


if __name__ == "__main__":
    unittest.main()
