"""Minimal multi-agent scheduler for planner fan-out / collect / merge."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Iterable, Optional

try:
    from models import PlanHandoffStatus, PlanItemRecord, PlanRunRecord
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.models import PlanHandoffStatus, PlanItemRecord, PlanRunRecord

try:
    from services.subagent_service import get_subagent_runtime_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.subagent_service import get_subagent_runtime_service

try:
    from services.scheduler_runtime_store import get_scheduler_runtime_store
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.scheduler_runtime_store import get_scheduler_runtime_store


CHILD_STATUSES = {"queued", "running", "completed", "failed", "cancelled"}
ROLE_ORDER = ("planner", "backend", "frontend", "qa", "docs")
DEFAULT_TIMEOUT_SECONDS = 45
DEFAULT_MAX_RETRIES = 1
DEFAULT_CANCEL_ON_FAILURE = False


class SchedulerService:
    """Persist and coordinate fan-out child executions for one active plan item."""

    def __init__(self, db):
        self.db = db
        self.subagent_runtime_service = get_subagent_runtime_service()
        self.runtime_store = get_scheduler_runtime_store(db)

    def prepare_execution(
        self,
        *,
        plan: Optional[PlanRunRecord],
        item: Optional[PlanItemRecord] = None,
    ) -> Optional[dict]:
        if plan is None:
            return None

        active_item = item or self._get_active_item(plan)
        if active_item is None:
            return None

        child_roles = self._resolve_child_roles(active_item)
        if len(child_roles) <= 1:
            return None

        group = self.runtime_store.get_child_group(active_item) or {}
        children = []
        now_text = self._now_text()
        required_capabilities = self.runtime_store.get_required_capabilities(active_item)

        active_item.agent_id = active_item.agent_id or self._build_scheduler_agent_id(plan=plan, item=active_item)
        active_item.handoff_status = PlanHandoffStatus.HANDED_OFF

        existing_children = group.get("children") or []
        scheduler_run_id = str(group.get("run_id") or "").strip() or self._build_scheduler_run_id(plan=plan, item=active_item)
        for index, role in enumerate(child_roles, start=1):
            existing = next((row for row in existing_children if row.get("agent_role") == role), None)
            child_execution_id = (
                str(existing.get("child_execution_id")).strip()
                if existing and str(existing.get("child_execution_id") or "").strip()
                else self._build_child_execution_id(plan=plan, item=active_item, index=index, role=role)
            )
            agent_id = (
                str(existing.get("agent_id")).strip()
                if existing and str(existing.get("agent_id") or "").strip()
                else self._build_child_agent_id(plan=plan, item=active_item, index=index, role=role)
            )
            status = str(existing.get("status") or "queued").strip().lower() if existing else "queued"
            if status not in CHILD_STATUSES:
                status = "queued"
            child = {
                "child_execution_id": child_execution_id,
                "child_run_id": str(existing.get("child_run_id") or "").strip() if existing else child_execution_id,
                "parent_run_id": (
                    str(existing.get("parent_run_id") or "").strip()
                    if existing and str(existing.get("parent_run_id") or "").strip()
                    else scheduler_run_id
                ),
                "run_id": (
                    str(existing.get("run_id") or "").strip()
                    if existing and str(existing.get("run_id") or "").strip()
                    else child_execution_id
                ),
                "run_kind": str(existing.get("run_kind") or "").strip() if existing else "child",
                "agent_role": role,
                "agent_id": agent_id,
                "status": status,
                "title": getattr(active_item, "title", ""),
                "scheduler_run_id": scheduler_run_id,
                "summary": str(existing.get("summary") or "").strip() if existing else "",
                "error": str(existing.get("error") or "").strip() if existing else "",
                "error_kind": str(existing.get("error_kind") or "").strip() if existing else "",
                "retry_count": int(existing.get("retry_count") or 0) if existing else 0,
                "model_name": str(existing.get("model_name") or "").strip() if existing else "",
                "provider_name": str(existing.get("provider_name") or "").strip() if existing else "",
                "provider_order": list(existing.get("provider_order") or []) if existing else [],
                "provider_switch_count": int(existing.get("provider_switch_count") or 0) if existing else 0,
                "provider_history": list(existing.get("provider_history") or []) if existing else [],
                "created_at": str(existing.get("created_at") if existing else now_text),
                "updated_at": now_text,
                "started_at": str(existing.get("started_at") or "").strip() if existing else "",
                "completed_at": str(existing.get("completed_at") or "").strip() if existing else "",
                "cancelled_at": str(existing.get("cancelled_at") or "").strip() if existing else "",
            }
            children.append(child)

        group = {
            "run_id": scheduler_run_id,
            "merge_strategy": str(group.get("merge_strategy") or "role_sections").strip() or "role_sections",
            "merge_status": str(group.get("merge_status") or "pending").strip() or "pending",
            "merged_output": str(group.get("merged_output") or ""),
                "policy": self._normalize_policy(
                    group.get("policy")
                or self.runtime_store.get_metadata(active_item).get("child_execution_policy")
                or {}
            ),
            "children": children,
            "last_merge_at": group.get("last_merge_at"),
        }
        self.runtime_store.save_child_roles(active_item, list(child_roles))
        self.runtime_store.save_runtime(active_item, scheduler_run=group, child_runs=children)
        self.append_audit_event(
            plan=plan,
            item_id=active_item.id,
            event_type="scheduler_fanout_prepared",
            content=f"已为当前步骤准备 {len(children)} 个子执行单元",
            payload={
                "child_count": len(children),
                "child_roles": list(child_roles),
                "scheduler_run_id": group["run_id"],
                "policy": dict(group["policy"]),
            },
            commit=False,
        )
        self.append_run_trace_event(
            plan=plan,
            item_id=active_item.id,
            source="scheduler",
            event_type="scheduler_fanout_prepared",
            summary=f"已为当前步骤准备 {len(children)} 个子执行单元",
            detail="调度器已完成 fan-out 拆分。",
            severity="info",
            payload={
                "child_count": len(children),
                "child_roles": list(child_roles),
                "scheduler_run_id": group["run_id"],
            },
            commit=False,
        )
        self._commit_refresh(plan)

        return {
            "plan": plan,
            "item": active_item,
            "child_count": len(children),
            "child_roles": list(child_roles),
            "execution_context": self.build_execution_context(
                plan=plan,
                item=active_item,
                required_capabilities=required_capabilities,
            ),
        }

    def mark_execution_started(
        self,
        *,
        plan: Optional[PlanRunRecord],
        item_id: Optional[int] = None,
    ) -> Optional[PlanRunRecord]:
        active_item = self._get_active_item(plan, item_id=item_id)
        if active_item is None:
            return plan
        if self._get_child_group(active_item):
            active_item.handoff_status = PlanHandoffStatus.EXECUTING
            self.append_audit_event(
                plan=plan,
                item_id=active_item.id,
                event_type="scheduler_execution_started",
                content="调度器已开始执行当前计划项",
                payload={},
                commit=False,
            )
            self.append_run_trace_event(
                plan=plan,
                item_id=active_item.id,
                source="scheduler",
                event_type="scheduler_execution_started",
                summary="调度器开始执行当前步骤",
                detail="子执行单元已进入运行阶段。",
                severity="info",
                payload={},
                commit=False,
            )
            self._commit_refresh(plan)
        return plan

    def mark_child_running(
        self,
        *,
        plan: Optional[PlanRunRecord],
        item_id: int,
        child_execution_id: str,
    ) -> Optional[PlanRunRecord]:
        active_item = self._get_active_item(plan, item_id=item_id)
        child = self.runtime_store.get_child_run(active_item, child_execution_id)
        if child is None:
            return plan
        child["status"] = "running"
        child["updated_at"] = self._now_text()
        child["started_at"] = self._now_text()
        self.runtime_store.replace_child_run(active_item, child_execution_id, child)
        self.append_audit_event(
            plan=plan,
            item_id=item_id,
            event_type="child_running",
            content=f"{child.get('agent_role', 'general')} 子执行开始运行",
            payload={
                "child_execution_id": child_execution_id,
                "agent_role": child.get("agent_role"),
                "agent_id": child.get("agent_id"),
            },
            commit=False,
        )
        self.append_run_trace_event(
            plan=plan,
            item_id=item_id,
            source="subagent",
            event_type="child_running",
            summary=f"{child.get('agent_role', 'general')} 子执行开始运行",
            detail=f"agent_id={child.get('agent_id') or 'unknown'}",
            severity="info",
            payload={
                "child_execution_id": child_execution_id,
                "agent_role": child.get("agent_role"),
                "agent_id": child.get("agent_id"),
            },
            commit=False,
        )
        self._commit_refresh(plan)
        return plan

    def mark_child_policy_selected(
        self,
        *,
        plan: Optional[PlanRunRecord],
        item_id: int,
        child_execution_id: str,
        model_name: str,
        provider_name: str,
        provider_order: Optional[list[str]] = None,
        provider_switch_count: Optional[int] = None,
        provider_history: Optional[list[dict]] = None,
    ) -> Optional[PlanRunRecord]:
        active_item = self._get_active_item(plan, item_id=item_id)
        child = self.runtime_store.get_child_run(active_item, child_execution_id)
        if child is None:
            return plan
        child["model_name"] = str(model_name or "").strip()
        child["provider_name"] = str(provider_name or "").strip()
        child["provider_order"] = list(provider_order or [])
        if provider_switch_count is not None:
            child["provider_switch_count"] = max(0, int(provider_switch_count))
        if provider_history is not None:
            child["provider_history"] = list(provider_history)
        child["updated_at"] = self._now_text()
        self.runtime_store.replace_child_run(active_item, child_execution_id, child)
        self.append_audit_event(
            plan=plan,
            item_id=item_id,
            event_type="child_policy_selected",
            content=f"{child.get('agent_role', 'general')} 子执行策略已装载",
            payload={
                "child_execution_id": child_execution_id,
                "agent_role": child.get("agent_role"),
                "agent_id": child.get("agent_id"),
                "model_name": child.get("model_name"),
                "provider_name": child.get("provider_name"),
                "provider_order": child.get("provider_order"),
                "provider_switch_count": child.get("provider_switch_count", 0),
            },
            commit=False,
        )
        self._commit_refresh(plan)
        return plan

    def mark_child_completed(
        self,
        *,
        plan: Optional[PlanRunRecord],
        item_id: int,
        child_execution_id: str,
        output_text: str,
    ) -> Optional[PlanRunRecord]:
        active_item = self._get_active_item(plan, item_id=item_id)
        child = self.runtime_store.get_child_run(active_item, child_execution_id)
        if child is None:
            return plan
        child["status"] = "completed"
        child["summary"] = str(output_text or "").strip()
        child["error"] = ""
        child["updated_at"] = self._now_text()
        child["completed_at"] = self._now_text()
        self.runtime_store.replace_child_run(active_item, child_execution_id, child)
        self.append_audit_event(
            plan=plan,
            item_id=item_id,
            event_type="child_completed",
            content=f"{child.get('agent_role', 'general')} 子执行已完成",
            payload={
                "child_execution_id": child_execution_id,
                "agent_role": child.get("agent_role"),
                "agent_id": child.get("agent_id"),
                "summary": child.get("summary"),
            },
            commit=False,
        )
        self.append_run_trace_event(
            plan=plan,
            item_id=item_id,
            source="subagent",
            event_type="child_completed",
            summary=f"{child.get('agent_role', 'general')} 子执行已完成",
            detail=child.get("summary") or "",
            severity="success",
            payload={
                "child_execution_id": child_execution_id,
                "agent_role": child.get("agent_role"),
                "agent_id": child.get("agent_id"),
            },
            commit=False,
        )
        self._commit_refresh(plan)
        return plan

    def mark_child_failed(
        self,
        *,
        plan: Optional[PlanRunRecord],
        item_id: int,
        child_execution_id: str,
        error_text: str,
        error_kind: str = "failed",
        retry_count: Optional[int] = None,
    ) -> Optional[PlanRunRecord]:
        active_item = self._get_active_item(plan, item_id=item_id)
        child = self.runtime_store.get_child_run(active_item, child_execution_id)
        if child is None:
            return plan
        child["status"] = "failed"
        child["error"] = str(error_text or "").strip()
        child["error_kind"] = str(error_kind or "failed").strip()
        if retry_count is not None:
            child["retry_count"] = max(0, int(retry_count))
        child["updated_at"] = self._now_text()
        self.runtime_store.replace_child_run(active_item, child_execution_id, child)
        self.append_audit_event(
            plan=plan,
            item_id=item_id,
            event_type="child_failed",
            content=f"{child.get('agent_role', 'general')} 子执行失败",
            payload={
                "child_execution_id": child_execution_id,
                "agent_role": child.get("agent_role"),
                "agent_id": child.get("agent_id"),
                "error": child.get("error"),
                "error_kind": child.get("error_kind"),
                "retry_count": child.get("retry_count", 0),
            },
            commit=False,
        )
        self.append_run_trace_event(
            plan=plan,
            item_id=item_id,
            source="subagent",
            event_type="child_failed",
            summary=f"{child.get('agent_role', 'general')} 子执行失败",
            detail=child.get("error") or "",
            severity="error" if child.get("error_kind") != "timeout" else "warning",
            payload={
                "child_execution_id": child_execution_id,
                "agent_role": child.get("agent_role"),
                "agent_id": child.get("agent_id"),
                "error_kind": child.get("error_kind"),
                "retry_count": child.get("retry_count", 0),
            },
            commit=False,
        )
        self._commit_refresh(plan)
        return plan

    def mark_child_retrying(
        self,
        *,
        plan: Optional[PlanRunRecord],
        item_id: int,
        child_execution_id: str,
        retry_count: int,
        error_text: str,
    ) -> Optional[PlanRunRecord]:
        active_item = self._get_active_item(plan, item_id=item_id)
        child = self.runtime_store.get_child_run(active_item, child_execution_id)
        if child is None:
            return plan
        child["status"] = "running"
        child["retry_count"] = max(0, int(retry_count))
        child["last_retry_error"] = str(error_text or "").strip()
        child["updated_at"] = self._now_text()
        self.runtime_store.replace_child_run(active_item, child_execution_id, child)
        self.append_audit_event(
            plan=plan,
            item_id=item_id,
            event_type="child_retrying",
            content=f"{child.get('agent_role', 'general')} 子执行开始重试",
            payload={
                "child_execution_id": child_execution_id,
                "agent_role": child.get("agent_role"),
                "agent_id": child.get("agent_id"),
                "retry_count": child.get("retry_count", 0),
                "error": child.get("last_retry_error"),
            },
            commit=False,
        )
        self.append_run_trace_event(
            plan=plan,
            item_id=item_id,
            source="scheduler",
            event_type="child_retrying",
            summary=f"{child.get('agent_role', 'general')} 子执行开始重试",
            detail=child.get("last_retry_error") or "",
            severity="warning",
            payload={
                "child_execution_id": child_execution_id,
                "agent_role": child.get("agent_role"),
                "retry_count": child.get("retry_count", 0),
            },
            commit=False,
        )
        self._commit_refresh(plan)
        return plan

    def mark_child_cancelled(
        self,
        *,
        plan: Optional[PlanRunRecord],
        item_id: int,
        child_execution_id: str,
        reason: str,
    ) -> Optional[PlanRunRecord]:
        active_item = self._get_active_item(plan, item_id=item_id)
        child = self.runtime_store.get_child_run(active_item, child_execution_id)
        if child is None:
            return plan
        child["status"] = "cancelled"
        child["error"] = str(reason or "").strip()
        child["error_kind"] = "cancelled"
        child["cancelled_at"] = self._now_text()
        child["updated_at"] = self._now_text()
        self.runtime_store.replace_child_run(active_item, child_execution_id, child)
        self.append_audit_event(
            plan=plan,
            item_id=item_id,
            event_type="child_cancelled",
            content=f"{child.get('agent_role', 'general')} 子执行已取消",
            payload={
                "child_execution_id": child_execution_id,
                "agent_role": child.get("agent_role"),
                "agent_id": child.get("agent_id"),
                "reason": child.get("error"),
            },
            commit=False,
        )
        self.append_run_trace_event(
            plan=plan,
            item_id=item_id,
            source="scheduler",
            event_type="child_cancelled",
            summary=f"{child.get('agent_role', 'general')} 子执行已取消",
            detail=child.get("error") or "",
            severity="warning",
            payload={
                "child_execution_id": child_execution_id,
                "agent_role": child.get("agent_role"),
                "agent_id": child.get("agent_id"),
            },
            commit=False,
        )
        self._commit_refresh(plan)
        return plan

    def merge_child_outputs(
        self,
        *,
        plan: Optional[PlanRunRecord],
        item_id: int,
    ) -> dict:
        active_item = self._get_active_item(plan, item_id=item_id)
        runtime_state = self.runtime_store.load_runtime(active_item) if active_item is not None else {}
        scheduler_run = dict((runtime_state or {}).get("scheduler_run") or {})
        children = list((runtime_state or {}).get("child_runs") or [])
        completed = [row for row in children if row.get("status") == "completed"]
        failed = [row for row in children if row.get("status") == "failed"]
        running = [row for row in children if row.get("status") in {"queued", "running"}]

        merged_sections = []
        for child in completed:
            merged_sections.append(
                f"[{child.get('agent_role', 'general')}] {str(child.get('summary') or '').strip()}".strip()
            )

        if failed:
            merged_sections.append(
                "未完成的子执行：" + "；".join(
                    f"{child.get('agent_role', 'general')}={str(child.get('error') or '执行失败').strip()}"
                    for child in failed
                )
            )

        merge_status = "completed"
        if failed and completed:
            merge_status = "partial_failed"
        elif failed and not completed:
            merge_status = "failed"
        elif running:
            merge_status = "incomplete"

        merged_output = "\n\n".join(section for section in merged_sections if section.strip()).strip()
        if active_item is not None and scheduler_run.get("run_id"):
            scheduler_run["merge_status"] = merge_status
            scheduler_run["merged_output"] = merged_output
            scheduler_run["last_merge_at"] = self._now_text()
            if merge_status in {"completed", "partial_failed"}:
                active_item.handoff_status = PlanHandoffStatus.MERGED
            self.runtime_store.save_runtime(active_item, scheduler_run=scheduler_run, child_runs=children)
            self.append_audit_event(
                plan=plan,
                item_id=item_id,
                event_type="scheduler_merged",
                content="调度器已完成子执行结果合并",
                payload={
                    "merge_status": merge_status,
                    "completed_children": len(completed),
                    "failed_children": len(failed),
                    "pending_children": len(running),
                },
                commit=False,
            )
            self.append_run_trace_event(
                plan=plan,
                item_id=item_id,
                source="scheduler",
                event_type="scheduler_merged",
                summary="调度器已完成结果合并",
                detail=merged_output,
                severity="success" if merge_status == "completed" else "warning",
                payload={
                    "merge_status": merge_status,
                    "completed_children": len(completed),
                    "failed_children": len(failed),
                    "pending_children": len(running),
                },
                commit=False,
            )
            self._commit_refresh(plan)

        return {
            "merge_status": merge_status,
            "merged_output": merged_output,
            "completed_children": len(completed),
            "failed_children": len(failed),
            "pending_children": len(running),
        }

    def serialize_child_executions(self, item: Optional[PlanItemRecord]) -> list[dict]:
        runtime_state = self.runtime_store.load_runtime(item)
        return [dict(child) for child in (runtime_state.get("child_runs") or [])]

    def get_audit_trail(self, item: Optional[PlanItemRecord]) -> list[dict]:
        return self.runtime_store.get_audit_trail(item)

    def get_run_trace(self, item: Optional[PlanItemRecord]) -> list[dict]:
        return self.runtime_store.get_run_trace(item)

    def get_approval_requests(self, item: Optional[PlanItemRecord]) -> list[dict]:
        return self.runtime_store.list_approval_requests(item)

    def get_background_runs(self, item: Optional[PlanItemRecord]) -> list[dict]:
        return self.runtime_store.list_background_runs(item)

    def get_worktree_runs(self, item: Optional[PlanItemRecord]) -> list[dict]:
        return self.runtime_store.list_worktree_runs(item)

    def get_scheduler_snapshot(self, item: Optional[PlanItemRecord]) -> dict:
        runtime_state = self.runtime_store.load_runtime(item)
        scheduler_run = dict(runtime_state.get("scheduler_run") or {})
        children = [dict(child) for child in (runtime_state.get("child_runs") or [])]
        counts = self._count_child_statuses(children)
        return {
            "scheduler_run_id": str(scheduler_run.get("run_id") or "").strip() or None,
            "merge_strategy": str(scheduler_run.get("merge_strategy") or "").strip() or None,
            "merge_status": str(scheduler_run.get("merge_status") or "").strip() or None,
            "merged_output": str(scheduler_run.get("merged_output") or "").strip() or None,
            "policy": dict(scheduler_run.get("policy") or {}),
            "child_count": len(children),
            "child_status_counts": counts,
            "active_children": counts.get("queued", 0) + counts.get("running", 0),
            "children": children,
        }

    def serialize_scheduler_run(self, item: Optional[PlanItemRecord]) -> dict:
        snapshot = self.get_scheduler_snapshot(item)
        merge_status = str(snapshot.get("merge_status") or "").strip().lower()
        active_children = int(snapshot.get("active_children") or 0)
        if active_children > 0:
            run_state = "running"
        elif merge_status == "completed":
            run_state = "completed"
        elif merge_status in {"partial_failed", "failed"}:
            run_state = "failed"
        elif merge_status == "incomplete":
            run_state = "incomplete"
        else:
            run_state = "pending"
        return {
            "run_id": snapshot.get("scheduler_run_id"),
            "parent_run_id": None,
            "run_kind": "scheduler",
            "state": run_state,
            "merge_strategy": snapshot.get("merge_strategy"),
            "merge_status": snapshot.get("merge_status"),
            "child_count": snapshot.get("child_count", 0),
            "active_children": active_children,
            "child_status_counts": dict(snapshot.get("child_status_counts") or {}),
            "policy": dict(snapshot.get("policy") or {}),
        }

    def get_runtime_persistence_descriptor(self) -> dict:
        return self.runtime_store.get_persistence_descriptor()

    def build_execution_context(
        self,
        *,
        plan: Optional[PlanRunRecord],
        item: Optional[PlanItemRecord],
        required_capabilities: Optional[list[str]] = None,
    ) -> Optional[dict]:
        if plan is None or item is None:
            return None
        scheduler_run = self.serialize_scheduler_run(item)
        if not scheduler_run.get("run_id"):
            return None
        capabilities = list(required_capabilities or self.runtime_store.get_required_capabilities(item))
        child_contexts = []
        for child in self.serialize_child_executions(item):
            child_contexts.append({
                "run_id": child.get("run_id"),
                "parent_run_id": child.get("parent_run_id") or scheduler_run.get("run_id"),
                "child_run_id": child.get("child_run_id") or child.get("child_execution_id"),
                "run_kind": child.get("run_kind") or "child",
                "execution_mode": "parallel",
                "plan_id": plan.id,
                "plan_item_id": item.id,
                "plan_item_title": item.title,
                "agent_role": child.get("agent_role"),
                "agent_id": child.get("agent_id"),
                "required_capabilities": list(capabilities),
                "handoff_status": "executing",
                "child_execution_id": child.get("child_execution_id"),
                "scheduler_run_id": scheduler_run.get("run_id"),
                "scheduler_policy": dict(scheduler_run.get("policy") or {}),
            })
        return {
            "run_id": scheduler_run.get("run_id"),
            "parent_run_id": scheduler_run.get("parent_run_id"),
            "run_kind": scheduler_run.get("run_kind"),
            "scheduler_mode": "fan_out",
            "scheduler_run_id": scheduler_run.get("run_id"),
            "merge_strategy": scheduler_run.get("merge_strategy"),
            "plan_id": plan.id,
            "plan_item_id": item.id,
            "plan_item_title": item.title,
            "agent_role": str(item.agent_role or "scheduler").strip() or "scheduler",
            "agent_id": item.agent_id,
            "required_capabilities": list(capabilities),
            "handoff_status": self._serialize_handoff_status(item.handoff_status),
            "child_contexts": child_contexts,
        }

    def get_merge_summary(self, item: Optional[PlanItemRecord]) -> dict:
        snapshot = self.get_scheduler_snapshot(item)
        return {
            "scheduler_run_id": snapshot["scheduler_run_id"],
            "merge_strategy": snapshot["merge_strategy"],
            "merge_status": snapshot["merge_status"],
            "merged_output": snapshot["merged_output"],
            "child_count": snapshot["child_count"],
            "policy": snapshot["policy"],
            "last_merge_at": (self.runtime_store.load_runtime(item).get("scheduler_run") or {}).get("last_merge_at"),
        }

    def append_audit_event(
        self,
        *,
        plan: Optional[PlanRunRecord],
        item_id: int,
        event_type: str,
        content: str,
        payload: Optional[dict] = None,
        commit: bool = True,
    ) -> Optional[PlanRunRecord]:
        active_item = self._get_active_item(plan, item_id=item_id)
        if active_item is None:
            return plan
        self.runtime_store.append_audit_trail(active_item, {
            "timestamp": self._now_text(),
            "event_type": str(event_type or "").strip() or "unknown",
            "content": str(content or "").strip(),
            "payload": dict(payload or {}),
        })
        if commit:
            self._commit_refresh(plan)
        return plan

    def append_run_trace_event(
        self,
        *,
        plan: Optional[PlanRunRecord],
        item_id: int,
        source: str,
        event_type: str,
        summary: str,
        detail: str = "",
        severity: str = "info",
        payload: Optional[dict] = None,
        execution_context: Optional[dict] = None,
        commit: bool = True,
    ) -> Optional[PlanRunRecord]:
        active_item = self._get_active_item(plan, item_id=item_id)
        if active_item is None:
            return plan
        payload_data = dict(payload or {})
        trace_scope = self._build_trace_scope(
            item=active_item,
            payload=payload_data,
            execution_context=execution_context,
        )
        merged_payload = dict(payload_data)
        for key, value in trace_scope.items():
            if key not in merged_payload and value is not None:
                merged_payload[key] = value
        self.runtime_store.append_run_trace(active_item, {
            "timestamp": self._now_text(),
            "run_id": trace_scope.get("run_id"),
            "parent_run_id": trace_scope.get("parent_run_id"),
            "child_run_id": trace_scope.get("child_run_id"),
            "run_kind": trace_scope.get("run_kind"),
            "scheduler_run_id": trace_scope.get("scheduler_run_id"),
            "plan_id": trace_scope.get("plan_id"),
            "plan_item_id": trace_scope.get("plan_item_id"),
            "agent_role": trace_scope.get("agent_role"),
            "agent_id": trace_scope.get("agent_id"),
            "source": str(source or "").strip() or "runtime",
            "event_type": str(event_type or "").strip() or "unknown",
            "severity": str(severity or "").strip() or "info",
            "summary": str(summary or "").strip(),
            "detail": str(detail or "").strip(),
            "payload": merged_payload,
        })
        self._persist_activity_attachment(
            item=active_item,
            source=source,
            event_type=event_type,
            trace_scope=trace_scope,
            payload=merged_payload,
        )
        if commit:
            self._commit_refresh(plan)
        return plan

    def get_execution_policy(self, item: Optional[PlanItemRecord]) -> dict:
        scheduler_run = self.runtime_store.load_runtime(item).get("scheduler_run") or {}
        return self._normalize_policy(scheduler_run.get("policy") or {})

    def filter_run_trace(
        self,
        item: Optional[PlanItemRecord],
        *,
        run_id: Optional[str] = None,
        child_run_id: Optional[str] = None,
        source: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[dict]:
        events = self.get_run_trace(item)
        filtered = []
        normalized_run_id = str(run_id or "").strip()
        normalized_child_run_id = str(child_run_id or "").strip()
        normalized_source = str(source or "").strip().lower()
        normalized_event_type = str(event_type or "").strip().lower()
        for entry in events:
            if normalized_run_id and str(entry.get("run_id") or "").strip() != normalized_run_id:
                continue
            if normalized_child_run_id and str(entry.get("child_run_id") or "").strip() != normalized_child_run_id:
                continue
            if normalized_source and str(entry.get("source") or "").strip().lower() != normalized_source:
                continue
            if normalized_event_type and str(entry.get("event_type") or "").strip().lower() != normalized_event_type:
                continue
            filtered.append(dict(entry))
        if limit is not None:
            try:
                normalized_limit = max(1, int(limit))
            except (TypeError, ValueError):
                normalized_limit = len(filtered)
            filtered = filtered[-normalized_limit:]
        return filtered

    def matches_runtime_scope(
        self,
        item: Optional[PlanItemRecord],
        *,
        run_id: Optional[str] = None,
        child_run_id: Optional[str] = None,
    ) -> bool:
        normalized_run_id = str(run_id or "").strip()
        normalized_child_run_id = str(child_run_id or "").strip()
        if not normalized_run_id and not normalized_child_run_id:
            return False
        scheduler_run = self.serialize_scheduler_run(item)
        if normalized_run_id and str(scheduler_run.get("run_id") or "").strip() == normalized_run_id:
            return True
        for child in self.serialize_child_executions(item):
            if normalized_run_id and str(child.get("run_id") or "").strip() == normalized_run_id:
                return True
            if normalized_child_run_id and str(child.get("child_run_id") or "").strip() == normalized_child_run_id:
                return True
        return False

    def build_run_trace_summary(self, events: Iterable[dict]) -> dict:
        source_counter = Counter()
        event_counter = Counter()
        severity_counter = Counter()
        latest_event = None
        for event in events or []:
            source_counter[str((event or {}).get("source") or "unknown")] += 1
            event_counter[str((event or {}).get("event_type") or "unknown")] += 1
            severity_counter[str((event or {}).get("severity") or "unknown")] += 1
            latest_event = dict(event)
        return {
            "total": sum(source_counter.values()),
            "by_source": dict(source_counter),
            "by_event_type": dict(event_counter),
            "by_severity": dict(severity_counter),
            "latest_event": latest_event,
        }

    def _resolve_child_roles(self, item: PlanItemRecord) -> list[str]:
        explicit = self._normalize_roles(self.runtime_store.get_child_roles(item))
        if len(explicit) > 1:
            return explicit

        text = " ".join(
            part
            for part in [str(getattr(item, "title", "") or ""), str(getattr(item, "details", "") or "")]
            if str(part).strip()
        ).lower()
        roles = self._normalize_roles(self.subagent_runtime_service.infer_roles_from_text(text))
        if len(roles) > 1:
            return roles

        legacy_roles = []
        if any(keyword in text for keyword in ["规划", "拆解", "plan", "todo", "方案"]):
            legacy_roles.append("planner")
        if any(keyword in text for keyword in ["后端", "api", "backend", "服务", "接口", "数据库"]):
            legacy_roles.append("backend")
        if any(keyword in text for keyword in ["前端", "ui", "vue", "frontend", "页面", "组件", "交互"]):
            legacy_roles.append("frontend")
        if any(keyword in text for keyword in ["测试", "qa", "回归", "验证", "smoke"]):
            legacy_roles.append("qa")
        if any(keyword in text for keyword in ["文档", "docs", "readme", "说明", "日志"]):
            legacy_roles.append("docs")

        roles = self._normalize_roles(legacy_roles)
        if len(roles) > 1:
            return roles

        fallback_role = str(item.agent_role or "").strip().lower()
        if fallback_role and fallback_role != "general":
            return [fallback_role]
        return roles

    def _normalize_roles(self, roles: Iterable[str]) -> list[str]:
        seen = []
        for role in roles:
            text = str(role or "").strip().lower()
            if text and text not in seen:
                seen.append(text)
        return sorted(seen, key=lambda value: ROLE_ORDER.index(value) if value in ROLE_ORDER else len(ROLE_ORDER))

    def _normalize_policy(self, policy: dict) -> dict:
        timeout_seconds = policy.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)
        max_retries = policy.get("max_retries", DEFAULT_MAX_RETRIES)
        cancel_on_failure = policy.get("cancel_on_failure", DEFAULT_CANCEL_ON_FAILURE)
        try:
            timeout_seconds = max(1, int(timeout_seconds))
        except (TypeError, ValueError):
            timeout_seconds = DEFAULT_TIMEOUT_SECONDS
        try:
            max_retries = max(0, int(max_retries))
        except (TypeError, ValueError):
            max_retries = DEFAULT_MAX_RETRIES
        return {
            "timeout_seconds": timeout_seconds,
            "max_retries": max_retries,
            "cancel_on_failure": bool(cancel_on_failure),
        }

    def _count_child_statuses(self, children: list[dict]) -> dict:
        counter = Counter()
        for child in children:
            status = str((child or {}).get("status") or "").strip().lower() or "unknown"
            counter[status] += 1
        return dict(counter)

    def _serialize_child_execution(self, child: Optional[dict], group: Optional[dict] = None) -> dict:
        data = dict(child or {})
        scheduler_run_id = str((group or {}).get("run_id") or "").strip() or None
        return {
            "child_execution_id": str(data.get("child_execution_id") or "").strip() or None,
            "child_run_id": str(data.get("child_run_id") or data.get("child_execution_id") or "").strip() or None,
            "run_id": str(data.get("run_id") or data.get("child_run_id") or data.get("child_execution_id") or "").strip() or None,
            "parent_run_id": str(data.get("parent_run_id") or scheduler_run_id or "").strip() or None,
            "run_kind": str(data.get("run_kind") or "child").strip() or "child",
            "scheduler_run_id": str(data.get("scheduler_run_id") or scheduler_run_id or "").strip() or None,
            "agent_role": str(data.get("agent_role") or "").strip() or None,
            "agent_id": str(data.get("agent_id") or "").strip() or None,
            "status": str(data.get("status") or "").strip() or "queued",
            "title": str(data.get("title") or "").strip() or None,
            "summary": str(data.get("summary") or "").strip() or None,
            "error": str(data.get("error") or "").strip() or None,
            "error_kind": str(data.get("error_kind") or "").strip() or None,
            "retry_count": max(0, int(data.get("retry_count") or 0)),
            "model_name": str(data.get("model_name") or "").strip() or None,
            "provider_name": str(data.get("provider_name") or "").strip() or None,
            "provider_order": list(data.get("provider_order") or []),
            "provider_switch_count": max(0, int(data.get("provider_switch_count") or 0)),
            "provider_history": [dict(entry) for entry in (data.get("provider_history") or []) if isinstance(entry, dict)],
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "started_at": data.get("started_at") or None,
            "completed_at": data.get("completed_at") or None,
            "cancelled_at": data.get("cancelled_at") or None,
        }

    def _get_child_group(self, item: Optional[PlanItemRecord]) -> Optional[dict]:
        return self.runtime_store.get_child_group(item)

    def _find_child(self, item: Optional[PlanItemRecord], child_execution_id: str) -> Optional[dict]:
        _group, child = self._get_child_runtime(item, child_execution_id)
        return child

    def _get_child_runtime(
        self,
        item: Optional[PlanItemRecord],
        child_execution_id: str,
    ) -> tuple[Optional[dict], Optional[dict]]:
        child = self.runtime_store.get_child_run(item, child_execution_id)
        if child is None:
            return None, None
        group = self.runtime_store.get_child_group(item)
        if group is None:
            return None, None
        children = []
        target_id = str(child_execution_id or "").strip()
        for entry in group.get("children") or []:
            if not isinstance(entry, dict):
                continue
            entry_copy = dict(entry)
            children.append(entry_copy)
            if str(entry_copy.get("child_execution_id") or "").strip() == target_id:
                child = entry_copy
        group["children"] = children
        return group, child

    def _get_active_item(
        self,
        plan: Optional[PlanRunRecord],
        *,
        item_id: Optional[int] = None,
    ) -> Optional[PlanItemRecord]:
        if plan is None:
            return None
        if item_id is not None:
            return next((item for item in plan.items if item.id == item_id), None)
        active = next((item for item in plan.items if str(getattr(item.status, "value", item.status)) == "in_progress"), None)
        if active is not None:
            return active
        if getattr(plan, "active_item_id", None) is not None:
            return next((item for item in plan.items if item.id == plan.active_item_id), None)
        return None

    def _build_scheduler_agent_id(self, *, plan: PlanRunRecord, item: PlanItemRecord) -> str:
        return f"scheduler-p{plan.id}-i{item.id}"

    def _build_scheduler_run_id(self, *, plan: PlanRunRecord, item: PlanItemRecord) -> str:
        return f"sched-p{plan.id}-i{item.id}"

    def _build_child_execution_id(self, *, plan: PlanRunRecord, item: PlanItemRecord, index: int, role: str) -> str:
        return f"{role}-child-p{plan.id}-i{item.id}-c{index}"

    def _build_child_agent_id(self, *, plan: PlanRunRecord, item: PlanItemRecord, index: int, role: str) -> str:
        return f"{role}-agent-p{plan.id}-i{item.id}-c{index}"

    def _commit_refresh(self, plan: Optional[PlanRunRecord]) -> None:
        if self.db is None:
            return
        commit = getattr(self.db, "commit", None)
        if callable(commit):
            commit()
        refresh = getattr(self.db, "refresh", None)
        if callable(refresh) and plan is not None:
            refresh(plan)

    def _now_text(self) -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    def _serialize_handoff_status(self, handoff_status: object) -> str:
        return handoff_status.value if hasattr(handoff_status, "value") else str(handoff_status)

    def _build_trace_scope(
        self,
        *,
        item: PlanItemRecord,
        payload: Optional[dict] = None,
        execution_context: Optional[dict] = None,
    ) -> dict:
        payload_data = dict(payload or {})
        context = dict(execution_context or {})
        group = self.runtime_store.get_child_group(item) or {}
        scheduler_run_id = str(
            payload_data.get("scheduler_run_id")
            or context.get("scheduler_run_id")
            or group.get("run_id")
            or ""
        ).strip() or None
        child_run_id = str(
            payload_data.get("child_run_id")
            or context.get("child_run_id")
            or payload_data.get("child_execution_id")
            or context.get("child_execution_id")
            or ""
        ).strip() or None
        run_id = str(
            payload_data.get("run_id")
            or context.get("run_id")
            or child_run_id
            or scheduler_run_id
            or ""
        ).strip() or None
        parent_run_id = str(
            payload_data.get("parent_run_id")
            or context.get("parent_run_id")
            or (scheduler_run_id if child_run_id else "")
        ).strip() or None
        run_kind = str(
            payload_data.get("run_kind")
            or context.get("run_kind")
            or ("child" if child_run_id else "scheduler")
        ).strip() or ("child" if child_run_id else "scheduler")
        return {
            "run_id": run_id,
            "parent_run_id": parent_run_id,
            "child_run_id": child_run_id,
            "run_kind": run_kind,
            "scheduler_run_id": scheduler_run_id,
            "plan_id": payload_data.get("plan_id") or context.get("plan_id") or getattr(item, "plan_id", None),
            "plan_item_id": payload_data.get("plan_item_id") or context.get("plan_item_id") or getattr(item, "id", None),
            "agent_role": payload_data.get("agent_role") or context.get("agent_role") or getattr(item, "agent_role", None),
            "agent_id": payload_data.get("agent_id") or context.get("agent_id") or getattr(item, "agent_id", None),
        }

    def _persist_activity_attachment(
        self,
        *,
        item: Optional[PlanItemRecord],
        source: str,
        event_type: str,
        trace_scope: dict,
        payload: dict,
    ) -> None:
        if item is None:
            return
        normalized_source = str(source or "").strip().lower()
        normalized_event_type = str(event_type or "").strip().lower()
        attachment = {
            "run_id": trace_scope.get("run_id"),
            "parent_run_id": trace_scope.get("parent_run_id"),
            "scheduler_run_id": trace_scope.get("scheduler_run_id"),
            "status": str(payload.get("status") or "").strip() or None,
            "source": source,
            "event_type": event_type,
            "detail": str(payload.get("detail") or "").strip() or str(payload.get("summary") or "").strip(),
            "metadata": dict(payload or {}),
        }
        if normalized_source == "background" or "background" in normalized_event_type or trace_scope.get("run_kind") == "background":
            attachment["background_run_id"] = (
                str(payload.get("background_run_id") or payload.get("run_id") or trace_scope.get("run_id") or "").strip()
            )
            attachment["title"] = str(payload.get("title") or payload.get("summary") or "").strip() or None
            attachment["artifact_id"] = str(payload.get("artifact_id") or "").strip() or None
            attachment["artifact_kind"] = str(payload.get("artifact_kind") or "").strip() or None
            self.runtime_store.record_background_run(item, attachment)
            return
        if normalized_source == "worktree" or "worktree" in normalized_event_type:
            attachment["worktree_run_id"] = (
                str(payload.get("worktree_run_id") or payload.get("run_id") or trace_scope.get("run_id") or "").strip()
            )
            attachment["workspace_path"] = str(payload.get("workspace_path") or payload.get("worktree_path") or "").strip() or None
            attachment["branch_name"] = str(payload.get("branch_name") or "").strip() or None
            self.runtime_store.record_worktree_run(item, attachment)


_scheduler_service = None


def get_scheduler_service(db) -> SchedulerService:
    return SchedulerService(db)
