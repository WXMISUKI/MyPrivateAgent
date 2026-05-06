"""Diagnostics and reconciliation for scheduler runtime persistence backends."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import inspect

try:
    from config import DB_MODE, SCHEDULER_RUNTIME_BACKEND
    from models import BackgroundRunRecord, ChildRunRecord, PlanItemRecord, SchedulerRunRecord, WorktreeRunRecord
    from services.scheduler_runtime_repository import get_scheduler_runtime_repository
    from services.scheduler_runtime_sql_repository import get_scheduler_runtime_sql_repository
    from services.scheduler_runtime_store import SchedulerRuntimeStore
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.config import DB_MODE, SCHEDULER_RUNTIME_BACKEND
    from backend.models import BackgroundRunRecord, ChildRunRecord, PlanItemRecord, SchedulerRunRecord, WorktreeRunRecord
    from backend.services.scheduler_runtime_repository import get_scheduler_runtime_repository
    from backend.services.scheduler_runtime_sql_repository import get_scheduler_runtime_sql_repository
    from backend.services.scheduler_runtime_store import SchedulerRuntimeStore


class SchedulerRuntimeDiagnosticsService:
    """Collect runtime backend diagnostics and perform relational reconciliation."""

    def __init__(self, db):
        self.db = db

    def collect_status(self, *, limit: int = 50) -> dict:
        store = SchedulerRuntimeStore(db=self.db)
        descriptor = store.get_persistence_descriptor()
        table_status = self._collect_table_status()
        record_counts = self._collect_record_counts(table_status)
        metadata_summary = self._collect_metadata_runtime_summary(limit=limit)
        return {
            "status": "ok",
            "database_mode": DB_MODE,
            "requested_backend": str(SCHEDULER_RUNTIME_BACKEND or "metadata").strip().lower() or "metadata",
            "effective_backend": descriptor.get("effective_backend"),
            "backend": descriptor.get("backend"),
            "backend_source": descriptor.get("backend_source"),
            "table_ready": bool(descriptor.get("table_ready")),
            "fallback_reason": descriptor.get("fallback_reason"),
            "persistence": descriptor,
            "table_status": table_status,
            "record_counts": record_counts,
            "metadata_runtime_summary": metadata_summary,
            "runtime_attachment_summary": self._collect_runtime_attachment_summary(limit=limit),
        }

    def reconcile_to_relational(
        self,
        *,
        plan_id: Optional[int] = None,
        item_id: Optional[int] = None,
        limit: int = 100,
    ) -> dict:
        relational_repository = get_scheduler_runtime_sql_repository(self.db)
        table_ready = relational_repository.is_available()
        if not table_ready:
            return {
                "status": "skipped",
                "table_ready": False,
                "reason": "scheduler_runtime_tables_missing",
                "reconciled_items": 0,
                "skipped_items": 0,
                "items": [],
            }

        query = self.db.query(PlanItemRecord).order_by(PlanItemRecord.updated_at.desc(), PlanItemRecord.id.desc())
        if plan_id is not None:
            query = query.filter(PlanItemRecord.plan_id == plan_id)
        if item_id is not None:
            query = query.filter(PlanItemRecord.id == item_id)

        items = query.limit(max(1, int(limit))).all()
        reconciled_items = 0
        skipped_items = 0
        result_items = []
        metadata_repository = get_scheduler_runtime_repository()
        for item in items:
            metadata_group = metadata_repository.get_child_group(item)
            if not metadata_group or not str(metadata_group.get("run_id") or "").strip():
                skipped_items += 1
                result_items.append({
                    "plan_id": item.plan_id,
                    "item_id": item.id,
                    "status": "skipped",
                    "reason": "no_runtime_metadata",
                })
                continue
            saved_group = relational_repository.save_child_group(item, metadata_group)
            reconciled_items += 1
            result_items.append({
                "plan_id": item.plan_id,
                "item_id": item.id,
                "status": "reconciled",
                "scheduler_run_id": (saved_group or {}).get("run_id"),
                "child_count": len((saved_group or {}).get("children") or []),
            })

        return {
            "status": "ok",
            "table_ready": True,
            "requested_backend": str(SCHEDULER_RUNTIME_BACKEND or "metadata").strip().lower() or "metadata",
            "reconciled_items": reconciled_items,
            "skipped_items": skipped_items,
            "items": result_items,
        }

    def _collect_table_status(self) -> dict:
        bind = getattr(self.db, "bind", None)
        if bind is None:
            return {
                "database_bound": False,
                "scheduler_runs": False,
                "child_runs": False,
                "background_runs": False,
                "worktree_runs": False,
            }
        inspector = inspect(bind)
        table_names = set(inspector.get_table_names())
        return {
            "database_bound": True,
            "scheduler_runs": "scheduler_runs" in table_names,
            "child_runs": "child_runs" in table_names,
            "background_runs": "background_runs" in table_names,
            "worktree_runs": "worktree_runs" in table_names,
        }

    def _collect_record_counts(self, table_status: dict) -> dict:
        if not table_status.get("database_bound"):
            return {"scheduler_runs": 0, "child_runs": 0, "background_runs": 0, "worktree_runs": 0}
        if not table_status.get("scheduler_runs") or not table_status.get("child_runs"):
            return {"scheduler_runs": 0, "child_runs": 0, "background_runs": 0, "worktree_runs": 0}
        background_runs = int(self.db.query(BackgroundRunRecord).count()) if table_status.get("background_runs") else 0
        worktree_runs = int(self.db.query(WorktreeRunRecord).count()) if table_status.get("worktree_runs") else 0
        return {
            "scheduler_runs": int(self.db.query(SchedulerRunRecord).count()),
            "child_runs": int(self.db.query(ChildRunRecord).count()),
            "background_runs": background_runs,
            "worktree_runs": worktree_runs,
        }

    def _collect_metadata_runtime_summary(self, *, limit: int) -> dict:
        items = (
            self.db.query(PlanItemRecord)
            .order_by(PlanItemRecord.updated_at.desc(), PlanItemRecord.id.desc())
            .limit(max(1, int(limit)))
            .all()
        )
        runtime_items = []
        for item in items:
            metadata = dict(item.item_metadata or {})
            group = metadata.get("child_execution_group") or {}
            run_id = str(group.get("run_id") or "").strip()
            if not run_id:
                continue
            runtime_items.append({
                "plan_id": item.plan_id,
                "item_id": item.id,
                "scheduler_run_id": run_id,
                "child_count": len(group.get("children") or []),
            })
        return {
            "scan_limit": max(1, int(limit)),
            "runtime_item_count": len(runtime_items),
            "items": runtime_items,
        }

    def _collect_runtime_attachment_summary(self, *, limit: int) -> dict:
        items = (
            self.db.query(PlanItemRecord)
            .order_by(PlanItemRecord.updated_at.desc(), PlanItemRecord.id.desc())
            .limit(max(1, int(limit)))
            .all()
        )
        store = SchedulerRuntimeStore(db=self.db)
        item_summaries = []
        approval_request_count = 0
        pending_approval_count = 0
        background_run_count = 0
        worktree_run_count = 0

        for item in items:
            runtime_state = store.load_runtime_state(item)
            item_approval_count = len(runtime_state.approval_requests)
            item_pending_approval_count = len(
                [
                    request
                    for request in runtime_state.approval_requests
                    if str(request.status or "").strip().lower() == "pending"
                ]
            )
            item_background_run_count = len(runtime_state.background_runs)
            item_worktree_run_count = len(runtime_state.worktree_runs)
            if (
                not runtime_state.scheduler_run.run_id
                and item_approval_count == 0
                and item_background_run_count == 0
                and item_worktree_run_count == 0
            ):
                continue
            approval_request_count += item_approval_count
            pending_approval_count += item_pending_approval_count
            background_run_count += item_background_run_count
            worktree_run_count += item_worktree_run_count
            item_summaries.append({
                "plan_id": item.plan_id,
                "item_id": item.id,
                "scheduler_run_id": runtime_state.scheduler_run.run_id,
                "approval_request_count": item_approval_count,
                "pending_approval_count": item_pending_approval_count,
                "background_run_count": item_background_run_count,
                "worktree_run_count": item_worktree_run_count,
            })

        return {
            "scan_limit": max(1, int(limit)),
            "runtime_item_count": len(item_summaries),
            "approval_request_count": approval_request_count,
            "pending_approval_count": pending_approval_count,
            "background_run_count": background_run_count,
            "worktree_run_count": worktree_run_count,
            "items": item_summaries,
        }


def get_scheduler_runtime_diagnostics_service(db) -> SchedulerRuntimeDiagnosticsService:
    return SchedulerRuntimeDiagnosticsService(db)
