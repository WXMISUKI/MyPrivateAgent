"""Timeline adapter for query control plane lifecycle events."""

from __future__ import annotations

from typing import Any, Callable, Optional

try:
    from services.query_control_plane_service import QueryControlPlaneService
    from services.run_trace_service import get_run_trace_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.query_control_plane_service import QueryControlPlaneService
    from backend.services.run_trace_service import get_run_trace_service


class QueryControlTimelineService:
    """Record canonical query lifecycle stages into trace and audit streams."""

    SOURCE = "query_control"

    def __init__(
        self,
        trace_service_factory: Optional[Callable[[Any], Any]] = None,
        control_plane_service: Optional[QueryControlPlaneService] = None,
    ):
        self.trace_service_factory = trace_service_factory or get_run_trace_service
        self.control_plane_service = control_plane_service or QueryControlPlaneService()

    def record_stage(
        self,
        *,
        db: Any,
        conversation_id: Optional[int],
        channel: str,
        stage: str,
        query_id: str,
        summary: str,
        detail: str = "",
        severity: str = "info",
        payload: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        self._validate_stage(stage)
        self._validate_channel(channel)
        event_type = f"query_control_{stage}"
        trace_service = self.trace_service_factory(db)
        snapshot_ref = trace_service.build_snapshot_ref(
            source=self.SOURCE,
            event_type=event_type,
            conversation_id=conversation_id,
        )
        dedupe_key = str((payload or {}).get("dedupe_key") or "").strip()
        if not dedupe_key:
            dedupe_key = self._build_dedupe_key(
                channel=channel,
                stage=stage,
                conversation_id=conversation_id,
                query_id=query_id,
            )
        final_payload = {
            **(payload or {}),
            "channel": channel,
            "stage": stage,
            "query_id": query_id,
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
                source=self.SOURCE,
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

    def _validate_stage(self, stage: str) -> None:
        if stage not in self.control_plane_service.build_runtime_contract()["lifecycle_stages"]:
            raise ValueError(f"Unknown query lifecycle stage: {stage}")

    def _validate_channel(self, channel: str) -> None:
        if channel not in self.control_plane_service.build_runtime_contract()["execution_channels"]:
            raise ValueError(f"Unknown query execution channel: {channel}")

    def _build_dedupe_key(
        self,
        *,
        channel: str,
        stage: str,
        conversation_id: Optional[int],
        query_id: str,
    ) -> str:
        conversation_key = conversation_id if conversation_id is not None else "NA"
        return f"{self.SOURCE}:{channel}:{stage}:{conversation_key}:{query_id}"

    def _has_existing_dedupe_key(
        self,
        *,
        trace_service: Any,
        conversation_id: int,
        event_type: str,
        dedupe_key: str,
    ) -> bool:
        has_dedupe_key = getattr(trace_service, "has_runtime_trace_dedupe_key", None)
        if not callable(has_dedupe_key):
            return False
        return bool(has_dedupe_key(
            user_id=None,
            conversation_id=conversation_id,
            source=self.SOURCE,
            event_type=event_type,
            dedupe_key=dedupe_key,
        ))


_query_control_timeline_service: QueryControlTimelineService | None = None


def get_query_control_timeline_service() -> QueryControlTimelineService:
    global _query_control_timeline_service
    if _query_control_timeline_service is None:
        _query_control_timeline_service = QueryControlTimelineService()
    return _query_control_timeline_service
