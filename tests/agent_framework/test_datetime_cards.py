import unittest

from backend.agent_framework.card_schemas import DATETIME_CARD_SCHEMA, build_datetime_card_from_text


class DateTimeCardTests(unittest.TestCase):
    def test_build_datetime_card_from_text(self):
        text = "2026-04-22 21:06:32 星期三"
        card = build_datetime_card_from_text(text)
        self.assertIsNotNone(card)
        self.assertEqual(card["schema"], DATETIME_CARD_SCHEMA)
        self.assertEqual(card["kind"], "datetime")
        self.assertEqual(card["date"], "2026/04/22")
        self.assertEqual(card["time"], "21:06:32")
        self.assertEqual(card["weekday"], "星期三")


if __name__ == "__main__":
    unittest.main()
