"""Shared diagnostics collectors for framework adapter governance surfaces."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

try:
    from database import SessionLocal
    from models import PlanItemRecord
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.database import SessionLocal
    from backend.models import PlanItemRecord


class FrameworkAdapterDiagnosticsService:
    """Collect framework adapter runtime diagnostics behind one stable seam."""

    def __init__(self, *, session_factory: Callable[[], Any] = SessionLocal):
        self.session_factory = session_factory

    def collect_latest_external_error_summary(
        self,
        *,
        db: Any = None,
        limit: int = 50,
    ) -> Optional[Dict[str, Any]]:
        database, should_close = self._resolve_db(db)
        if database is None:
            return None
        try:
            scheduler_service = self._build_scheduler_service(database)
            latest_event = None
            latest_timestamp = None
            for item in self._recent_plan_items(database, limit=limit):
                events = scheduler_service.filter_run_trace(
                    item,
                    source="framework_adapter",
                    event_type="framework_adapter_external_error",
                    limit=1,
                )
                if not events:
                    continue
                event = dict(events[-1] or {})
                event_timestamp = self._parse_iso_datetime(str(event.get("timestamp") or ""))
                event_timestamp = event_timestamp or datetime.min.replace(tzinfo=timezone.utc)
                if latest_timestamp is None or event_timestamp > latest_timestamp:
                    latest_timestamp = event_timestamp
                    latest_event = event

            if latest_event is None:
                return None

            payload = dict(latest_event.get("payload") or {})
            snapshot_ref = dict(payload.get("snapshot_ref") or {})
            return {
                "timestamp": latest_event.get("timestamp"),
                "event_type": latest_event.get("event_type"),
                "severity": latest_event.get("severity"),
                "summary": latest_event.get("summary"),
                "detail": latest_event.get("detail") or payload.get("error_detail"),
                "error_type": payload.get("error_type"),
                "adapter_id": payload.get("adapter_id"),
                "framework_name": payload.get("framework_name"),
                "run_id": latest_event.get("run_id") or payload.get("run_id"),
                "snapshot_ref": snapshot_ref or None,
            }
        finally:
            if should_close:
                database.close()

    def collect_external_error_counts(
        self,
        *,
        db: Any = None,
        limit: int = 50,
    ) -> Optional[Dict[str, Any]]:
        database, should_close = self._resolve_db(db)
        if database is None:
            return None
        sample_size = max(1, int(limit))
        try:
            scheduler_service = self._build_scheduler_service(database)
            total = 0
            by_error_type: Dict[str, int] = {}
            for item in self._recent_plan_items(database, limit=sample_size):
                events = scheduler_service.filter_run_trace(
                    item,
                    source="framework_adapter",
                    event_type="framework_adapter_external_error",
                    limit=sample_size,
                )
                for raw_event in events or []:
                    event = dict(raw_event or {})
                    payload = dict(event.get("payload") or {})
                    error_type = str(payload.get("error_type") or "").strip() or "unknown"
                    total += 1
                    by_error_type[error_type] = int(by_error_type.get(error_type) or 0) + 1

            if total <= 0:
                return None
            return {
                "total": total,
                "window_scope": "recent_plan_items",
                "sample_size": sample_size,
                "by_error_type": by_error_type,
            }
        finally:
            if should_close:
                database.close()

    def _resolve_db(self, db: Any = None) -> tuple[Any, bool]:
        if db is not None:
            return db, False
        return self.session_factory(), True

    def _recent_plan_items(self, db: Any, *, limit: int) -> list[Any]:
        return (
            db.query(PlanItemRecord)
            .order_by(PlanItemRecord.updated_at.desc(), PlanItemRecord.id.desc())
            .limit(max(1, int(limit)))
            .all()
        )

    @staticmethod
    def _build_scheduler_service(db: Any) -> Any:
        try:
            from services.scheduler_service import SchedulerService
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.services.scheduler_service import SchedulerService

        return SchedulerService(db)

    @staticmethod
    def _parse_iso_datetime(value: str | None) -> datetime | None:
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


_framework_adapter_diagnostics_service: FrameworkAdapterDiagnosticsService | None = None


def get_framework_adapter_diagnostics_service() -> FrameworkAdapterDiagnosticsService:
    global _framework_adapter_diagnostics_service
    if _framework_adapter_diagnostics_service is None:
        _framework_adapter_diagnostics_service = FrameworkAdapterDiagnosticsService()
    return _framework_adapter_diagnostics_service
