import unittest
from types import SimpleNamespace
from datetime import datetime, timedelta, timezone

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
                                "provider": "volcengine-ark",
                                "model_name": "doubao",
                            },
                        },
                        {
                            "event_type": "tool_failed",
                            "summary": "工具 `search` 执行失败",
                            "detail": "执行错误: network timeout",
                            "timestamp": "2026-04-28T09:00:10Z",
                            "payload": {"error_category": "provider_timeout", "provider": "volcengine-ark", "model_name": "doubao"},
                        },
                        {
                            "source": "hook",
                            "event_type": "pre_tool_use_blocked",
                            "summary": "Hook 阻断工具调用",
                            "detail": "命中高风险策略",
                            "timestamp": "2026-04-28T09:00:20Z",
                            "payload": {"tool_name": "mcp_filesystem_write", "provider": "volcengine-ark", "model_name": "doubao"},
                        },
                        {
                            "source": "subagent",
                            "event_type": "child_completed",
                            "summary": "backend 子执行已完成",
                            "detail": "agent_id=backend-agent",
                            "timestamp": "2026-04-28T09:00:21Z",
                            "payload": {"agent_role": "backend", "provider": "volcengine-ark", "model_name": "doubao"},
                        },
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
                                "provider": "volcengine-ark",
                                "model_name": "doubao",
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
        self.assertEqual(summary["top_hook_event_types"][0], {"name": "pre_tool_use_blocked", "count": 1})
        self.assertEqual(summary["top_subagent_roles"][0], {"name": "backend", "count": 1})
        self.assertEqual(summary["top_providers"][0], {"name": "volcengine-ark", "count": 5})
        self.assertEqual(summary["top_models"][0], {"name": "doubao", "count": 5})
        self.assertEqual(summary["trend_by_day"], [{"date": "2026-04-28", "count": 2}])
        self.assertEqual(summary["provider_model_pairs"], [{"provider": "volcengine-ark", "model": "doubao", "count": 2}])
        self.assertEqual(
            summary["profile_provider_model_pairs"],
            [
                {"profile": "travel_planning", "provider": "volcengine-ark", "model": "doubao", "count": 1},
                {"profile": "planning", "provider": "volcengine-ark", "model": "doubao", "count": 1},
            ],
        )
        self.assertEqual(summary["window_comparison"]["window_days"], None)
        self.assertEqual(summary["top_regression_risk_models"], [])
        self.assertIn("benchmark_health", summary)
        self.assertEqual(summary["benchmark_health"]["total_assertions"], 4)
        self.assertGreaterEqual(summary["benchmark_health"]["passed_assertions"], 1)
        self.assertEqual(summary["benchmark_health"]["threshold_score"], 80.0)
        self.assertIn("gate_passed", summary["benchmark_health"])
        self.assertIn("required_profiles", summary["benchmark_health"])
        self.assertIn("covered_profiles", summary["benchmark_health"])
        self.assertIn("missing_profiles", summary["benchmark_health"])
        self.assertIn("benchmark_catalog_total", summary["benchmark_health"])
        self.assertIn("benchmark_catalog_matched", summary["benchmark_health"])
        self.assertIn("benchmark_catalog_coverage_ratio", summary["benchmark_health"])
        self.assertIn("benchmark_catalog_unmatched", summary["benchmark_health"])
        self.assertIn("scenario_coverage", summary["benchmark_health"])
        self.assertIn("action_playbook", summary["benchmark_health"])
        if summary["benchmark_health"]["benchmark_catalog_unmatched"]:
            self.assertIn("remediation", summary["benchmark_health"]["benchmark_catalog_unmatched"][0])
            self.assertIn("remediation_action_id", summary["benchmark_health"]["benchmark_catalog_unmatched"][0])

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
                                "provider": "volcengine-ark",
                                "model_name": "doubao",
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
                                "provider": "ollama",
                                "model_name": "llama3.1",
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

    def test_get_summary_supports_hook_and_subagent_filters(self):
        items = [
            SimpleNamespace(
                id=1,
                title="执行治理检查",
                item_metadata={
                    "run_trace": [
                        {
                            "source": "hook",
                            "event_type": "pre_tool_use_blocked",
                            "summary": "Hook 阻断工具调用",
                            "detail": "命中高风险策略",
                            "timestamp": "2026-04-28T09:00:20Z",
                            "payload": {"tool_name": "mcp_filesystem_write"},
                        },
                        {
                            "source": "subagent",
                            "event_type": "child_completed",
                            "summary": "frontend 子执行已完成",
                            "detail": "agent_id=frontend-agent",
                            "timestamp": "2026-04-28T09:00:21Z",
                            "payload": {"agent_role": "frontend", "provider": "volcengine-ark", "model_name": "doubao"},
                        },
                        {
                            "source": "subagent",
                            "event_type": "child_completed",
                            "summary": "backend 子执行已完成",
                            "detail": "agent_id=backend-agent",
                            "timestamp": "2026-04-28T09:00:22Z",
                            "payload": {"agent_role": "backend", "provider": "ollama", "model_name": "llama3.1"},
                        },
                    ]
                },
            ),
        ]

        service = CapabilityGapService(_DbStub(items))
        summary = service.get_summary(limit=20, hook_event_type="pre_tool_use_blocked", subagent_role="frontend")

        self.assertEqual(summary["top_hook_event_types"], [{"name": "pre_tool_use_blocked", "count": 1}])
        self.assertEqual(summary["top_subagent_roles"], [{"name": "frontend", "count": 1}])
        self.assertEqual(summary["applied_filters"]["hook_event_type"], "pre_tool_use_blocked")
        self.assertEqual(summary["applied_filters"]["subagent_role"], "frontend")

    def test_get_summary_supports_provider_and_model_filters(self):
        items = [
            SimpleNamespace(
                id=1,
                title="provider model filter",
                item_metadata={
                    "run_trace": [
                        {
                            "event_type": "capability_gap_fallback",
                            "summary": "框架已触发能力边界降级收口",
                            "detail": "当前缺少可靠交通建议。",
                            "timestamp": "2026-04-28T09:00:00Z",
                            "payload": {
                                "missing_parts": ["transport"],
                                "profile": "travel_planning",
                                "completion_stage": "boundary_fallback",
                                "provider": "volcengine-ark",
                                "model_name": "doubao",
                            },
                        },
                        {
                            "event_type": "capability_gap_fallback",
                            "summary": "框架已触发能力边界降级收口",
                            "detail": "当前缺少稳定天气源。",
                            "timestamp": "2026-04-28T09:10:00Z",
                            "payload": {
                                "missing_parts": ["weather"],
                                "profile": "research_compare",
                                "completion_stage": "retry",
                                "provider": "ollama",
                                "model_name": "llama3.1",
                            },
                        },
                    ]
                },
            ),
        ]

        service = CapabilityGapService(_DbStub(items))
        summary = service.get_summary(limit=20, provider="volcengine-ark", model_name="doubao")

        self.assertEqual(summary["total_gap_events"], 1)
        self.assertEqual(summary["top_providers"], [{"name": "volcengine-ark", "count": 1}])
        self.assertEqual(summary["top_models"], [{"name": "doubao", "count": 1}])
        self.assertEqual(summary["trend_by_day"], [{"date": "2026-04-28", "count": 1}])
        self.assertEqual(summary["provider_model_pairs"], [{"provider": "volcengine-ark", "model": "doubao", "count": 1}])
        self.assertEqual(
            summary["profile_provider_model_pairs"],
            [{"profile": "travel_planning", "provider": "volcengine-ark", "model": "doubao", "count": 1}],
        )
        self.assertEqual(summary["applied_filters"]["provider"], "volcengine-ark")
        self.assertEqual(summary["applied_filters"]["model_name"], "doubao")

    def test_get_summary_supports_window_days_filter(self):
        now = datetime.now(timezone.utc)
        in_window = (now - timedelta(days=2)).isoformat().replace("+00:00", "Z")
        out_window = (now - timedelta(days=40)).isoformat().replace("+00:00", "Z")
        items = [
            SimpleNamespace(
                id=1,
                title="window-days-filter",
                item_metadata={
                    "run_trace": [
                        {
                            "event_type": "capability_gap_fallback",
                            "summary": "框架已触发能力边界降级收口",
                            "detail": "窗口内事件",
                            "timestamp": in_window,
                            "payload": {
                                "missing_parts": ["transport"],
                                "profile": "planning",
                                "completion_stage": "boundary_fallback",
                                "provider": "volcengine-ark",
                                "model_name": "doubao",
                            },
                        },
                        {
                            "event_type": "capability_gap_fallback",
                            "summary": "框架已触发能力边界降级收口",
                            "detail": "窗口外事件",
                            "timestamp": out_window,
                            "payload": {
                                "missing_parts": ["play"],
                                "profile": "planning",
                                "completion_stage": "boundary_fallback",
                                "provider": "volcengine-ark",
                                "model_name": "doubao",
                            },
                        },
                    ]
                },
            ),
        ]

        service = CapabilityGapService(_DbStub(items))
        summary = service.get_summary(limit=20, window_days=7)

        self.assertEqual(summary["total_gap_events"], 1)
        self.assertEqual(summary["top_missing_parts"], [{"name": "transport", "count": 1}])
        self.assertEqual(summary["applied_filters"]["window_days"], 7)
        self.assertEqual(summary["window_comparison"]["window_days"], 7)
        self.assertEqual(summary["window_comparison"]["current_count"], 1)
        self.assertEqual(summary["window_comparison"]["previous_count"], 0)
        self.assertEqual(summary["window_comparison"]["delta_count"], 1)
        self.assertEqual(
            summary["top_regression_risk_models"],
            [
                {
                    "provider": "volcengine-ark",
                    "model": "doubao",
                    "current_count": 1,
                    "previous_count": 0,
                    "delta_count": 1,
                    "risk_level": "medium",
                }
            ],
        )
        self.assertIn("benchmark_health", summary)
        self.assertEqual(summary["benchmark_health"]["total_assertions"], 4)
        self.assertEqual(summary["benchmark_health"]["threshold_score"], 80.0)
        self.assertIn("benchmark_catalog_total", summary["benchmark_health"])
        self.assertIn("scenario_coverage", summary["benchmark_health"])
