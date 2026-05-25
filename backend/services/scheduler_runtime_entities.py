"""Typed scheduler runtime entities and serialization helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class SchedulerRuntimePersistenceDescriptor:
    backend: str = "metadata_adapter"
    scope: str = "plan_item_metadata"
    durable: bool = True
    migration_ready: bool = False
    requested_backend: str = "metadata"
    effective_backend: str = "metadata"
    backend_source: str = "metadata"
    table_ready: bool = False
    fallback_reason: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "backend": self.backend,
            "scope": self.scope,
            "durable": self.durable,
            "migration_ready": self.migration_ready,
            "requested_backend": self.requested_backend,
            "effective_backend": self.effective_backend,
            "backend_source": self.backend_source,
            "table_ready": self.table_ready,
            "fallback_reason": self.fallback_reason,
        }


@dataclass
class SchedulerRunState:
    run_id: Optional[str] = None
    parent_run_id: Optional[str] = None
    run_kind: Optional[str] = None
    state: Optional[str] = None
    merge_strategy: Optional[str] = None
    merge_status: Optional[str] = None
    policy: dict = field(default_factory=dict)
    last_merge_at: Optional[str] = None
    merged_output: Optional[str] = None
    child_count: int = 0
    active_children: int = 0
    child_status_counts: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "parent_run_id": self.parent_run_id,
            "run_kind": self.run_kind,
            "state": self.state,
            "merge_strategy": self.merge_strategy,
            "merge_status": self.merge_status,
            "policy": dict(self.policy or {}),
            "last_merge_at": self.last_merge_at,
            "merged_output": self.merged_output,
            "child_count": self.child_count,
            "active_children": self.active_children,
            "child_status_counts": dict(self.child_status_counts or {}),
        }


@dataclass
class ChildRunState:
    child_execution_id: Optional[str] = None
    child_run_id: Optional[str] = None
    run_id: Optional[str] = None
    parent_run_id: Optional[str] = None
    run_kind: str = "child"
    scheduler_run_id: Optional[str] = None
    agent_role: Optional[str] = None
    agent_id: Optional[str] = None
    status: str = "queued"
    title: Optional[str] = None
    summary: Optional[str] = None
    error: Optional[str] = None
    error_kind: Optional[str] = None
    retry_count: int = 0
    model_name: Optional[str] = None
    provider_name: Optional[str] = None
    provider_order: list[str] = field(default_factory=list)
    provider_switch_count: int = 0
    provider_history: list[dict] = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    cancelled_at: Optional[str] = None
    last_retry_error: Optional[str] = None
    approval_event: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        child_display_id = self.child_run_id or self.child_execution_id
        return {
            "child_execution_id": self.child_execution_id,
            "child_run_id": self.child_run_id,
            "child_display_id": child_display_id,
            "run_id": self.run_id,
            "parent_run_id": self.parent_run_id,
            "run_kind": self.run_kind,
            "scheduler_run_id": self.scheduler_run_id,
            "agent_role": self.agent_role,
            "agent_id": self.agent_id,
            "status": self.status,
            "title": self.title,
            "summary": self.summary,
            "error": self.error,
            "error_kind": self.error_kind,
            "retry_count": self.retry_count,
            "model_name": self.model_name,
            "provider_name": self.provider_name,
            "provider_order": list(self.provider_order or []),
            "provider_switch_count": self.provider_switch_count,
            "provider_history": [dict(entry) for entry in (self.provider_history or [])],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "cancelled_at": self.cancelled_at,
            "last_retry_error": self.last_retry_error,
            "approval_event": dict(self.approval_event or {}),
        }


@dataclass
class ApprovalRequestState:
    request_id: Optional[str] = None
    request_kind: str = "tool_permission"
    tool_name: Optional[str] = None
    permission_level: Optional[str] = None
    status: str = "pending"
    user_id: Optional[int] = None
    conversation_id: Optional[int] = None
    plan_id: Optional[int] = None
    plan_item_id: Optional[int] = None
    result: Optional[str] = None
    requested_at: Optional[str] = None
    completed_at: Optional[str] = None
    run_id: Optional[str] = None
    parent_run_id: Optional[str] = None
    child_run_id: Optional[str] = None
    child_display_id: Optional[str] = None
    scheduler_run_id: Optional[str] = None
    run_kind: Optional[str] = None
    source_event_type: Optional[str] = None
    requires_approval: bool = True
    reason_code: Optional[str] = None
    reason: Optional[str] = None
    requested_by_role: Optional[str] = None
    requested_by_agent_id: Optional[str] = None
    tool_args: dict = field(default_factory=dict)
    request_metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "request_kind": self.request_kind,
            "tool_name": self.tool_name,
            "permission_level": self.permission_level,
            "status": self.status,
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "plan_id": self.plan_id,
            "plan_item_id": self.plan_item_id,
            "result": self.result,
            "requested_at": self.requested_at,
            "completed_at": self.completed_at,
            "run_id": self.run_id,
            "parent_run_id": self.parent_run_id,
            "child_run_id": self.child_run_id,
            "child_display_id": self.child_display_id,
            "scheduler_run_id": self.scheduler_run_id,
            "run_kind": self.run_kind,
            "source_event_type": self.source_event_type,
            "requires_approval": self.requires_approval,
            "reason_code": self.reason_code,
            "reason": self.reason,
            "requested_by_role": self.requested_by_role,
            "requested_by_agent_id": self.requested_by_agent_id,
            "tool_args": dict(self.tool_args or {}),
            "request_metadata": dict(self.request_metadata or {}),
        }

    @classmethod
    def from_dict(cls, payload: dict | None) -> "ApprovalRequestState":
        data = dict(payload or {})
        return cls(
            request_id=data.get("request_id"),
            request_kind=str(data.get("request_kind") or "tool_permission"),
            tool_name=data.get("tool_name"),
            permission_level=data.get("permission_level"),
            status=str(data.get("status") or "pending"),
            user_id=data.get("user_id"),
            conversation_id=data.get("conversation_id"),
            plan_id=data.get("plan_id"),
            plan_item_id=data.get("plan_item_id"),
            result=data.get("result"),
            requested_at=data.get("requested_at"),
            completed_at=data.get("completed_at"),
            run_id=data.get("run_id"),
            parent_run_id=data.get("parent_run_id"),
            child_run_id=data.get("child_run_id"),
            child_display_id=data.get("child_display_id"),
            scheduler_run_id=data.get("scheduler_run_id"),
            run_kind=data.get("run_kind"),
            source_event_type=data.get("source_event_type"),
            requires_approval=bool(data.get("requires_approval", True)),
            reason_code=data.get("reason_code"),
            reason=data.get("reason"),
            requested_by_role=data.get("requested_by_role"),
            requested_by_agent_id=data.get("requested_by_agent_id"),
            tool_args=dict(data.get("tool_args") or {}),
            request_metadata=dict(data.get("request_metadata") or {}),
        )


@dataclass
class BackgroundRunState:
    background_run_id: Optional[str] = None
    run_id: Optional[str] = None
    parent_run_id: Optional[str] = None
    scheduler_run_id: Optional[str] = None
    status: str = "running"
    source: Optional[str] = None
    event_type: Optional[str] = None
    title: Optional[str] = None
    detail: Optional[str] = None
    artifact_id: Optional[str] = None
    artifact_kind: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "background_run_id": self.background_run_id,
            "run_id": self.run_id,
            "parent_run_id": self.parent_run_id,
            "scheduler_run_id": self.scheduler_run_id,
            "status": self.status,
            "source": self.source,
            "event_type": self.event_type,
            "title": self.title,
            "detail": self.detail,
            "artifact_id": self.artifact_id,
            "artifact_kind": self.artifact_kind,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": dict(self.metadata or {}),
        }


@dataclass
class WorktreeRunState:
    worktree_run_id: Optional[str] = None
    run_id: Optional[str] = None
    parent_run_id: Optional[str] = None
    scheduler_run_id: Optional[str] = None
    status: str = "running"
    source: Optional[str] = None
    event_type: Optional[str] = None
    workspace_path: Optional[str] = None
    branch_name: Optional[str] = None
    detail: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "worktree_run_id": self.worktree_run_id,
            "run_id": self.run_id,
            "parent_run_id": self.parent_run_id,
            "scheduler_run_id": self.scheduler_run_id,
            "status": self.status,
            "source": self.source,
            "event_type": self.event_type,
            "workspace_path": self.workspace_path,
            "branch_name": self.branch_name,
            "detail": self.detail,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": dict(self.metadata or {}),
        }


@dataclass
class SchedulerRuntimeState:
    scheduler_run: SchedulerRunState = field(default_factory=SchedulerRunState)
    child_runs: list[ChildRunState] = field(default_factory=list)
    approval_requests: list[ApprovalRequestState] = field(default_factory=list)
    background_runs: list[BackgroundRunState] = field(default_factory=list)
    worktree_runs: list[WorktreeRunState] = field(default_factory=list)
    persistence: SchedulerRuntimePersistenceDescriptor = field(default_factory=SchedulerRuntimePersistenceDescriptor)

    def to_dict(self) -> dict:
        return {
            "scheduler_run": self.scheduler_run.to_dict(),
            "child_runs": [child.to_dict() for child in self.child_runs],
            "approval_requests": [request.to_dict() for request in self.approval_requests],
            "background_runs": [run.to_dict() for run in self.background_runs],
            "worktree_runs": [run.to_dict() for run in self.worktree_runs],
            "persistence": self.persistence.to_dict(),
        }
