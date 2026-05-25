"""Runtime store abstraction for scheduler and child run state."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import or_
from sqlalchemy import inspect

try:
    from config import SCHEDULER_RUNTIME_BACKEND
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.config import SCHEDULER_RUNTIME_BACKEND

try:
    from models import (
        ArtifactRecord,
        BackgroundRunRecord,
        PermissionRequestRecord,
        PlanItemRecord,
        PlanRunRecord,
        WorktreeRunRecord,
    )
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.models import (
        ArtifactRecord,
        BackgroundRunRecord,
        PermissionRequestRecord,
        PlanItemRecord,
        PlanRunRecord,
        WorktreeRunRecord,
    )

try:
    from services.scheduler_runtime_repository import get_scheduler_runtime_repository
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.scheduler_runtime_repository import get_scheduler_runtime_repository

try:
    from services.scheduler_runtime_sql_repository import get_scheduler_runtime_sql_repository
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.scheduler_runtime_sql_repository import get_scheduler_runtime_sql_repository

try:
    from services.scheduler_runtime_contract import SchedulerRuntimeRepository
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.scheduler_runtime_contract import SchedulerRuntimeRepository

try:
    from services.scheduler_runtime_entities import (
        ApprovalRequestState,
        BackgroundRunState,
        ChildRunState,
        SchedulerRunState,
        SchedulerRuntimePersistenceDescriptor,
        SchedulerRuntimeState,
        WorktreeRunState,
    )
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.scheduler_runtime_entities import (
        ApprovalRequestState,
        BackgroundRunState,
        ChildRunState,
        SchedulerRunState,
        SchedulerRuntimePersistenceDescriptor,
        SchedulerRuntimeState,
        WorktreeRunState,
    )


class SchedulerRuntimeStore:
    """Formal runtime state boundary for scheduler / child run operations."""

    def __init__(self, db=None, repository: Optional[SchedulerRuntimeRepository] = None):
        self.db = db
        self._available_tables = self._discover_available_tables()
        self.requested_backend = str(SCHEDULER_RUNTIME_BACKEND or "metadata").strip().lower() or "metadata"
        self.metadata_repository = get_scheduler_runtime_repository()
        self.selection = {
            "requested_backend": self.requested_backend,
            "effective_backend": "metadata",
            "backend_source": "metadata",
            "table_ready": False,
            "fallback_reason": None,
        }
        if repository is not None:
            self.repository = repository
            self._refresh_selection_from_repository()
        else:
            self.repository = self._resolve_repository(db)

    def get_required_capabilities(self, item: Optional[PlanItemRecord]) -> list[str]:
        return self._call_repository("get_required_capabilities", item)

    def get_metadata(self, item: Optional[PlanItemRecord]) -> dict:
        return self._call_repository("get_metadata", item)

    def get_child_roles(self, item: Optional[PlanItemRecord]) -> list[str]:
        return self._call_repository("get_child_roles", item)

    def save_child_roles(self, item: Optional[PlanItemRecord], roles: list[str]) -> list[str]:
        return self._call_repository("save_child_roles", item, roles)

    def load_runtime_state(self, item: Optional[PlanItemRecord]) -> SchedulerRuntimeState:
        group = self._call_repository("get_child_group", item) or {}
        scheduler_run_id = str(group.get("run_id") or "").strip() or None
        policy = dict(group.get("policy") or {})
        merge_strategy = str(group.get("merge_strategy") or "").strip() or None
        merge_status = str(group.get("merge_status") or "").strip() or None
        merged_output = str(group.get("merged_output") or "").strip() or None
        child_runs = [self._serialize_child_run(child, scheduler_run_id) for child in self.repository.list_children(item)]
        child_status_counts = self._count_child_statuses(child_runs)
        approval_requests = self._load_approval_requests(item)
        background_runs = self._load_background_runs(item)
        worktree_runs = self._load_worktree_runs(item)
        active_children = child_status_counts.get("queued", 0) + child_status_counts.get("running", 0)
        if active_children > 0:
            scheduler_state = "running"
        elif merge_status == "completed":
            scheduler_state = "completed"
        elif merge_status in {"partial_failed", "failed"}:
            scheduler_state = "failed"
        elif merge_status == "incomplete":
            scheduler_state = "incomplete"
        else:
            scheduler_state = "pending" if scheduler_run_id else None
        return SchedulerRuntimeState(
            scheduler_run=SchedulerRunState(
                run_id=scheduler_run_id,
                parent_run_id=None,
                run_kind="scheduler" if scheduler_run_id else None,
                state=scheduler_state,
                merge_strategy=merge_strategy,
                merge_status=merge_status,
                policy=policy,
                last_merge_at=group.get("last_merge_at"),
                merged_output=merged_output,
                child_count=len(child_runs),
                active_children=active_children,
                child_status_counts=child_status_counts,
            ),
            child_runs=child_runs,
            approval_requests=approval_requests,
            background_runs=background_runs,
            worktree_runs=worktree_runs,
            persistence=SchedulerRuntimePersistenceDescriptor(**self.get_persistence_descriptor()),
        )

    def load_runtime(self, item: Optional[PlanItemRecord]) -> dict:
        return self.load_runtime_state(item).to_dict()

    def get_child_group(self, item: Optional[PlanItemRecord]) -> Optional[dict]:
        return self._call_repository("get_child_group", item)

    def get_persistence_descriptor(self) -> dict:
        descriptor = self.repository.get_persistence_descriptor()
        merged = dict(descriptor or {})
        merged.update(dict(self.selection or {}))
        merged["backend"] = (
            "relational_tables"
            if merged.get("effective_backend") == "relational"
            else "metadata_adapter"
        )
        return merged

    def save_runtime(
        self,
        item: Optional[PlanItemRecord],
        *,
        scheduler_run: Optional[dict],
        child_runs: Optional[list[dict]] = None,
    ) -> Optional[dict]:
        if item is None:
            return None
        runtime = self.load_runtime_state(item)
        scheduler_data = runtime.scheduler_run.to_dict()
        scheduler_data.update(dict(scheduler_run or {}))
        children = list(child_runs if child_runs is not None else [child.to_dict() for child in runtime.child_runs])
        group = {
            "run_id": scheduler_data.get("run_id"),
            "merge_strategy": scheduler_data.get("merge_strategy"),
            "merge_status": scheduler_data.get("merge_status"),
            "merged_output": scheduler_data.get("merged_output") or "",
            "policy": dict(scheduler_data.get("policy") or {}),
            "children": [self._serialize_child_group_entry(child, scheduler_data.get("run_id")) for child in children],
            "last_merge_at": scheduler_data.get("last_merge_at"),
        }
        return self._call_repository("save_child_group", item, group)

    def save_runtime_state(
        self,
        item: Optional[PlanItemRecord],
        state: SchedulerRuntimeState,
    ) -> SchedulerRuntimeState:
        self.save_runtime(
            item,
            scheduler_run=state.scheduler_run.to_dict(),
            child_runs=[child.to_dict() for child in state.child_runs],
        )
        return self.load_runtime_state(item)

    def get_child_run(
        self,
        item: Optional[PlanItemRecord],
        child_execution_id: str,
    ) -> Optional[dict]:
        _group, child = self._call_repository("find_child_group_entry", item, child_execution_id)
        if child is None:
            return None
        scheduler_run_id = str((self._call_repository("get_child_group", item) or {}).get("run_id") or "").strip() or None
        return self._serialize_child_run(child, scheduler_run_id).to_dict()

    def replace_child_run(
        self,
        item: Optional[PlanItemRecord],
        child_execution_id: str,
        child_run: dict,
    ) -> Optional[dict]:
        group, existing = self._call_repository("find_child_group_entry", item, child_execution_id)
        if group is None or existing is None:
            return None
        children = []
        normalized_target = str(child_execution_id or "").strip()
        for child in group.get("children") or []:
            if not isinstance(child, dict):
                continue
            current_id = str(child.get("child_execution_id") or "").strip()
            if current_id == normalized_target:
                children.append(self._serialize_child_group_entry(child_run, str(group.get("run_id") or "").strip() or None))
            else:
                children.append(dict(child))
        group["children"] = children
        self._call_repository("save_child_group", item, group)
        return self.get_child_run(item, child_execution_id)

    def update_child_run(
        self,
        item: Optional[PlanItemRecord],
        child_execution_id: str,
        updates: dict,
    ) -> Optional[dict]:
        child_run = self.get_child_run(item, child_execution_id)
        if child_run is None:
            return None
        child_run.update(dict(updates or {}))
        return self.replace_child_run(item, child_execution_id, child_run)

    def get_audit_trail(self, item: Optional[PlanItemRecord]) -> list[dict]:
        return self._call_repository("get_audit_trail", item)

    def list_approval_requests(self, item: Optional[PlanItemRecord]) -> list[dict]:
        return [request.to_dict() for request in self._load_approval_requests(item)]

    def list_background_runs(self, item: Optional[PlanItemRecord]) -> list[dict]:
        return [run.to_dict() for run in self._load_background_runs(item)]

    def list_worktree_runs(self, item: Optional[PlanItemRecord]) -> list[dict]:
        return [run.to_dict() for run in self._load_worktree_runs(item)]

    def record_background_run(self, item: Optional[PlanItemRecord], run: dict) -> Optional[dict]:
        state = self._persist_background_run(item, run)
        return state.to_dict() if state is not None else None

    def record_worktree_run(self, item: Optional[PlanItemRecord], run: dict) -> Optional[dict]:
        state = self._persist_worktree_run(item, run)
        return state.to_dict() if state is not None else None

    def append_audit_trail(self, item: Optional[PlanItemRecord], entry: dict, *, limit: int = 50) -> list[dict]:
        return self._call_repository("append_audit_trail", item, entry, limit=limit)

    def get_run_trace(self, item: Optional[PlanItemRecord]) -> list[dict]:
        return self._call_repository("get_run_trace", item)

    def append_run_trace(self, item: Optional[PlanItemRecord], entry: dict, *, limit: int = 100) -> list[dict]:
        return self._call_repository("append_run_trace", item, entry, limit=limit)

    def _serialize_child_run(self, child: Optional[dict], scheduler_run_id: Optional[str]) -> dict:
        data = dict(child or {})
        fallback_child_run_id = str(data.get("child_execution_id") or "").strip() or None
        child_run_id = str(data.get("child_run_id") or fallback_child_run_id or "").strip() or None
        run_id = str(data.get("run_id") or child_run_id or fallback_child_run_id or "").strip() or None
        return ChildRunState(
            child_execution_id=fallback_child_run_id,
            child_run_id=child_run_id,
            run_id=run_id,
            parent_run_id=str(data.get("parent_run_id") or scheduler_run_id or "").strip() or None,
            run_kind=str(data.get("run_kind") or "child").strip() or "child",
            scheduler_run_id=str(data.get("scheduler_run_id") or scheduler_run_id or "").strip() or None,
            agent_role=str(data.get("agent_role") or "").strip() or None,
            agent_id=str(data.get("agent_id") or "").strip() or None,
            status=str(data.get("status") or "").strip() or "queued",
            title=str(data.get("title") or "").strip() or None,
            summary=str(data.get("summary") or "").strip() or None,
            error=str(data.get("error") or "").strip() or None,
            error_kind=str(data.get("error_kind") or "").strip() or None,
            retry_count=max(0, int(data.get("retry_count") or 0)),
            model_name=str(data.get("model_name") or "").strip() or None,
            provider_name=str(data.get("provider_name") or "").strip() or None,
            provider_order=list(data.get("provider_order") or []),
            provider_switch_count=max(0, int(data.get("provider_switch_count") or 0)),
            provider_history=[dict(entry) for entry in (data.get("provider_history") or []) if isinstance(entry, dict)],
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            started_at=data.get("started_at") or None,
            completed_at=data.get("completed_at") or None,
            cancelled_at=data.get("cancelled_at") or None,
            last_retry_error=str(data.get("last_retry_error") or "").strip() or None,
            approval_event=dict(data.get("approval_event") or {}),
        )

    def _serialize_child_group_entry(self, child_run: Optional[dict], scheduler_run_id: Optional[str]) -> dict:
        child = self._serialize_child_run(child_run, scheduler_run_id).to_dict()
        return {
            "child_execution_id": child.get("child_execution_id"),
            "child_run_id": child.get("child_run_id"),
            "child_display_id": child.get("child_display_id"),
            "parent_run_id": child.get("parent_run_id"),
            "run_id": child.get("run_id"),
            "run_kind": child.get("run_kind"),
            "agent_role": child.get("agent_role"),
            "agent_id": child.get("agent_id"),
            "status": child.get("status"),
            "title": child.get("title") or "",
            "scheduler_run_id": child.get("scheduler_run_id"),
            "summary": child.get("summary") or "",
            "error": child.get("error") or "",
            "error_kind": child.get("error_kind") or "",
            "retry_count": child.get("retry_count", 0),
            "model_name": child.get("model_name") or "",
            "provider_name": child.get("provider_name") or "",
            "provider_order": list(child.get("provider_order") or []),
            "provider_switch_count": child.get("provider_switch_count", 0),
            "provider_history": list(child.get("provider_history") or []),
            "created_at": child.get("created_at"),
            "updated_at": child.get("updated_at"),
            "started_at": child.get("started_at") or "",
            "completed_at": child.get("completed_at") or "",
            "cancelled_at": child.get("cancelled_at") or "",
            "last_retry_error": child.get("last_retry_error") or "",
            "approval_event": dict(child.get("approval_event") or {}),
        }

    def _count_child_statuses(self, child_runs: list[ChildRunState]) -> dict:
        counts = {}
        for child in child_runs:
            status = str(child.status or "").strip().lower() or "unknown"
            counts[status] = counts.get(status, 0) + 1
        return counts

    def _load_approval_requests(self, item: Optional[PlanItemRecord]) -> list[ApprovalRequestState]:
        trace_events = self.get_run_trace(item)
        trace_index: dict[str, dict] = {}
        trace_order: list[str] = []
        for event in trace_events:
            if not isinstance(event, dict):
                continue
            request_id = self._extract_request_id(event)
            if not request_id:
                continue
            if request_id not in trace_index:
                trace_index[request_id] = {
                    "request_id": request_id,
                    "tool_name": None,
                    "permission_level": None,
                    "status": "pending",
                    "user_id": None,
                    "conversation_id": self._resolve_conversation_id(item),
                    "plan_id": getattr(item, "plan_id", None),
                    "plan_item_id": getattr(item, "id", None),
                    "result": None,
                    "requested_at": event.get("timestamp"),
                    "completed_at": None,
                    "run_id": event.get("run_id"),
                    "parent_run_id": event.get("parent_run_id"),
                    "child_run_id": event.get("child_run_id"),
                    "scheduler_run_id": event.get("scheduler_run_id"),
                    "run_kind": event.get("run_kind"),
                    "source_event_type": event.get("event_type"),
                    "tool_args": {},
                    "request_metadata": {},
                }
                trace_order.append(request_id)
            payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
            current = trace_index[request_id]
            current["tool_name"] = current["tool_name"] or self._normalize_optional_text(
                payload.get("tool_name") or event.get("tool_name")
            )
            current["permission_level"] = current["permission_level"] or self._normalize_optional_text(
                payload.get("permission_level")
            )
            if isinstance(payload.get("tool_args"), dict) and not current["tool_args"]:
                current["tool_args"] = dict(payload.get("tool_args") or {})
            status = self._derive_approval_status(event)
            if status:
                current["status"] = status
            if status in {"approved", "denied", "timeout"}:
                current["completed_at"] = event.get("timestamp") or current["completed_at"]
                current["result"] = self._normalize_optional_text(payload.get("result")) or current["result"]

        records: dict[str, ApprovalRequestState] = {}
        if self.db is not None and (trace_order or getattr(item, "id", None) is not None):
            try:
                query = self.db.query(PermissionRequestRecord)
                filters = []
                if trace_order:
                    filters.append(PermissionRequestRecord.request_id.in_(trace_order))
                item_id = getattr(item, "id", None)
                if item_id is not None:
                    filters.append(PermissionRequestRecord.plan_item_id == item_id)
                if filters:
                    query = query.filter(or_(*filters))
                records_in_db = query.order_by(PermissionRequestRecord.created_at.asc(), PermissionRequestRecord.id.asc()).all()
                for record in records_in_db:
                    request_id = str(record.request_id)
                    if request_id not in trace_index:
                        trace_index[request_id] = {
                            "request_id": request_id,
                            "tool_name": self._normalize_optional_text(record.tool_name),
                            "permission_level": self._normalize_optional_text(record.permission_level),
                            "status": self._normalize_optional_text(record.status) or "pending",
                            "user_id": getattr(record, "user_id", None),
                            "conversation_id": getattr(record, "conversation_id", None),
                            "plan_id": getattr(record, "plan_id", None),
                            "plan_item_id": getattr(record, "plan_item_id", None),
                            "result": self._normalize_optional_text(record.result),
                            "requested_at": self._serialize_datetime(getattr(record, "created_at", None)),
                            "completed_at": self._serialize_datetime(getattr(record, "completed_at", None)),
                            "run_id": self._normalize_optional_text(getattr(record, "run_id", None)),
                            "parent_run_id": self._normalize_optional_text(getattr(record, "parent_run_id", None)),
                            "child_run_id": self._normalize_optional_text(getattr(record, "child_run_id", None)),
                            "scheduler_run_id": self._normalize_optional_text(getattr(record, "scheduler_run_id", None)),
                            "run_kind": self._normalize_optional_text(getattr(record, "run_kind", None)),
                            "source_event_type": None,
                            "tool_args": dict(getattr(record, "tool_args", {}) or {}),
                            "request_metadata": dict(getattr(record, "request_metadata", {}) or {}),
                        }
                    if request_id not in trace_order:
                        trace_order.append(request_id)
                    records[str(record.request_id)] = ApprovalRequestState(
                        request_id=record.request_id,
                        tool_name=self._normalize_optional_text(record.tool_name),
                        permission_level=self._normalize_optional_text(record.permission_level),
                        status=self._normalize_optional_text(record.status) or "pending",
                        user_id=getattr(record, "user_id", None),
                        conversation_id=getattr(record, "conversation_id", None),
                        plan_id=getattr(record, "plan_id", None),
                        plan_item_id=getattr(record, "plan_item_id", None),
                        result=self._normalize_optional_text(record.result),
                        requested_at=self._serialize_datetime(getattr(record, "created_at", None)),
                        completed_at=self._serialize_datetime(getattr(record, "completed_at", None)),
                        run_id=self._normalize_optional_text(getattr(record, "run_id", None)),
                        parent_run_id=self._normalize_optional_text(getattr(record, "parent_run_id", None)),
                        child_run_id=self._normalize_optional_text(getattr(record, "child_run_id", None)),
                        scheduler_run_id=self._normalize_optional_text(getattr(record, "scheduler_run_id", None)),
                        run_kind=self._normalize_optional_text(getattr(record, "run_kind", None)),
                        source_event_type=None,
                        tool_args=dict(getattr(record, "tool_args", {}) or {}),
                        request_metadata=dict(getattr(record, "request_metadata", {}) or {}),
                    )
            except Exception:
                records = {}

        approvals: list[ApprovalRequestState] = []
        for request_id in trace_order:
            base_state = records.get(request_id)
            if base_state is None:
                base_state = ApprovalRequestState(**trace_index[request_id])
            else:
                trace_state = trace_index[request_id]
                if base_state.plan_id is None:
                    base_state.plan_id = trace_state.get("plan_id")
                if base_state.plan_item_id is None:
                    base_state.plan_item_id = trace_state.get("plan_item_id")
                if not base_state.run_id:
                    base_state.run_id = trace_state.get("run_id")
                if not base_state.parent_run_id:
                    base_state.parent_run_id = trace_state.get("parent_run_id")
                if not base_state.child_run_id:
                    base_state.child_run_id = trace_state.get("child_run_id")
                if not base_state.scheduler_run_id:
                    base_state.scheduler_run_id = trace_state.get("scheduler_run_id")
                if not base_state.run_kind:
                    base_state.run_kind = trace_state.get("run_kind")
                base_state.source_event_type = trace_state.get("source_event_type")
                if not base_state.tool_name:
                    base_state.tool_name = trace_state.get("tool_name")
                if not base_state.permission_level:
                    base_state.permission_level = trace_state.get("permission_level")
                if not base_state.requested_at:
                    base_state.requested_at = trace_state.get("requested_at")
                if not base_state.completed_at:
                    base_state.completed_at = trace_state.get("completed_at")
                if not base_state.result:
                    base_state.result = trace_state.get("result")
                if not base_state.tool_args:
                    base_state.tool_args = dict(trace_state.get("tool_args") or {})
                if not base_state.request_metadata:
                    base_state.request_metadata = dict(trace_state.get("request_metadata") or {})
            approvals.append(base_state)
        return approvals

    def _load_background_runs(self, item: Optional[PlanItemRecord]) -> list[BackgroundRunState]:
        runs: dict[str, BackgroundRunState] = {}
        if self._background_tables_ready() and item is not None:
            persisted_runs = self._list_persisted_background_runs(item)
            if not persisted_runs:
                for projected in self._project_background_runs(item):
                    self._persist_background_run(item, projected.to_dict())
                persisted_runs = self._list_persisted_background_runs(item)
            for run in persisted_runs:
                runs[run.background_run_id or f"background-{len(runs) + 1}"] = run
        for projected in self._project_background_runs(item):
            run_key = projected.background_run_id or f"background-{len(runs) + 1}"
            existing = runs.get(run_key)
            if existing is None:
                runs[run_key] = projected
                continue
            runs[run_key] = self._merge_background_state(existing, projected)
        return list(runs.values())

    def _project_background_runs(self, item: Optional[PlanItemRecord]) -> list[BackgroundRunState]:
        runs: dict[str, BackgroundRunState] = {}
        for index, event in enumerate(self.get_run_trace(item), start=1):
            if not isinstance(event, dict) or not self._is_background_event(event):
                continue
            payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
            run_key = (
                self._normalize_optional_text(payload.get("background_run_id"))
                or self._normalize_optional_text(event.get("run_id"))
                or self._normalize_optional_text(event.get("event_id"))
                or f"background-{index}"
            )
            existing = runs.get(run_key)
            if existing is None:
                existing = BackgroundRunState(
                    background_run_id=run_key,
                    run_id=self._normalize_optional_text(event.get("run_id")),
                    parent_run_id=self._normalize_optional_text(event.get("parent_run_id")),
                    scheduler_run_id=self._normalize_optional_text(
                        event.get("scheduler_run_id") or payload.get("scheduler_run_id")
                    ),
                    status=self._derive_activity_status(event),
                    source=self._normalize_optional_text(event.get("source")),
                    event_type=self._normalize_optional_text(event.get("event_type")),
                    title=self._normalize_optional_text(payload.get("title") or event.get("summary")),
                    detail=self._normalize_optional_text(event.get("detail")),
                    artifact_id=self._normalize_optional_text(payload.get("artifact_id")),
                    artifact_kind=self._normalize_optional_text(payload.get("artifact_kind")),
                    started_at=event.get("timestamp"),
                    completed_at=None,
                    metadata=dict(payload or {}),
                )
                runs[run_key] = existing
            existing.status = self._derive_activity_status(event, fallback=existing.status)
            existing.detail = self._normalize_optional_text(event.get("detail")) or existing.detail
            if existing.started_at is None:
                existing.started_at = event.get("timestamp")
            if existing.status in {"completed", "failed", "cancelled"}:
                existing.completed_at = event.get("timestamp") or existing.completed_at

        for artifact in self._list_runtime_artifacts(item):
            metadata = dict(getattr(artifact, "artifact_metadata", {}) or {})
            run_key = self._normalize_optional_text(metadata.get("background_run_id"))
            if not run_key:
                continue
            existing = runs.get(run_key)
            if existing is None:
                runs[run_key] = BackgroundRunState(
                    background_run_id=run_key,
                    run_id=self._normalize_optional_text(metadata.get("run_id")),
                    parent_run_id=self._normalize_optional_text(metadata.get("parent_run_id")),
                    scheduler_run_id=self._normalize_optional_text(metadata.get("scheduler_run_id")),
                    status=self._normalize_optional_text(metadata.get("status")) or "completed",
                    source="artifact",
                    event_type=None,
                    title=self._normalize_optional_text(metadata.get("title") or getattr(artifact, "kind", None)),
                    detail=self._normalize_optional_text(getattr(artifact, "content", None)),
                    artifact_id=self._normalize_optional_text(getattr(artifact, "artifact_id", None)),
                    artifact_kind=self._normalize_optional_text(getattr(artifact, "kind", None)),
                    started_at=self._serialize_datetime(getattr(artifact, "created_at", None)),
                    completed_at=self._serialize_datetime(getattr(artifact, "created_at", None)),
                    metadata=metadata,
                )
                continue
            if not existing.artifact_id:
                existing.artifact_id = self._normalize_optional_text(getattr(artifact, "artifact_id", None))
            if not existing.artifact_kind:
                existing.artifact_kind = self._normalize_optional_text(getattr(artifact, "kind", None))
        return list(runs.values())

    def _load_worktree_runs(self, item: Optional[PlanItemRecord]) -> list[WorktreeRunState]:
        runs: dict[str, WorktreeRunState] = {}
        if self._worktree_tables_ready() and item is not None:
            persisted_runs = self._list_persisted_worktree_runs(item)
            if not persisted_runs:
                for projected in self._project_worktree_runs(item):
                    self._persist_worktree_run(item, projected.to_dict())
                persisted_runs = self._list_persisted_worktree_runs(item)
            for run in persisted_runs:
                runs[run.worktree_run_id or f"worktree-{len(runs) + 1}"] = run
        for projected in self._project_worktree_runs(item):
            run_key = projected.worktree_run_id or f"worktree-{len(runs) + 1}"
            existing = runs.get(run_key)
            if existing is None:
                runs[run_key] = projected
                continue
            runs[run_key] = self._merge_worktree_state(existing, projected)
        return list(runs.values())

    def _project_worktree_runs(self, item: Optional[PlanItemRecord]) -> list[WorktreeRunState]:
        runs: dict[str, WorktreeRunState] = {}
        for index, event in enumerate(self.get_run_trace(item), start=1):
            if not isinstance(event, dict) or not self._is_worktree_event(event):
                continue
            payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
            run_key = (
                self._normalize_optional_text(payload.get("worktree_run_id"))
                or self._normalize_optional_text(event.get("run_id"))
                or self._normalize_optional_text(event.get("event_id"))
                or f"worktree-{index}"
            )
            existing = runs.get(run_key)
            if existing is None:
                existing = WorktreeRunState(
                    worktree_run_id=run_key,
                    run_id=self._normalize_optional_text(event.get("run_id")),
                    parent_run_id=self._normalize_optional_text(event.get("parent_run_id")),
                    scheduler_run_id=self._normalize_optional_text(
                        event.get("scheduler_run_id") or payload.get("scheduler_run_id")
                    ),
                    status=self._derive_activity_status(event),
                    source=self._normalize_optional_text(event.get("source")),
                    event_type=self._normalize_optional_text(event.get("event_type")),
                    workspace_path=self._normalize_optional_text(
                        payload.get("workspace_path") or payload.get("worktree_path")
                    ),
                    branch_name=self._normalize_optional_text(payload.get("branch_name")),
                    detail=self._normalize_optional_text(event.get("detail")),
                    started_at=event.get("timestamp"),
                    completed_at=None,
                    metadata=dict(payload or {}),
                )
                runs[run_key] = existing
            existing.status = self._derive_activity_status(event, fallback=existing.status)
            existing.detail = self._normalize_optional_text(event.get("detail")) or existing.detail
            if existing.started_at is None:
                existing.started_at = event.get("timestamp")
            if existing.status in {"completed", "failed", "cancelled"}:
                existing.completed_at = event.get("timestamp") or existing.completed_at

        for artifact in self._list_runtime_artifacts(item):
            metadata = dict(getattr(artifact, "artifact_metadata", {}) or {})
            run_key = self._normalize_optional_text(metadata.get("worktree_run_id"))
            if not run_key:
                continue
            existing = runs.get(run_key)
            if existing is None:
                runs[run_key] = WorktreeRunState(
                    worktree_run_id=run_key,
                    run_id=self._normalize_optional_text(metadata.get("run_id")),
                    parent_run_id=self._normalize_optional_text(metadata.get("parent_run_id")),
                    scheduler_run_id=self._normalize_optional_text(metadata.get("scheduler_run_id")),
                    status=self._normalize_optional_text(metadata.get("status")) or "completed",
                    source="artifact",
                    event_type=None,
                    workspace_path=self._normalize_optional_text(
                        metadata.get("workspace_path") or metadata.get("worktree_path")
                    ),
                    branch_name=self._normalize_optional_text(metadata.get("branch_name")),
                    detail=self._normalize_optional_text(getattr(artifact, "content", None)),
                    started_at=self._serialize_datetime(getattr(artifact, "created_at", None)),
                    completed_at=self._serialize_datetime(getattr(artifact, "created_at", None)),
                    metadata=metadata,
                )
                continue
            if not existing.workspace_path:
                existing.workspace_path = self._normalize_optional_text(
                    metadata.get("workspace_path") or metadata.get("worktree_path")
                )
            if not existing.branch_name:
                existing.branch_name = self._normalize_optional_text(metadata.get("branch_name"))
        return list(runs.values())

    def _persist_background_run(self, item: Optional[PlanItemRecord], run: Optional[dict]) -> Optional[BackgroundRunState]:
        if item is None or self.db is None or not self._background_tables_ready():
            return None
        data = dict(run or {})
        background_run_id = self._normalize_optional_text(data.get("background_run_id"))
        if not background_run_id:
            return None
        record = (
            self.db.query(BackgroundRunRecord)
            .filter(BackgroundRunRecord.background_run_id == background_run_id)
            .first()
        )
        if record is None:
            record = BackgroundRunRecord(
                background_run_id=background_run_id,
                plan_id=item.plan_id,
                plan_item_id=item.id,
            )
            self.db.add(record)
        record.background_run_id = background_run_id
        record.plan_id = item.plan_id
        record.plan_item_id = item.id
        record.run_id = self._normalize_optional_text(data.get("run_id"))
        record.parent_run_id = self._normalize_optional_text(data.get("parent_run_id"))
        record.scheduler_run_id = self._normalize_optional_text(data.get("scheduler_run_id"))
        record.status = self._normalize_optional_text(data.get("status")) or "running"
        record.source = self._normalize_optional_text(data.get("source"))
        record.event_type = self._normalize_optional_text(data.get("event_type"))
        record.title = self._normalize_optional_text(data.get("title"))
        record.detail = self._normalize_optional_text(data.get("detail"))
        record.artifact_id = self._normalize_optional_text(data.get("artifact_id"))
        record.artifact_kind = self._normalize_optional_text(data.get("artifact_kind"))
        record.run_metadata = dict(data.get("metadata") or {})
        record.started_at = self._parse_datetime(data.get("started_at"))
        record.completed_at = self._parse_datetime(data.get("completed_at"))
        self.db.flush()
        return self._background_record_to_state(record)

    def _persist_worktree_run(self, item: Optional[PlanItemRecord], run: Optional[dict]) -> Optional[WorktreeRunState]:
        if item is None or self.db is None or not self._worktree_tables_ready():
            return None
        data = dict(run or {})
        worktree_run_id = self._normalize_optional_text(data.get("worktree_run_id"))
        if not worktree_run_id:
            return None
        record = (
            self.db.query(WorktreeRunRecord)
            .filter(WorktreeRunRecord.worktree_run_id == worktree_run_id)
            .first()
        )
        if record is None:
            record = WorktreeRunRecord(
                worktree_run_id=worktree_run_id,
                plan_id=item.plan_id,
                plan_item_id=item.id,
            )
            self.db.add(record)
        record.worktree_run_id = worktree_run_id
        record.plan_id = item.plan_id
        record.plan_item_id = item.id
        record.run_id = self._normalize_optional_text(data.get("run_id"))
        record.parent_run_id = self._normalize_optional_text(data.get("parent_run_id"))
        record.scheduler_run_id = self._normalize_optional_text(data.get("scheduler_run_id"))
        record.status = self._normalize_optional_text(data.get("status")) or "running"
        record.source = self._normalize_optional_text(data.get("source"))
        record.event_type = self._normalize_optional_text(data.get("event_type"))
        record.workspace_path = self._normalize_optional_text(data.get("workspace_path"))
        record.branch_name = self._normalize_optional_text(data.get("branch_name"))
        record.detail = self._normalize_optional_text(data.get("detail"))
        record.run_metadata = dict(data.get("metadata") or {})
        record.started_at = self._parse_datetime(data.get("started_at"))
        record.completed_at = self._parse_datetime(data.get("completed_at"))
        self.db.flush()
        return self._worktree_record_to_state(record)

    def _list_persisted_background_runs(self, item: Optional[PlanItemRecord]) -> list[BackgroundRunState]:
        if item is None or self.db is None or not self._background_tables_ready():
            return []
        item_id = getattr(item, "id", None)
        if item_id is None:
            return []
        records = (
            self.db.query(BackgroundRunRecord)
            .filter(BackgroundRunRecord.plan_item_id == item_id)
            .order_by(BackgroundRunRecord.created_at.asc(), BackgroundRunRecord.id.asc())
            .all()
        )
        return [self._background_record_to_state(record) for record in records]

    def _list_persisted_worktree_runs(self, item: Optional[PlanItemRecord]) -> list[WorktreeRunState]:
        if item is None or self.db is None or not self._worktree_tables_ready():
            return []
        item_id = getattr(item, "id", None)
        if item_id is None:
            return []
        records = (
            self.db.query(WorktreeRunRecord)
            .filter(WorktreeRunRecord.plan_item_id == item_id)
            .order_by(WorktreeRunRecord.created_at.asc(), WorktreeRunRecord.id.asc())
            .all()
        )
        return [self._worktree_record_to_state(record) for record in records]

    def _background_record_to_state(self, record: BackgroundRunRecord) -> BackgroundRunState:
        return BackgroundRunState(
            background_run_id=self._normalize_optional_text(record.background_run_id),
            run_id=self._normalize_optional_text(record.run_id),
            parent_run_id=self._normalize_optional_text(record.parent_run_id),
            scheduler_run_id=self._normalize_optional_text(record.scheduler_run_id),
            status=self._normalize_optional_text(record.status) or "running",
            source=self._normalize_optional_text(record.source),
            event_type=self._normalize_optional_text(record.event_type),
            title=self._normalize_optional_text(record.title),
            detail=self._normalize_optional_text(record.detail),
            artifact_id=self._normalize_optional_text(record.artifact_id),
            artifact_kind=self._normalize_optional_text(record.artifact_kind),
            started_at=self._serialize_datetime(record.started_at or record.created_at),
            completed_at=self._serialize_datetime(record.completed_at),
            metadata=dict(record.run_metadata or {}),
        )

    def _worktree_record_to_state(self, record: WorktreeRunRecord) -> WorktreeRunState:
        return WorktreeRunState(
            worktree_run_id=self._normalize_optional_text(record.worktree_run_id),
            run_id=self._normalize_optional_text(record.run_id),
            parent_run_id=self._normalize_optional_text(record.parent_run_id),
            scheduler_run_id=self._normalize_optional_text(record.scheduler_run_id),
            status=self._normalize_optional_text(record.status) or "running",
            source=self._normalize_optional_text(record.source),
            event_type=self._normalize_optional_text(record.event_type),
            workspace_path=self._normalize_optional_text(record.workspace_path),
            branch_name=self._normalize_optional_text(record.branch_name),
            detail=self._normalize_optional_text(record.detail),
            started_at=self._serialize_datetime(record.started_at or record.created_at),
            completed_at=self._serialize_datetime(record.completed_at),
            metadata=dict(record.run_metadata or {}),
        )

    def _merge_background_state(
        self,
        persisted: BackgroundRunState,
        projected: BackgroundRunState,
    ) -> BackgroundRunState:
        return BackgroundRunState(
            background_run_id=persisted.background_run_id or projected.background_run_id,
            run_id=persisted.run_id or projected.run_id,
            parent_run_id=persisted.parent_run_id or projected.parent_run_id,
            scheduler_run_id=persisted.scheduler_run_id or projected.scheduler_run_id,
            status=persisted.status or projected.status,
            source=persisted.source or projected.source,
            event_type=persisted.event_type or projected.event_type,
            title=persisted.title or projected.title,
            detail=persisted.detail or projected.detail,
            artifact_id=persisted.artifact_id or projected.artifact_id,
            artifact_kind=persisted.artifact_kind or projected.artifact_kind,
            started_at=persisted.started_at or projected.started_at,
            completed_at=persisted.completed_at or projected.completed_at,
            metadata=dict(persisted.metadata or projected.metadata or {}),
        )

    def _merge_worktree_state(
        self,
        persisted: WorktreeRunState,
        projected: WorktreeRunState,
    ) -> WorktreeRunState:
        return WorktreeRunState(
            worktree_run_id=persisted.worktree_run_id or projected.worktree_run_id,
            run_id=persisted.run_id or projected.run_id,
            parent_run_id=persisted.parent_run_id or projected.parent_run_id,
            scheduler_run_id=persisted.scheduler_run_id or projected.scheduler_run_id,
            status=persisted.status or projected.status,
            source=persisted.source or projected.source,
            event_type=persisted.event_type or projected.event_type,
            workspace_path=persisted.workspace_path or projected.workspace_path,
            branch_name=persisted.branch_name or projected.branch_name,
            detail=persisted.detail or projected.detail,
            started_at=persisted.started_at or projected.started_at,
            completed_at=persisted.completed_at or projected.completed_at,
            metadata=dict(persisted.metadata or projected.metadata or {}),
        )

    def _background_tables_ready(self) -> bool:
        return self._table_exists("background_runs")

    def _worktree_tables_ready(self) -> bool:
        return self._table_exists("worktree_runs")

    def _table_exists(self, table_name: str) -> bool:
        if not self._available_tables:
            return False
        return table_name in self._available_tables

    def _discover_available_tables(self) -> set[str]:
        bind = getattr(self.db, "bind", None)
        if self.db is None or bind is None:
            return set()
        try:
            return set(inspect(bind).get_table_names())
        except Exception:
            return set()

    def _extract_request_id(self, event: dict) -> Optional[str]:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        return self._normalize_optional_text(payload.get("request_id"))

    def _derive_approval_status(self, event: dict) -> Optional[str]:
        event_type = str(event.get("event_type") or "").strip().lower()
        if event_type == "tool_permission_required":
            return "pending"
        if event_type == "permission_approved":
            return "approved"
        if event_type in {"permission_denied", "tool_denied"}:
            return "denied"
        return None

    def _derive_activity_status(self, event: dict, fallback: str = "running") -> str:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        payload_status = self._normalize_optional_text(payload.get("status"))
        if payload_status:
            return payload_status
        event_type = str(event.get("event_type") or "").strip().lower()
        if event_type.endswith("_completed") or event_type.endswith("_merged"):
            return "completed"
        if event_type.endswith("_failed"):
            return "failed"
        if event_type.endswith("_cancelled"):
            return "cancelled"
        if event_type.endswith("_started") or event_type.endswith("_prepared"):
            return "running"
        return fallback

    def _is_background_event(self, event: dict) -> bool:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        run_kind = str(event.get("run_kind") or payload.get("run_kind") or "").strip().lower()
        source = str(event.get("source") or "").strip().lower()
        event_type = str(event.get("event_type") or "").strip().lower()
        execution_mode = str(payload.get("execution_mode") or "").strip().lower()
        return (
            run_kind == "background"
            or source == "background"
            or execution_mode == "background"
            or "background" in event_type
        )

    def _is_worktree_event(self, event: dict) -> bool:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        source = str(event.get("source") or "").strip().lower()
        event_type = str(event.get("event_type") or "").strip().lower()
        return (
            source == "worktree"
            or "worktree" in event_type
            or self._normalize_optional_text(payload.get("workspace_path")) is not None
            or self._normalize_optional_text(payload.get("worktree_path")) is not None
            or self._normalize_optional_text(payload.get("branch_name")) is not None
        )

    def _resolve_conversation_id(self, item: Optional[PlanItemRecord]) -> Optional[int]:
        if item is None:
            return None
        plan = getattr(item, "plan", None)
        conversation_id = getattr(plan, "conversation_id", None)
        if conversation_id is not None:
            return conversation_id
        if self.db is None:
            return None
        plan_id = getattr(item, "plan_id", None)
        if plan_id is None:
            return None
        try:
            plan = self.db.query(PlanRunRecord).filter(PlanRunRecord.id == plan_id).first()
        except Exception:
            return None
        return getattr(plan, "conversation_id", None) if plan is not None else None

    def _list_runtime_artifacts(self, item: Optional[PlanItemRecord]) -> list[ArtifactRecord]:
        conversation_id = self._resolve_conversation_id(item)
        if self.db is None or conversation_id is None:
            return []
        try:
            return (
                self.db.query(ArtifactRecord)
                .filter(ArtifactRecord.conversation_id == conversation_id)
                .order_by(ArtifactRecord.created_at.desc(), ArtifactRecord.id.desc())
                .limit(50)
                .all()
            )
        except Exception:
            return []

    def _serialize_datetime(self, value: object) -> Optional[str]:
        if value is None:
            return None
        isoformat = getattr(value, "isoformat", None)
        if callable(isoformat):
            return value.isoformat()
        return self._normalize_optional_text(value)

    def _parse_datetime(self, value: object):
        if value is None:
            return None
        if hasattr(value, "tzinfo") or hasattr(value, "year"):
            return value
        text = self._normalize_optional_text(value)
        if not text:
            return None
        try:
            from datetime import datetime

            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None

    def _normalize_optional_text(self, value: object) -> Optional[str]:
        text = str(value or "").strip()
        return text or None

    def _resolve_repository(self, db) -> SchedulerRuntimeRepository:
        normalized_backend = self.requested_backend
        metadata_repository = self.metadata_repository
        if normalized_backend == "metadata":
            self.selection.update({
                "effective_backend": "metadata",
                "backend_source": "metadata",
                "table_ready": False,
                "fallback_reason": None,
            })
            return metadata_repository
        if db is None:
            self.selection.update({
                "effective_backend": "metadata",
                "backend_source": "metadata",
                "table_ready": False,
                "fallback_reason": "database_session_unavailable",
            })
            return metadata_repository
        relational_repository = get_scheduler_runtime_sql_repository(db)
        relational_ready = relational_repository.is_available()
        if normalized_backend == "relational":
            if relational_ready:
                self.selection.update({
                    "effective_backend": "relational",
                    "backend_source": "relational",
                    "table_ready": True,
                    "fallback_reason": None,
                })
                return relational_repository
            self.selection.update({
                "effective_backend": "metadata",
                "backend_source": "metadata",
                "table_ready": False,
                "fallback_reason": "scheduler_runtime_tables_missing",
            })
            return metadata_repository
        if normalized_backend == "auto":
            if relational_ready:
                self.selection.update({
                    "effective_backend": "relational",
                    "backend_source": "relational",
                    "table_ready": True,
                    "fallback_reason": None,
                })
                return relational_repository
            self.selection.update({
                "effective_backend": "metadata",
                "backend_source": "metadata",
                "table_ready": False,
                "fallback_reason": "scheduler_runtime_tables_missing",
            })
            return metadata_repository
        self.selection.update({
            "effective_backend": "metadata",
            "backend_source": "metadata",
            "table_ready": False,
            "fallback_reason": "unknown_scheduler_runtime_backend",
        })
        return metadata_repository

    def _refresh_selection_from_repository(self) -> None:
        descriptor = dict(self.repository.get_persistence_descriptor() or {})
        backend = str(descriptor.get("backend") or "metadata_adapter").strip().lower()
        effective_backend = "relational" if backend == "relational_tables" else "metadata"
        backend_source = "relational" if effective_backend == "relational" else "metadata"
        self.selection.update({
            "effective_backend": effective_backend,
            "backend_source": backend_source,
            "table_ready": bool(descriptor.get("migration_ready", False) or descriptor.get("table_ready", False)),
            "fallback_reason": None,
        })

    def _call_repository(self, method_name: str, *args, **kwargs):
        method = getattr(self.repository, method_name)
        try:
            return method(*args, **kwargs)
        except Exception:
            if self.repository is self.metadata_repository:
                raise
            self.repository = self.metadata_repository
            self.selection.update({
                "effective_backend": "metadata",
                "backend_source": "metadata",
                "table_ready": False,
                "fallback_reason": f"runtime_operation_failed:{method_name}",
            })
            fallback_method = getattr(self.repository, method_name)
            return fallback_method(*args, **kwargs)


def get_scheduler_runtime_store(db=None) -> SchedulerRuntimeStore:
    return SchedulerRuntimeStore(db=db)
