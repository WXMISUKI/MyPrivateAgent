import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from backend.services.provider_failover_analytics_service import ProviderFailoverAnalyticsService


class _StubQuery:
    def __init__(self, items):
        self.items = items

    def order_by(self, _field):
        return self

    def limit(self, _value):
        return self

    def all(self):
        return self.items


class _StubDb:
    def __init__(self, items):
        self.items = items

    def query(self, _model):
        return _StubQuery(self.items)


class ProviderFailoverAnalyticsServiceTests(unittest.TestCase):
    def test_get_summary_aggregates_failover_metrics(self):
        item = SimpleNamespace(
            updated_at=datetime.now(timezone.utc),
            item_metadata={
                "child_execution_group": {
                    "children": [
                        {
                            "provider_name": "ollama",
                            "model_name": "llama3.1",
                            "provider_switch_count": 1,
                            "provider_history": [
                                {"provider_name": "volcengine-ark", "model_name": "doubao", "reason": "initial"},
                                {"provider_name": "ollama", "model_name": "llama3.1", "reason": "provider_fallback_model_selected"},
                            ],
                        },
                        {
                            "provider_name": "volcengine-ark",
                            "model_name": "doubao",
                            "provider_switch_count": 0,
                            "provider_history": [
                                {"provider_name": "volcengine-ark", "model_name": "doubao", "reason": "initial"},
                            ],
                        },
                    ]
                }
            },
        )
        service = ProviderFailoverAnalyticsService(_StubDb([item]))

        summary = service.get_summary(window_days=7, limit=50)
        self.assertEqual(summary["total_children"], 2)
        self.assertEqual(summary["switched_children"], 1)
        self.assertEqual(summary["total_switches"], 1)
        self.assertEqual(summary["switch_rate"], 0.5)
        self.assertEqual(summary["top_provider_failover_pairs"][0]["name"], "volcengine-ark->ollama")


if __name__ == "__main__":
    unittest.main()

