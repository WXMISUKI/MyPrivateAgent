"""Deterministic local trial for scheduler fan-out / collect / merge."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

try:
    from models import PlanHandoffStatus, PlanStatus
    from services.scheduler_service import SchedulerService
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.models import PlanHandoffStatus, PlanStatus
    from backend.services.scheduler_service import SchedulerService


TRIAL_CONTRACT_VERSION = "scheduler-fanout-local-trial-v1"
DEFAULT_OBJECTIVE = "验证 Scheduler fan-out 本地最小调度闭环"
DEFAULT_ITEM_TITLE = "完成前后端联调、回归测试和说明文档"
DEFAULT_ITEM_DETAILS = "需要同时处理后端接口、前端联动、回归验证和文档说明。"
DEFAULT_CHILD_ROLES = ("backend", "frontend", "qa", "docs")
DEFAULT_MODE = "success"
SUPPORTED_MODES = {"success", "partial_failure", "blocked"}


@dataclass(frozen=True)
class SchedulerFanoutLocalTrialReport:
    contract_version: str
    generated_at: str
    decision: str
    reason_code: str
    recommended_next_action: str
    mode: str
    objective: str
    item_title: str
    requested_child_roles: list[str]
    scheduler: dict[str, Any] = field(default_factory=dict)
    children: list[dict[str, Any]] = field(default_factory=list)
    merge: dict[str, Any] = field(default_factory=dict)
    blockers: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    boundary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SchedulerFanoutLocalTrialService:
    """Run a local deterministic scheduler trial without real worker dispatch."""

    def __init__(self, scheduler_service: SchedulerService | None = None):
        self.scheduler_service = scheduler_service or SchedulerService(db=None)

    def run_trial(
        self,
        *,
        mode: str = DEFAULT_MODE,
        objective: str = DEFAULT_OBJECTIVE,
        item_title: str = DEFAULT_ITEM_TITLE,
        item_details: str = DEFAULT_ITEM_DETAILS,
        child_roles: list[str] | tuple[str, ...] = DEFAULT_CHILD_ROLES,
        failed_role: str = "frontend",
    ) -> SchedulerFanoutLocalTrialReport:
        normalized_mode = _normalize_mode(mode)
        roles = _normalize_roles(child_roles)
        if normalized_mode == "blocked":
            roles = roles[:1] or ["backend"]
            item_title = "本地单一调度步骤"
            item_details = "仅用于验证 fan-out blocked path。"
        plan, item = _build_local_plan(
            objective=objective,
            item_title=item_title,
            item_details=item_details,
            child_roles=roles,
        )
        try:
            prepared = self.scheduler_service.prepare_execution(plan=plan, item=item)
            if not prepared:
                return _blocked_report(
                    mode=normalized_mode,
                    objective=objective,
                    item_title=item_title,
                    requested_child_roles=roles,
                    reason_code="scheduler_fanout_not_prepared",
                    blocker=_issue("scheduler", "scheduler_fanout_not_prepared"),
                )

            execution_context = dict(prepared.get("execution_context") or {})
            child_contexts = list(execution_context.get("child_contexts") or [])
            if len(child_contexts) < 2:
                return _blocked_report(
                    mode=normalized_mode,
                    objective=objective,
                    item_title=item_title,
                    requested_child_roles=roles,
                    reason_code="scheduler_fanout_insufficient_children",
                    blocker=_issue("scheduler", "scheduler_fanout_insufficient_children"),
                )

            failed_child_id = _select_failed_child_id(child_contexts, failed_role) if normalized_mode == "partial_failure" else ""
            for child in child_contexts:
                child_id = str(child.get("child_execution_id") or "").strip()
                if not child_id:
                    return _blocked_report(
                        mode=normalized_mode,
                        objective=objective,
                        item_title=item_title,
                        requested_child_roles=roles,
                        reason_code="scheduler_child_id_missing",
                        blocker=_issue("scheduler", "scheduler_child_id_missing"),
                    )
                self.scheduler_service.mark_child_running(
                    plan=plan,
                    item_id=item.id,
                    child_execution_id=child_id,
                )
                if child_id == failed_child_id:
                    self.scheduler_service.mark_child_failed(
                        plan=plan,
                        item_id=item.id,
                        child_execution_id=child_id,
                        error_text=f"{child.get('agent_role') or 'child'} deterministic failure",
                        error_kind="local_trial_failure",
                    )
                else:
                    self.scheduler_service.mark_child_completed(
                        plan=plan,
                        item_id=item.id,
                        child_execution_id=child_id,
                        output_text=f"{child.get('agent_role') or 'child'} deterministic output ready",
                    )

            merge = self.scheduler_service.merge_child_outputs(plan=plan, item_id=item.id)
            scheduler = self.scheduler_service.serialize_scheduler_run(item)
            children = self.scheduler_service.serialize_child_executions(item)
            return _build_report(
                mode=normalized_mode,
                objective=objective,
                item_title=item_title,
                requested_child_roles=roles,
                scheduler=scheduler,
                children=children,
                merge=merge,
            )
        except Exception as exc:  # pragma: no cover - defensive local trial guard
            return _blocked_report(
                mode=normalized_mode,
                objective=objective,
                item_title=item_title,
                requested_child_roles=roles,
                reason_code="scheduler_fanout_local_trial_failed",
                blocker=_issue("scheduler", "scheduler_fanout_local_trial_failed", message=str(exc)),
            )


def _build_report(
    *,
    mode: str,
    objective: str,
    item_title: str,
    requested_child_roles: list[str],
    scheduler: dict[str, Any],
    children: list[dict[str, Any]],
    merge: dict[str, Any],
) -> SchedulerFanoutLocalTrialReport:
    merge_status = str(merge.get("merge_status") or scheduler.get("merge_status") or "").strip()
    merged_output = str(merge.get("merged_output") or scheduler.get("merged_output") or "").strip()
    child_statuses = {str(child.get("status") or "").strip() for child in children}
    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    if not scheduler.get("scheduler_run_id"):
        blockers.append(_issue("scheduler", "scheduler_run_id_missing"))
    if any(not child.get("child_run_id") for child in children):
        blockers.append(_issue("scheduler", "child_run_id_missing"))
    if not merged_output:
        blockers.append(_issue("scheduler", "merged_output_missing"))

    if blockers:
        decision = "blocked"
        reason_code = blockers[0]["reason_code"]
    elif merge_status == "completed" and child_statuses == {"completed"}:
        decision = "go"
        reason_code = "scheduler_fanout_local_trial_ready"
    elif merge_status in {"partial_failed", "incomplete"}:
        decision = "review"
        reason_code = f"scheduler_fanout_merge_{merge_status}"
        warnings.append(_issue("scheduler", reason_code, status="review"))
    else:
        decision = "blocked"
        reason_code = "scheduler_fanout_unexpected_merge_status"
        blockers.append(_issue("scheduler", reason_code))

    return SchedulerFanoutLocalTrialReport(
        contract_version=TRIAL_CONTRACT_VERSION,
        generated_at=datetime.now(UTC).isoformat(),
        decision=decision,
        reason_code=reason_code,
        recommended_next_action=_next_action(decision),
        mode=mode,
        objective=objective,
        item_title=item_title,
        requested_child_roles=requested_child_roles,
        scheduler={
            "scheduler_run_id": scheduler.get("scheduler_run_id") or scheduler.get("run_id"),
            "run_id": scheduler.get("run_id"),
            "merge_strategy": scheduler.get("merge_strategy"),
            "merge_status": merge_status,
            "child_count": len(children),
            "child_status_counts": _count_statuses(children),
        },
        children=[
            {
                "child_execution_id": child.get("child_execution_id"),
                "child_run_id": child.get("child_run_id"),
                "child_display_id": child.get("child_display_id"),
                "run_id": child.get("run_id"),
                "parent_run_id": child.get("parent_run_id"),
                "scheduler_run_id": child.get("scheduler_run_id"),
                "agent_role": child.get("agent_role"),
                "agent_id": child.get("agent_id"),
                "status": child.get("status"),
                "summary": child.get("summary") or "",
                "error": child.get("error") or "",
                "error_kind": child.get("error_kind") or "",
            }
            for child in children
        ],
        merge={
            "merge_status": merge_status,
            "merged_output": merged_output,
            "merge_strategy": merge.get("merge_strategy") or scheduler.get("merge_strategy"),
        },
        blockers=blockers,
        warnings=warnings,
        boundary=_boundary(),
    )


def _blocked_report(
    *,
    mode: str,
    objective: str,
    item_title: str,
    requested_child_roles: list[str],
    reason_code: str,
    blocker: dict[str, Any],
) -> SchedulerFanoutLocalTrialReport:
    return SchedulerFanoutLocalTrialReport(
        contract_version=TRIAL_CONTRACT_VERSION,
        generated_at=datetime.now(UTC).isoformat(),
        decision="blocked",
        reason_code=reason_code,
        recommended_next_action=_next_action("blocked"),
        mode=mode,
        objective=objective,
        item_title=item_title,
        requested_child_roles=requested_child_roles,
        blockers=[blocker],
        boundary=_boundary(),
    )


def _build_local_plan(
    *,
    objective: str,
    item_title: str,
    item_details: str,
    child_roles: list[str],
):
    item = SimpleNamespace(
        id=11,
        plan_id=1,
        step_order=1,
        title=item_title,
        details=item_details,
        status=PlanStatus.IN_PROGRESS,
        owner="local-trial",
        agent_role="planner",
        agent_id=None,
        handoff_status=PlanHandoffStatus.READY,
        item_metadata={
            "required_capabilities": ["scheduler.local_trial"],
            "child_roles": child_roles,
        },
    )
    plan = SimpleNamespace(
        id=1,
        active_item_id=item.id,
        objective=objective,
        items=[item],
    )
    return plan, item


def _normalize_mode(mode: str) -> str:
    text = str(mode or DEFAULT_MODE).strip().lower().replace("-", "_")
    return text if text in SUPPORTED_MODES else DEFAULT_MODE


def _normalize_roles(roles: list[str] | tuple[str, ...]) -> list[str]:
    normalized: list[str] = []
    for role in roles or []:
        text = str(role or "").strip().lower()
        if text and text not in normalized:
            normalized.append(text)
    return normalized or list(DEFAULT_CHILD_ROLES)


def _select_failed_child_id(children: list[dict[str, Any]], failed_role: str) -> str:
    normalized_role = str(failed_role or "").strip().lower()
    for child in children:
        if str(child.get("agent_role") or "").strip().lower() == normalized_role:
            return str(child.get("child_execution_id") or "").strip()
    return str((children[1] if len(children) > 1 else children[0]).get("child_execution_id") or "").strip()


def _count_statuses(children: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for child in children:
        status = str(child.get("status") or "").strip() or "unknown"
        counts[status] = counts.get(status, 0) + 1
    return counts


def _next_action(decision: str) -> str:
    if decision == "go":
        return "use_scheduler_trial_as_phase_a_runtime_core_baseline"
    if decision == "review":
        return "review_partial_failure_merge_before_real_dispatch_promotion"
    return "fix_scheduler_fanout_trial_before_runtime_core_promotion"


def _boundary() -> dict[str, Any]:
    return {
        "real_child_executor_dispatch": "not_performed",
        "worker_startup": "not_performed",
        "sandbox_backend_invocation": "not_performed",
        "retry_scheduler": "not_performed",
        "llm_invocation": "not_performed",
        "chat_invocation": "not_performed",
        "default_runtime_behavior_changed": False,
        "frontend_ui_changed": False,
    }


def _issue(
    component: str,
    reason_code: str,
    *,
    status: str = "blocked",
    message: str | None = None,
) -> dict[str, Any]:
    issue = {"component": component, "status": status, "reason_code": reason_code}
    if message:
        issue["message"] = message
    return issue
