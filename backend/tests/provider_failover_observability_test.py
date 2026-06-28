from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from backend.routers.providers import get_failover_analytics
from backend.services import provider_failover_analytics_service as failover_module
from backend.services.provider_failover_analytics_service import ProviderFailoverAnalyticsService


@dataclass
class _FakePlanItem:
    updated_at: datetime


class _FakeQuery:
    def __init__(self, items):
        self._items = items

    def order_by(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def all(self):
        return self._items


class _FakeDb:
    def __init__(self, items):
        self._items = items

    def query(self, _model):
        return _FakeQuery(self._items)


class _FakeSchedulerService:
    def __init__(self, _db):
        pass

    def serialize_child_executions(self, item):
        if item.updated_at.year < 2025:
            return []
        return [
            {
                "provider_name": "ollama",
                "model_name": "llama3.1",
                "provider_switch_count": 1,
                "provider_history": [
                    {"provider_name": "ark", "model_name": "doubao"},
                    {"provider_name": "ollama", "model_name": "llama3.1"},
                ],
            },
            {
                "provider_name": "ollama",
                "model_name": "llama3.1",
                "provider_switch_count": 0,
                "provider_history": [
                    {"provider_name": "ollama", "model_name": "llama3.1"}
                ],
            },
        ]


def test_failover_analytics_service_summarizes_windowed_history(monkeypatch: pytest.MonkeyPatch):
    now = datetime.now(timezone.utc)
    recent_item = _FakePlanItem(updated_at=now)
    stale_item = _FakePlanItem(updated_at=now - timedelta(days=30))
    db = _FakeDb([recent_item, stale_item])

    monkeypatch.setattr(failover_module, "SchedulerService", _FakeSchedulerService)
    service = ProviderFailoverAnalyticsService(db)

    summary = service.get_summary(window_days=7, limit=10)

    assert summary["window_days"] == 7
    assert summary["total_children"] == 2
    assert summary["switched_children"] == 1
    assert summary["total_switches"] == 1
    assert summary["switch_rate"] == 0.5
    assert summary["average_switches_per_switched_child"] == 1.0
    assert summary["top_target_providers"] == [{"name": "ollama", "count": 2}]
    assert summary["top_provider_failover_pairs"] == [{"name": "ark->ollama", "count": 1}]
    assert summary["top_target_models"] == [{"name": "llama3.1", "count": 2}]


def test_failover_analytics_route_enforces_bounds_and_uses_summary(monkeypatch: pytest.MonkeyPatch):
    with pytest.raises(HTTPException) as exc_info:
        get_failover_analytics(window_days=5, limit=10, db=object())
    assert exc_info.value.status_code == 400

    class _FakeService:
        def __init__(self):
            self.calls = []

        def get_summary(self, *, window_days: int, limit: int):
            self.calls.append((window_days, limit))
            return {"window_days": window_days, "limit": limit, "switch_rate": 0.1}

    fake_service = _FakeService()
    monkeypatch.setattr(
        "backend.routers.providers.get_provider_failover_analytics_service",
        lambda _db: fake_service,
    )

    result = get_failover_analytics(window_days=7, limit=100, db=object())

    assert result == {"window_days": 7, "limit": 100, "switch_rate": 0.1}
    assert fake_service.calls == [(7, 100)]
