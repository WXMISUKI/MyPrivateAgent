"""Timeline adapter for self-improvement governance events."""

from __future__ import annotations

from typing import Any, Callable, Optional

try:
    from services.run_trace_service import get_run_trace_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.run_trace_service import get_run_trace_service


class SelfImprovementTimelineService:
    """Record learning governance actions into trace and audit streams."""

    def __init__(self, trace_service_factory: Optional[Callable[[Any], Any]] = None):
        self.trace_service_factory = trace_service_factory or get_run_trace_service

    def record_learning_event(
        self,
        *,
        db: Any,
        conversation_id: Optional[int],
        learning_id: str,
        event_type: str,
        summary: str,
        detail: str = "",
        severity: str = "info",
        payload: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        return self._record_event(
            db=db,
            conversation_id=conversation_id,
            source="learning",
            entity_id_key="learning_id",
            entity_id=learning_id,
            event_type=event_type,
            summary=summary,
            detail=detail,
            severity=severity,
            payload=payload,
        )

    def record_error_event(
        self,
        *,
        db: Any,
        conversation_id: Optional[int],
        error_id: str,
        event_type: str,
        summary: str,
        detail: str = "",
        severity: str = "error",
        payload: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        return self._record_event(
            db=db,
            conversation_id=conversation_id,
            source="error",
            entity_id_key="error_id",
            entity_id=error_id,
            event_type=event_type,
            summary=summary,
            detail=detail,
            severity=severity,
            payload=payload,
        )

    def record_feature_request_event(
        self,
        *,
        db: Any,
        conversation_id: Optional[int],
        feature_id: str,
        event_type: str,
        summary: str,
        detail: str = "",
        severity: str = "info",
        payload: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        return self._record_event(
            db=db,
            conversation_id=conversation_id,
            source="feature_request",
            entity_id_key="feature_id",
            entity_id=feature_id,
            event_type=event_type,
            summary=summary,
            detail=detail,
            severity=severity,
            payload=payload,
        )

    def _record_event(
        self,
        *,
        db: Any,
        conversation_id: Optional[int],
        source: str,
        entity_id_key: str,
        entity_id: str,
        event_type: str,
        summary: str,
        detail: str,
        severity: str,
        payload: Optional[dict[str, Any]],
    ) -> dict[str, Any]:
        trace_service = self.trace_service_factory(db)
        snapshot_ref = trace_service.build_snapshot_ref(
            source=source,
            event_type=event_type,
            conversation_id=conversation_id,
        )
        dedupe_key = str((payload or {}).get("dedupe_key") or "").strip()
        if not dedupe_key:
            dedupe_key = self._build_dedupe_key(
                source=source,
                event_type=event_type,
                conversation_id=conversation_id,
                entity_id=entity_id,
            )
        final_payload = {
            **(payload or {}),
            entity_id_key: entity_id,
            "conversation_id": conversation_id,
            "snapshot_ref": snapshot_ref,
            "dedupe_key": dedupe_key,
        }
        trace_written = False
        audit_written = False
        if conversation_id is not None:
            if self._has_existing_dedupe_key(
                trace_service=trace_service,
                conversation_id=conversation_id,
                source=source,
                event_type=event_type,
                dedupe_key=dedupe_key,
            ):
                return {
                    "trace_written": False,
                    "audit_written": False,
                    "conversation_id": conversation_id,
                    "snapshot_ref": snapshot_ref,
                    "dedupe_key": dedupe_key,
                    "dedupe_source": "persisted_trace",
                }
            trace_written = trace_service.append_latest_active_item_trace(
                user_id=None,
                conversation_id=conversation_id,
                source=source,
                event_type=event_type,
                summary=summary,
                detail=detail,
                severity=severity,
                payload=final_payload,
            )
            audit_written = trace_service.append_latest_active_item_audit(
                user_id=None,
                conversation_id=conversation_id,
                event_type=event_type,
                content=summary,
                payload=final_payload,
            )
        return {
            "trace_written": trace_written,
            "audit_written": audit_written,
            "conversation_id": conversation_id,
            "snapshot_ref": snapshot_ref,
            "dedupe_key": dedupe_key,
        }

    def _build_dedupe_key(
        self,
        *,
        source: str,
        event_type: str,
        conversation_id: Optional[int],
        entity_id: str,
    ) -> str:
        conversation_key = conversation_id if conversation_id is not None else "NA"
        return f"{source}:{event_type}:{conversation_key}:{entity_id}"

    def _has_existing_dedupe_key(
        self,
        *,
        trace_service: Any,
        conversation_id: int,
        source: str,
        event_type: str,
        dedupe_key: str,
    ) -> bool:
        has_dedupe_key = getattr(trace_service, "has_runtime_trace_dedupe_key", None)
        if not callable(has_dedupe_key):
            return False
        return bool(has_dedupe_key(
            user_id=None,
            conversation_id=conversation_id,
            source=source,
            event_type=event_type,
            dedupe_key=dedupe_key,
        ))


_self_improvement_timeline_service: SelfImprovementTimelineService | None = None


def get_self_improvement_timeline_service() -> SelfImprovementTimelineService:
    global _self_improvement_timeline_service
    if _self_improvement_timeline_service is None:
        _self_improvement_timeline_service = SelfImprovementTimelineService()
    return _self_improvement_timeline_service
