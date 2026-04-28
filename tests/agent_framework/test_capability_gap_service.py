import unittest
from types import SimpleNamespace

from backend.services.capability_gap_service import CapabilityGapService


class _QueryStub:
    def __init__(self, items):
        self.items = items

    def order_by(self, *_args, **_kwargs):
        return self

    def limit(self, _value):
        return self

    def all(self):
        return self.items


class _DbStub:
    def __init__(self, items):
        self.items = items

    def query(self, _model):
        return _QueryStub(self.items)


class CapabilityGapServiceTests(unittest.TestCase):
    def test_get_summary_aggregates_recent_gap_events(self):
        items = [
            SimpleNamespace(
                id=1,
                title="规划舟山旅行",
                item_metadata={
                    "run_trace": [
                        {
                            "event_type": "capability_gap_fallback",
                            "summary": "框架已触发能力边界降级收口",
                            "detail": "当前缺少可靠交通建议。",
                            "timestamp": "2026-04-28T09:00:00Z",
                            "payload": {
                                "missing_parts": ["transport", "play"],
                                "profile": "travel_planning",
                                "completion_stage": "boundary_fallback",
                            },
                        },
                        {
                            "event_type": "tool_failed",
                            "summary": "工具 `search` 执行失败",
                            "detail": "执行错误: network timeout",
                            "timestamp": "2026-04-28T09:00:10Z",
                            "payload": {"error_category": "provider_timeout"},
                        }
                    ]
                },
            ),
            SimpleNamespace(
                id=2,
                title="安排交通与景点",
                item_metadata={
                    "run_trace": [
                        {
                            "event_type": "capability_gap_fallback",
                            "summary": "框架已触发能力边界降级收口",
                            "detail": "当前缺少可靠交通建议。",
                            "timestamp": "2026-04-28T09:10:00Z",
                            "payload": {
                                "missing_parts": ["transport"],
                                "profile": "planning",
                                "completion_stage": "timeout_fallback",
                            },
                        }
                    ]
                },
            ),
        ]

        service = CapabilityGapService(_DbStub(items))
        summary = service.get_summary(limit=20)

        self.assertEqual(summary["total_gap_events"], 2)
        self.assertEqual(summary["top_missing_parts"][0], {"name": "transport", "count": 2})
        self.assertIn("交通路线检索工具", summary["suggested_investments"][0])
        self.assertEqual(summary["top_profiles"][0], {"name": "travel_planning", "count": 1})
        self.assertEqual(summary["top_completion_stages"][0], {"name": "boundary_fallback", "count": 1})
        self.assertEqual(summary["top_error_categories"][0], {"name": "provider_timeout", "count": 1})

    def test_get_summary_supports_missing_part_and_keyword_filters(self):
        items = [
            SimpleNamespace(
                id=1,
                title="规划舟山旅行",
                item_metadata={
                    "run_trace": [
                        {
                            "event_type": "capability_gap_fallback",
                            "summary": "框架已触发能力边界降级收口",
                            "detail": "当前缺少可靠交通建议。",
                            "timestamp": "2026-04-28T09:00:00Z",
                            "payload": {
                                "missing_parts": ["transport", "play"],
                                "profile": "travel_planning",
                                "completion_stage": "boundary_fallback",
                            },
                        }
                    ]
                },
            ),
            SimpleNamespace(
                id=2,
                title="安排天气说明",
                item_metadata={
                    "run_trace": [
                        {
                            "event_type": "capability_gap_fallback",
                            "summary": "框架已触发能力边界降级收口",
                            "detail": "当前缺少稳定天气源。",
                            "timestamp": "2026-04-28T09:10:00Z",
                            "payload": {
                                "missing_parts": ["weather"],
                                "profile": "research_compare",
                                "completion_stage": "retry",
                            },
                        }
                    ]
                },
            ),
        ]

        service = CapabilityGapService(_DbStub(items))
        summary = service.get_summary(
            limit=20,
            missing_part="transport",
            keyword="舟山",
            profile="travel_planning",
            completion_stage="boundary_fallback",
        )

        self.assertEqual(summary["total_gap_events"], 1)
        self.assertEqual(summary["top_missing_parts"], [{"name": "transport", "count": 1}, {"name": "play", "count": 1}])
        self.assertEqual(summary["available_missing_parts"], ["play", "transport"])
        self.assertEqual(summary["applied_filters"]["missing_part"], "transport")
        self.assertEqual(summary["applied_filters"]["keyword"], "舟山")
        self.assertEqual(summary["applied_filters"]["profile"], "travel_planning")
        self.assertEqual(summary["applied_filters"]["completion_stage"], "boundary_fallback")
