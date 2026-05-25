"""Record Embedded SDK approval lifecycle evidence into runtime trace."""

from __future__ import annotations

from typing import Any, Callable, Mapping

try:
    from services.run_trace_service import get_run_trace_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.run_trace_service import get_run_trace_service


SDK_APPROVAL_LIFECYCLE_TRACE_EVENT_TYPE = "sdk_approval_lifecycle"
SDK_APPROVAL_LIFECYCLE_TRACE_SOURCE = "embedded_sdk"
SDK_APPROVAL_LIFECYCLE_STATUS_KINDS = {
    "approval_resolved",
    "approval_replayed",
    "approval_ignored",
    "recovery_failed_closed",
}


class SdkApprovalLifecycleTimelineService:
    """Mirror selected Embedded SDK approval lifecycle events to governance trace."""

    def __init__(self, db: Any = None, *, trace_service_factory: Callable[[Any], Any] = get_run_trace_service):
        self.db = db
        self.trace_service_factory = trace_service_factory

    def record_event(self, *, run_context: Any, event: Mapping[str, Any]) -> dict[str, Any]:
        status_kind = str(event.get("status_kind") or "").strip()
        if status_kind not in SDK_APPROVAL_LIFECYCLE_STATUS_KINDS:
            return {"trace_written": False, "reason": "status_kind_not_tracked", "status_kind": status_kind}

        payload = self._build_payload(run_context=run_context, event=event)
        dedupe_key = payload["dedupe_key"]
        trace_service = self.trace_service_factory(self.db)
        has_dedupe_key = getattr(trace_service, "has_runtime_trace_dedupe_key", None)
        if callable(has_dedupe_key) and has_dedupe_key(
            user_id=getattr(run_context, "user_id", None),
            conversation_id=getattr(run_context, "conversation_id", None),
            run_id=getattr(run_context, "run_id", None),
            source=SDK_APPROVAL_LIFECYCLE_TRACE_SOURCE,
            event_type=SDK_APPROVAL_LIFECYCLE_TRACE_EVENT_TYPE,
            dedupe_key=dedupe_key,
        ):
            return {
                "trace_written": False,
                "dedupe_source": "persisted_trace",
                "dedupe_key": dedupe_key,
                "status_kind": status_kind,
            }

        append_trace = getattr(trace_service, "append_runtime_trace", None)
        if not callable(append_trace):
            return {"trace_written": False, "reason": "trace_service_unavailable", "dedupe_key": dedupe_key}

        trace_written = bool(append_trace(
            user_id=getattr(run_context, "user_id", None),
            conversation_id=getattr(run_context, "conversation_id", None),
            run_id=getattr(run_context, "run_id", None),
            source=SDK_APPROVAL_LIFECYCLE_TRACE_SOURCE,
            event_type=SDK_APPROVAL_LIFECYCLE_TRACE_EVENT_TYPE,
            summary=str(event.get("summary") or f"Embedded SDK {status_kind}"),
            detail=self._build_detail(payload),
            severity=self._severity_for_status(status_kind),
            payload=payload,
        ))
        return {
            "trace_written": trace_written,
            "dedupe_key": dedupe_key,
            "status_kind": status_kind,
        }

    def _build_payload(self, *, run_context: Any, event: Mapping[str, Any]) -> dict[str, Any]:
        status_kind = str(event.get("status_kind") or "").strip()
        approval_request = event.get("approval_request") if isinstance(event.get("approval_request"), Mapping) else {}
        approval_submission = (
            event.get("approval_submission")
            if isinstance(event.get("approval_submission"), Mapping)
            else {}
        )
        recovery = event.get("recovery") if isinstance(event.get("recovery"), Mapping) else {}
        recovery_reason = str(
            recovery.get("reason")
            or recovery.get("recovery_reason")
            or event.get("recovery_reason")
            or ""
        ).strip()
        blocked_reason = str(
            recovery.get("blocked_reason")
            or event.get("blocked_reason")
            or recovery_reason
            or ""
        ).strip()
        decision = str(
            event.get("decision")
            or approval_submission.get("attempted_decision")
            or approval_submission.get("decision")
            or approval_request.get("result")
            or ""
        ).strip()
        approval_request_id = str(
            event.get("approval_request_id")
            or approval_request.get("request_id")
            or recovery.get("request_id")
            or ""
        ).strip()
        payload = {
            "contract_version": "phase-ii-sdk-approval-lifecycle-trace-v1",
            "source": SDK_APPROVAL_LIFECYCLE_TRACE_SOURCE,
            "status_kind": status_kind,
            "run_id": str(getattr(run_context, "run_id", "") or "").strip(),
            "conversation_id": getattr(run_context, "conversation_id", None),
            "user_id": getattr(run_context, "user_id", None),
            "approval_request_id": approval_request_id,
            "decision": decision,
            "approval_status": str(approval_request.get("status") or "").strip(),
            "original_decision": str(event.get("original_decision") or approval_submission.get("original_decision") or "").strip(),
            "attempted_decision": str(event.get("attempted_decision") or approval_submission.get("attempted_decision") or "").strip(),
            "submission_status": str(approval_submission.get("status") or "").strip(),
            "recovery_reason": recovery_reason,
            "blocked_reason": blocked_reason,
        }
        payload["dedupe_key"] = self._build_dedupe_key(payload)
        return payload

    def _build_dedupe_key(self, payload: Mapping[str, Any]) -> str:
        parts = [
            "sdk_approval_lifecycle",
            str(payload.get("run_id") or "unknown_run"),
            str(payload.get("approval_request_id") or "unknown_approval"),
            str(payload.get("status_kind") or "unknown_status"),
            str(payload.get("decision") or payload.get("attempted_decision") or ""),
            str(payload.get("recovery_reason") or payload.get("blocked_reason") or ""),
        ]
        return ":".join(part.replace(":", "_") for part in parts)

    def _build_detail(self, payload: Mapping[str, Any]) -> str:
        status_kind = str(payload.get("status_kind") or "").strip() or "unknown"
        decision = str(payload.get("decision") or payload.get("attempted_decision") or "").strip()
        recovery_reason = str(payload.get("recovery_reason") or "").strip()
        parts = [f"status={status_kind}"]
        if decision:
            parts.append(f"decision={decision}")
        if recovery_reason:
            parts.append(f"recovery_reason={recovery_reason}")
        return " / ".join(parts)

    def _severity_for_status(self, status_kind: str) -> str:
        if status_kind == "recovery_failed_closed":
            return "warning"
        return "info"


def get_sdk_approval_lifecycle_timeline_service(db: Any = None) -> SdkApprovalLifecycleTimelineService:
    return SdkApprovalLifecycleTimelineService(db)
