"""Approval engine service for creating formal runtime approval objects."""

from __future__ import annotations

from typing import Any, Dict, Optional

try:
    from services.scheduler_runtime_entities import ApprovalRequestState
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.scheduler_runtime_entities import ApprovalRequestState


class ApprovalEngineService:
    """Build formal approval runtime state records from governance decisions."""

    def create_tool_approval_request(
        self,
        *,
        request_id: str,
        tool_name: str,
        tool_args: Optional[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
        permission_level: str = "ask",
        reason: str = "",
        reason_code: Optional[str] = None,
        requested_at: Optional[str] = None,
        request_metadata: Optional[Dict[str, Any]] = None,
    ) -> ApprovalRequestState:
        runtime_context = dict(context or {})
        child_run_id = runtime_context.get("child_run_id")
        child_display_id = runtime_context.get("child_display_id") or child_run_id
        return ApprovalRequestState(
            request_id=str(request_id or "").strip() or None,
            request_kind="tool_permission",
            tool_name=str(tool_name or "").strip() or None,
            permission_level=str(permission_level or "").strip() or "ask",
            status="pending",
            user_id=runtime_context.get("user_id"),
            conversation_id=runtime_context.get("conversation_id"),
            plan_id=runtime_context.get("plan_id"),
            plan_item_id=runtime_context.get("plan_item_id"),
            result=None,
            requested_at=requested_at,
            completed_at=None,
            run_id=runtime_context.get("run_id"),
            parent_run_id=runtime_context.get("parent_run_id"),
            child_run_id=child_run_id,
            child_display_id=child_display_id,
            scheduler_run_id=runtime_context.get("scheduler_run_id"),
            run_kind=runtime_context.get("run_kind"),
            source_event_type=runtime_context.get("source_event_type") or "tool_permission_required",
            requires_approval=True,
            reason_code=str(reason_code or "").strip() or None,
            reason=str(reason or "").strip() or None,
            requested_by_role=runtime_context.get("agent_role"),
            requested_by_agent_id=runtime_context.get("agent_id"),
            tool_args=dict(tool_args or {}),
            request_metadata=dict(request_metadata or {}),
        )

    def submit_approval_decision(
        self,
        approval: ApprovalRequestState,
        decision: str,
        *,
        completed_at: Optional[str] = None,
    ) -> Dict[str, str]:
        normalized_decision = self._normalize_approval_decision(decision)
        original_decision = str(approval.status or "").strip().lower() or "pending"

        if original_decision in {"approved", "denied"}:
            submission_status = "replayed" if original_decision == normalized_decision else "ignored"
            return {
                "status": submission_status,
                "reason": "approval_already_resolved",
                "event_status_kind": f"approval_{submission_status}",
                "original_decision": original_decision,
                "attempted_decision": normalized_decision,
            }

        approval.status = normalized_decision
        approval.result = normalized_decision
        approval.completed_at = completed_at
        approval.requires_approval = False
        return {
            "status": "accepted",
            "reason": "approval_resolved",
            "event_status_kind": "approval_resolved",
            "original_decision": original_decision,
            "attempted_decision": normalized_decision,
        }

    @staticmethod
    def _normalize_approval_decision(value: Any) -> str:
        normalized = str(value or "").strip().lower()
        alias_map = {
            "approve": "approved",
            "approved": "approved",
            "allow": "approved",
            "deny": "denied",
            "denied": "denied",
            "reject": "denied",
            "rejected": "denied",
        }
        if normalized not in alias_map:
            raise ValueError("approval decision must be approved or denied.")
        return alias_map[normalized]


_approval_engine_service: Optional[ApprovalEngineService] = None


def get_approval_engine_service() -> ApprovalEngineService:
    global _approval_engine_service
    if _approval_engine_service is None:
        _approval_engine_service = ApprovalEngineService()
    return _approval_engine_service
