"""Aggregate capability-gap signals from planner run traces."""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Iterable, List, Optional

try:
    from models import PlanItemRecord
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.models import PlanItemRecord


class CapabilityGapService:
    """Summarize recent capability-gap fallback signals for framework governance."""

    def __init__(self, db):
        self.db = db

    def get_summary(
        self,
        *,
        limit: int = 100,
        missing_part: Optional[str] = None,
        keyword: Optional[str] = None,
        profile: Optional[str] = None,
        completion_stage: Optional[str] = None,
        error_category: Optional[str] = None,
    ) -> Dict[str, Any]:
        items = (
            self.db.query(PlanItemRecord)
            .order_by(PlanItemRecord.updated_at.desc())
            .limit(max(1, int(limit)))
            .all()
        )

        normalized_missing_part = str(missing_part or "").strip().lower() or None
        normalized_keyword = str(keyword or "").strip().lower() or None
        normalized_profile = str(profile or "").strip() or None
        normalized_stage = str(completion_stage or "").strip() or None
        normalized_error_category = str(error_category or "").strip() or None
        gap_events: List[Dict[str, Any]] = []
        profile_counter: Counter[str] = Counter()
        stage_counter: Counter[str] = Counter()
        error_counter: Counter[str] = Counter()
        for item in items:
            metadata = dict(item.item_metadata or {})
            run_trace = metadata.get("run_trace") or []
            for entry in run_trace:
                if not isinstance(entry, dict):
                    continue
                event_type = str(entry.get("event_type") or "").strip()
                payload = entry.get("payload") or {}

                if event_type == "capability_gap_fallback":
                    missing_parts = self._normalize_list(payload.get("missing_parts") or [])
                    event_profile = str(payload.get("profile") or payload.get("completion_check", {}).get("profile") or "").strip()
                    event_stage = str(payload.get("completion_stage") or payload.get("completion_check", {}).get("stage") or "").strip()
                    searchable_text = " ".join(
                        [
                            str(item.title or "").strip(),
                            str(entry.get("summary") or "").strip(),
                            str(entry.get("detail") or "").strip(),
                        ]
                    ).lower()
                    if normalized_missing_part and normalized_missing_part not in missing_parts:
                        continue
                    if normalized_keyword and normalized_keyword not in searchable_text:
                        continue
                    if normalized_profile and normalized_profile != event_profile:
                        continue
                    if normalized_stage and normalized_stage != event_stage:
                        continue
                    gap_events.append(
                        {
                            "plan_item_id": item.id,
                            "title": item.title,
                            "summary": str(entry.get("summary") or "").strip(),
                            "detail": str(entry.get("detail") or "").strip(),
                            "timestamp": entry.get("timestamp"),
                            "missing_parts": missing_parts,
                            "profile": event_profile,
                            "completion_stage": event_stage,
                        }
                    )
                    profile_counter.update([event_profile] if event_profile else [])
                    stage_counter.update([event_stage] if event_stage else [])
                    continue

                if event_type not in {"tool_failed", "mcp_tool_failed"}:
                    continue
                current_error_category = str(payload.get("error_category") or "").strip()
                if not current_error_category:
                    continue
                searchable_text = " ".join(
                    [
                        str(item.title or "").strip(),
                        str(entry.get("summary") or "").strip(),
                        str(entry.get("detail") or "").strip(),
                    ]
                ).lower()
                if normalized_keyword and normalized_keyword not in searchable_text:
                    continue
                if normalized_error_category and normalized_error_category != current_error_category:
                    continue
                error_counter.update([current_error_category])

        part_counter: Counter[str] = Counter()
        for event in gap_events:
            part_counter.update(event["missing_parts"])

        top_missing_parts = [
            {"name": name, "count": count}
            for name, count in part_counter.most_common()
        ]

        suggestions = self._build_suggestions(part_counter.keys())
        recent_examples = gap_events[:5]

        return {
            "total_gap_events": len(gap_events),
            "top_missing_parts": top_missing_parts,
            "top_profiles": [{"name": name, "count": count} for name, count in profile_counter.most_common()],
            "top_completion_stages": [{"name": name, "count": count} for name, count in stage_counter.most_common()],
            "top_error_categories": [{"name": name, "count": count} for name, count in error_counter.most_common()],
            "suggested_investments": suggestions,
            "recent_examples": recent_examples,
            "available_missing_parts": sorted(part_counter.keys()),
            "available_profiles": sorted(profile_counter.keys()),
            "available_completion_stages": sorted(stage_counter.keys()),
            "available_error_categories": sorted(error_counter.keys()),
            "applied_filters": {
                "limit": max(1, int(limit)),
                "missing_part": normalized_missing_part,
                "keyword": normalized_keyword,
                "profile": normalized_profile,
                "completion_stage": normalized_stage,
                "error_category": normalized_error_category,
            },
        }

    def _normalize_list(self, values: Iterable[Any]) -> List[str]:
        normalized: List[str] = []
        for value in values or []:
            text = str(value or "").strip()
            if text and text not in normalized:
                normalized.append(text)
        return normalized

    def _build_suggestions(self, missing_parts: Iterable[str]) -> List[str]:
        suggestion_map = {
            "weather": "补充更稳定的天气/地理位置工具或天气 MCP。",
            "transport": "优先补交通路线检索工具，或接入地图 / 出行类 MCP。",
            "play": "优先补 POI / 景点检索工具，或接入旅游攻略类 MCP。",
        }
        suggestions: List[str] = []
        for part in missing_parts:
            suggestion = suggestion_map.get(part)
            if suggestion and suggestion not in suggestions:
                suggestions.append(suggestion)
        return suggestions


def get_capability_gap_service(db) -> CapabilityGapService:
    return CapabilityGapService(db)
