"""Query Control timeline recorder for main chat lifecycle events."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    from services.query_control_event_mapper_service import get_query_control_event_mapper_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.query_control_event_mapper_service import get_query_control_event_mapper_service


class MainChatQueryControlService:
    """Record mapped main chat lifecycle events into Query Control timeline."""

    def __init__(
        self,
        *,
        query_control_event_mapper: Any = None,
        query_control_timeline_service: Any = None,
    ) -> None:
        self.query_control_event_mapper = query_control_event_mapper or get_query_control_event_mapper_service()
        self.query_control_timeline_service = query_control_timeline_service

    def record_query_control_events(
        self,
        *,
        db: Any,
        conversation_id: Optional[int],
        query_id: str,
        events: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        recordings = []
        failures = []
        if db is None or self.query_control_timeline_service is None or not str(query_id or "").strip():
            return {"recordings": recordings, "failures": failures}
        for event in list(events or []):
            event_dict = dict(event or {})
            mapping = self.query_control_event_mapper.map_main_chat_event(event_dict)
            if mapping is None:
                continue
            try:
                recordings.append(self.query_control_timeline_service.record_stage(
                    db=db,
                    conversation_id=conversation_id,
                    channel=mapping["channel"],
                    stage=mapping["stage"],
                    query_id=query_id,
                    summary=str(event_dict.get("content") or event_dict.get("summary") or f"Main chat {mapping['stage']}"),
                    detail=str(event_dict.get("detail") or ""),
                    severity=str(event_dict.get("severity") or "info"),
                    payload=self.query_control_event_mapper.build_record_payload(event_dict),
                ))
            except Exception as exc:  # pragma: no cover - exact recorder failure belongs to integration.
                failures.append({
                    "stage": mapping["stage"],
                    "event_type": event_dict.get("type"),
                    "status_kind": event_dict.get("status_kind"),
                    "error": str(exc),
                })
        return {"recordings": recordings, "failures": failures}


_main_chat_query_control_service: Optional[MainChatQueryControlService] = None


def get_main_chat_query_control_service() -> MainChatQueryControlService:
    global _main_chat_query_control_service
    if _main_chat_query_control_service is None:
        _main_chat_query_control_service = MainChatQueryControlService()
    return _main_chat_query_control_service
