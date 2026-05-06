"""Aggregate provider failover metrics from planner child execution metadata."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

try:
    from models import PlanItemRecord
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.models import PlanItemRecord

try:
    from services.scheduler_service import SchedulerService
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.scheduler_service import SchedulerService


class ProviderFailoverAnalyticsService:
    """Summarize provider failover behavior for runtime operations visibility."""

    def __init__(self, db):
        self.db = db
        self.scheduler_service = SchedulerService(db)

    def get_summary(self, *, window_days: int = 7, limit: int = 500) -> Dict[str, Any]:
        window_days = max(1, int(window_days))
        limit = max(1, int(limit))
        now_utc = datetime.now(timezone.utc)
        window_start = now_utc - timedelta(days=window_days)

        items = (
            self.db.query(PlanItemRecord)
            .order_by(PlanItemRecord.updated_at.desc())
            .limit(limit)
            .all()
        )

        total_children = 0
        switched_children = 0
        total_switches = 0
        provider_target_counter: Counter[str] = Counter()
        provider_pair_counter: Counter[str] = Counter()
        model_counter: Counter[str] = Counter()

        for item in items:
            updated_at = getattr(item, "updated_at", None)
            if updated_at is None:
                continue
            updated_dt = self._to_utc(updated_at)
            if updated_dt is None or updated_dt < window_start:
                continue

            for child in self.scheduler_service.serialize_child_executions(item):
                total_children += 1
                switch_count = max(0, int(child.get("provider_switch_count") or 0))
                target_provider = str(child.get("provider_name") or "").strip()
                target_model = str(child.get("model_name") or "").strip()
                history = child.get("provider_history") or []

                if target_provider:
                    provider_target_counter.update([target_provider])
                if target_model:
                    model_counter.update([target_model])

                if switch_count > 0:
                    switched_children += 1
                    total_switches += switch_count

                if isinstance(history, list) and len(history) >= 2:
                    first = history[0] if isinstance(history[0], dict) else {}
                    last = history[-1] if isinstance(history[-1], dict) else {}
                    source_provider = str(first.get("provider_name") or "").strip()
                    final_provider = str(last.get("provider_name") or "").strip()
                    if source_provider and final_provider and source_provider != final_provider:
                        provider_pair_counter.update([f"{source_provider}->{final_provider}"])

        switch_rate = round((switched_children / total_children), 4) if total_children > 0 else 0.0
        average_switches = round((total_switches / switched_children), 4) if switched_children > 0 else 0.0

        return {
            "window_days": window_days,
            "total_children": total_children,
            "switched_children": switched_children,
            "total_switches": total_switches,
            "switch_rate": switch_rate,
            "average_switches_per_switched_child": average_switches,
            "top_target_providers": [
                {"name": name, "count": count}
                for name, count in provider_target_counter.most_common(5)
            ],
            "top_provider_failover_pairs": [
                {"name": name, "count": count}
                for name, count in provider_pair_counter.most_common(5)
            ],
            "top_target_models": [
                {"name": name, "count": count}
                for name, count in model_counter.most_common(5)
            ],
        }

    def _to_utc(self, value: Any) -> Optional[datetime]:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        text = str(value or "").strip()
        if not text:
            return None
        try:
            normalized = text.replace("Z", "+00:00")
            dt = datetime.fromisoformat(normalized)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            return None


def get_provider_failover_analytics_service(db) -> ProviderFailoverAnalyticsService:
    return ProviderFailoverAnalyticsService(db)
