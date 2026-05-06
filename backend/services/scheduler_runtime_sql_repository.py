"""Relational scheduler runtime repository backed by dedicated tables."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import inspect

try:
    from models import ChildRunRecord, PlanItemRecord, SchedulerRunRecord
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.models import ChildRunRecord, PlanItemRecord, SchedulerRunRecord

try:
    from services.scheduler_runtime_repository import SchedulerRuntimeMetadataRepository
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.scheduler_runtime_repository import SchedulerRuntimeMetadataRepository


class SchedulerRuntimeSqlRepository:
    """Persist scheduler and child run state in dedicated relational tables."""

    def __init__(self, db):
        self.db = db
        self.metadata_repository = SchedulerRuntimeMetadataRepository()

    def get_persistence_descriptor(self) -> dict:
        return {
            "backend": "relational_tables",
            "scope": "scheduler_runs+child_runs",
            "durable": True,
            "migration_ready": True,
        }

    def is_available(self) -> bool:
        bind = getattr(self.db, "bind", None)
        if bind is None:
            return False
        inspector = inspect(bind)
        table_names = set(inspector.get_table_names())
        return {"scheduler_runs", "child_runs"}.issubset(table_names)

    def get_metadata(self, item: Optional[PlanItemRecord]) -> dict:
        return self.metadata_repository.get_metadata(item)

    def get_required_capabilities(self, item: Optional[PlanItemRecord]) -> list[str]:
        return self.metadata_repository.get_required_capabilities(item)

    def get_child_roles(self, item: Optional[PlanItemRecord]) -> list[str]:
        return self.metadata_repository.get_child_roles(item)

    def save_child_roles(self, item: Optional[PlanItemRecord], roles: list[str]) -> list[str]:
        return self.metadata_repository.save_child_roles(item, roles)

    def get_child_group(self, item: Optional[PlanItemRecord]) -> Optional[dict]:
        if item is None or self.db is None:
            return None
        scheduler_run = self._get_scheduler_run_record(item)
        if scheduler_run is None:
            metadata_group = self.metadata_repository.get_child_group(item)
            if metadata_group:
                self.save_child_group(item, metadata_group)
                scheduler_run = self._get_scheduler_run_record(item)
            if scheduler_run is None:
                return None
        children = (
            self.db.query(ChildRunRecord)
            .filter(ChildRunRecord.plan_item_id == item.id, ChildRunRecord.scheduler_run_id == scheduler_run.scheduler_run_id)
            .order_by(ChildRunRecord.created_at.asc(), ChildRunRecord.id.asc())
            .all()
        )
        return {
            "run_id": scheduler_run.scheduler_run_id,
            "merge_strategy": scheduler_run.merge_strategy,
            "merge_status": scheduler_run.merge_status,
            "merged_output": scheduler_run.merged_output or "",
            "policy": dict(scheduler_run.policy or {}),
            "children": [self._serialize_child_record(child) for child in children],
            "last_merge_at": self._serialize_datetime(scheduler_run.last_merge_at),
        }

    def save_child_group(self, item: Optional[PlanItemRecord], group: Optional[dict]) -> Optional[dict]:
        if item is None or self.db is None:
            return None
        if group is None:
            scheduler_run = self._get_scheduler_run_record(item)
            if scheduler_run is not None:
                self.db.query(ChildRunRecord).filter(ChildRunRecord.plan_item_id == item.id).delete()
                self.db.delete(scheduler_run)
                self.db.flush()
            self.metadata_repository.save_child_group(item, None)
            return None

        scheduler_run_id = str(group.get("run_id") or "").strip()
        if not scheduler_run_id:
            return None
        scheduler_run = self._get_scheduler_run_record(item)
        if scheduler_run is None:
            scheduler_run = SchedulerRunRecord(
                scheduler_run_id=scheduler_run_id,
                plan_id=item.plan_id,
                plan_item_id=item.id,
            )
            self.db.add(scheduler_run)
        scheduler_run.scheduler_run_id = scheduler_run_id
        scheduler_run.plan_id = item.plan_id
        scheduler_run.plan_item_id = item.id
        scheduler_run.parent_run_id = self._normalize_text(group.get("parent_run_id"))
        scheduler_run.run_kind = self._normalize_text(group.get("run_kind")) or "scheduler"
        scheduler_run.state = self._normalize_text(group.get("state"))
        scheduler_run.merge_strategy = self._normalize_text(group.get("merge_strategy"))
        scheduler_run.merge_status = self._normalize_text(group.get("merge_status"))
        scheduler_run.merged_output = self._normalize_text(group.get("merged_output"))
        scheduler_run.policy = dict(group.get("policy") or {})
        scheduler_run.last_merge_at = self._parse_datetime(group.get("last_merge_at"))
        scheduler_run.runtime_metadata = {"source": "scheduler_runtime_sql_repository"}
        self.db.flush()

        incoming_ids = set()
        for child in group.get("children") or []:
            if not isinstance(child, dict):
                continue
            child_execution_id = self._normalize_text(child.get("child_execution_id"))
            if not child_execution_id:
                continue
            incoming_ids.add(child_execution_id)
            record = (
                self.db.query(ChildRunRecord)
                .filter(
                    ChildRunRecord.plan_item_id == item.id,
                    ChildRunRecord.child_execution_id == child_execution_id,
                )
                .first()
            )
            if record is None:
                record = ChildRunRecord(
                    child_run_id=self._normalize_text(child.get("child_run_id")) or child_execution_id,
                    child_execution_id=child_execution_id,
                    plan_id=item.plan_id,
                    plan_item_id=item.id,
                    run_id=self._normalize_text(child.get("run_id")) or child_execution_id,
                )
                self.db.add(record)
            record.child_run_id = self._normalize_text(child.get("child_run_id")) or child_execution_id
            record.child_execution_id = child_execution_id
            record.scheduler_run_ref_id = scheduler_run.id
            record.scheduler_run_id = scheduler_run.scheduler_run_id
            record.plan_id = item.plan_id
            record.plan_item_id = item.id
            record.parent_run_id = self._normalize_text(child.get("parent_run_id")) or scheduler_run.scheduler_run_id
            record.run_id = self._normalize_text(child.get("run_id")) or record.child_run_id
            record.run_kind = self._normalize_text(child.get("run_kind")) or "child"
            record.agent_role = self._normalize_text(child.get("agent_role"))
            record.agent_id = self._normalize_text(child.get("agent_id"))
            record.status = self._normalize_text(child.get("status")) or "queued"
            record.title = self._normalize_text(child.get("title"))
            record.summary = self._normalize_text(child.get("summary"))
            record.error = self._normalize_text(child.get("error"))
            record.error_kind = self._normalize_text(child.get("error_kind"))
            record.retry_count = max(0, int(child.get("retry_count") or 0))
            record.model_name = self._normalize_text(child.get("model_name"))
            record.provider_name = self._normalize_text(child.get("provider_name"))
            record.provider_order = list(child.get("provider_order") or [])
            record.provider_switch_count = max(0, int(child.get("provider_switch_count") or 0))
            record.provider_history = list(child.get("provider_history") or [])
            record.started_at = self._parse_datetime(child.get("started_at"))
            record.completed_at = self._parse_datetime(child.get("completed_at"))
            record.cancelled_at = self._parse_datetime(child.get("cancelled_at"))
            record.child_metadata = {
                "created_at": child.get("created_at"),
                "updated_at": child.get("updated_at"),
                "last_retry_error": self._normalize_text(child.get("last_retry_error")),
            }
        stale_query = self.db.query(ChildRunRecord).filter(
            ChildRunRecord.plan_item_id == item.id,
            ChildRunRecord.scheduler_run_id == scheduler_run.scheduler_run_id,
        )
        if incoming_ids:
            stale_query = stale_query.filter(ChildRunRecord.child_execution_id.notin_(incoming_ids))
        stale_children = stale_query.all()
        for stale in stale_children:
            self.db.delete(stale)
        self.db.flush()
        self.metadata_repository.save_child_group(item, group)
        return self.get_child_group(item)

    def list_children(self, item: Optional[PlanItemRecord]) -> list[dict]:
        group = self.get_child_group(item) or {}
        return [dict(child) for child in (group.get("children") or []) if isinstance(child, dict)]

    def find_child_group_entry(
        self,
        item: Optional[PlanItemRecord],
        child_execution_id: str,
    ) -> tuple[Optional[dict], Optional[dict]]:
        group = self.get_child_group(item)
        if group is None:
            return None, None
        normalized_child_execution_id = self._normalize_text(child_execution_id)
        if not normalized_child_execution_id:
            return group, None
        for child in group.get("children") or []:
            if self._normalize_text(child.get("child_execution_id")) == normalized_child_execution_id:
                return group, dict(child)
        return group, None

    def get_audit_trail(self, item: Optional[PlanItemRecord]) -> list[dict]:
        return self.metadata_repository.get_audit_trail(item)

    def append_audit_trail(self, item: Optional[PlanItemRecord], entry: dict, *, limit: int = 50) -> list[dict]:
        return self.metadata_repository.append_audit_trail(item, entry, limit=limit)

    def get_run_trace(self, item: Optional[PlanItemRecord]) -> list[dict]:
        return self.metadata_repository.get_run_trace(item)

    def append_run_trace(self, item: Optional[PlanItemRecord], entry: dict, *, limit: int = 100) -> list[dict]:
        return self.metadata_repository.append_run_trace(item, entry, limit=limit)

    def _get_scheduler_run_record(self, item: PlanItemRecord) -> Optional[SchedulerRunRecord]:
        return (
            self.db.query(SchedulerRunRecord)
            .filter(SchedulerRunRecord.plan_item_id == item.id)
            .order_by(SchedulerRunRecord.updated_at.desc(), SchedulerRunRecord.id.desc())
            .first()
        )

    def _serialize_child_record(self, record: ChildRunRecord) -> dict:
        metadata = dict(record.child_metadata or {})
        return {
            "child_execution_id": record.child_execution_id,
            "child_run_id": record.child_run_id,
            "parent_run_id": record.parent_run_id,
            "run_id": record.run_id,
            "run_kind": record.run_kind,
            "agent_role": record.agent_role,
            "agent_id": record.agent_id,
            "status": record.status,
            "title": record.title or "",
            "scheduler_run_id": record.scheduler_run_id,
            "summary": record.summary or "",
            "error": record.error or "",
            "error_kind": record.error_kind or "",
            "retry_count": int(record.retry_count or 0),
            "model_name": record.model_name or "",
            "provider_name": record.provider_name or "",
            "provider_order": list(record.provider_order or []),
            "provider_switch_count": int(record.provider_switch_count or 0),
            "provider_history": list(record.provider_history or []),
            "created_at": metadata.get("created_at") or self._serialize_datetime(record.created_at),
            "updated_at": metadata.get("updated_at") or self._serialize_datetime(record.updated_at),
            "started_at": self._serialize_datetime(record.started_at) or "",
            "completed_at": self._serialize_datetime(record.completed_at) or "",
            "cancelled_at": self._serialize_datetime(record.cancelled_at) or "",
            "last_retry_error": metadata.get("last_retry_error") or "",
        }

    def _parse_datetime(self, value: object) -> Optional[datetime]:
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
        text = self._normalize_text(value)
        if not text:
            return None
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None

    def _serialize_datetime(self, value: object) -> Optional[str]:
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z") if value.tzinfo else value.isoformat(timespec="seconds")
        return None

    def _normalize_text(self, value: object) -> Optional[str]:
        text = str(value or "").strip()
        return text or None


def get_scheduler_runtime_sql_repository(db) -> SchedulerRuntimeSqlRepository:
    return SchedulerRuntimeSqlRepository(db)
