"""Record recovery operation evidence into runtime trace."""

from __future__ import annotations

from typing import Any, Callable, Mapping

try:
    from services.run_trace_service import get_run_trace_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.run_trace_service import get_run_trace_service


RECOVERY_AUDIT_TRACE_SOURCE = "recovery_audit"
RECOVERY_AUDIT_TRACE_EVENT_TYPE = "recovery_operation_recorded"


class RecoveryAuditTimelineService:
    """Opt-in writer for compact recovery operation trace evidence."""

    def __init__(self, db: Any = None, *, trace_service_factory: Callable[[Any], Any] = get_run_trace_service):
        self.db = db
        self.trace_service_factory = trace_service_factory

    def record_operation(
        self,
        *,
        operation: Mapping[str, Any],
        user_id: int | None = None,
        conversation_id: int | None = None,
        run_id: str | None = None,
        db: Any = None,
    ) -> dict[str, Any]:
        payload = self._build_payload(operation=operation, run_id=run_id)
        dedupe_key = payload["dedupe_key"]
        effective_db = self.db if db is None else db
        trace_service = self.trace_service_factory(effective_db)
        has_dedupe_key = getattr(trace_service, "has_runtime_trace_dedupe_key", None)
        if callable(has_dedupe_key) and has_dedupe_key(
            user_id=user_id,
            conversation_id=conversation_id,
            run_id=payload["run_id"],
            source=RECOVERY_AUDIT_TRACE_SOURCE,
            event_type=RECOVERY_AUDIT_TRACE_EVENT_TYPE,
            dedupe_key=dedupe_key,
        ):
            return {
                "trace_written": False,
                "dedupe_source": "persisted_trace",
                "dedupe_key": dedupe_key,
                "operation_id": payload["operation_id"],
            }

        append_trace = getattr(trace_service, "append_runtime_trace", None)
        if not callable(append_trace):
            return {
                "trace_written": False,
                "reason": "trace_service_unavailable",
                "dedupe_key": dedupe_key,
                "operation_id": payload["operation_id"],
            }

        trace_written = bool(append_trace(
            user_id=user_id,
            conversation_id=conversation_id,
            run_id=payload["run_id"],
            source=RECOVERY_AUDIT_TRACE_SOURCE,
            event_type=RECOVERY_AUDIT_TRACE_EVENT_TYPE,
            summary=self._build_summary(payload),
            detail=self._build_detail(payload),
            severity=self._severity_for_status(payload["operation_status"]),
            payload=payload,
        ))
        return {
            "trace_written": trace_written,
            "dedupe_key": dedupe_key,
            "operation_id": payload["operation_id"],
        }

    def _build_payload(self, *, operation: Mapping[str, Any], run_id: str | None = None) -> dict[str, Any]:
        operation_dict = dict(operation or {})
        retry = operation_dict.get("retry") if isinstance(operation_dict.get("retry"), Mapping) else {}
        worker_ownership = (
            operation_dict.get("worker_ownership")
            if isinstance(operation_dict.get("worker_ownership"), Mapping)
            else {}
        )
        normalized_run_id = str(run_id or operation_dict.get("run_id") or "").strip()
        operation_id = str(operation_dict.get("operation_id") or "").strip()
        entrypoint = str(operation_dict.get("entrypoint") or "").strip()
        operation_status = str(operation_dict.get("operation_status") or "").strip()
        recovery_reason = str(operation_dict.get("recovery_reason") or "").strip()
        payload = {
            "contract_version": "phase-ii-recovery-audit-trace-v1",
            "source": RECOVERY_AUDIT_TRACE_SOURCE,
            "operation_id": operation_id,
            "run_id": normalized_run_id,
            "entrypoint": entrypoint,
            "operation_status": operation_status,
            "recovery_reason": recovery_reason,
            "blocked_reason": str(operation_dict.get("blocked_reason") or "").strip(),
            "retry_status": str(retry.get("status") or "").strip(),
            "retry_attempt_number": int(retry.get("attempt_number") or 0),
            "retry_max_attempts": int(retry.get("max_attempts") or 0),
            "ownership_implemented": bool(worker_ownership.get("implemented")),
            "ownership_status": str(worker_ownership.get("lease_status") or "").strip(),
            "recorded_at": str(operation_dict.get("recorded_at") or "").strip(),
        }
        payload["dedupe_key"] = self._build_dedupe_key(payload)
        return payload

    def _build_dedupe_key(self, payload: Mapping[str, Any]) -> str:
        run_id = str(payload.get("run_id") or "unknown_run").strip() or "unknown_run"
        operation_id = str(payload.get("operation_id") or "").strip()
        if operation_id:
            return self._join_dedupe_parts(["recovery_audit", run_id, operation_id])
        return self._join_dedupe_parts([
            "recovery_audit",
            run_id,
            str(payload.get("entrypoint") or "unknown_entrypoint"),
            str(payload.get("operation_status") or "unknown_status"),
            str(payload.get("recovery_reason") or payload.get("blocked_reason") or ""),
        ])

    @staticmethod
    def _join_dedupe_parts(parts: list[str]) -> str:
        return ":".join(str(part or "").replace(":", "_") for part in parts)

    def _build_summary(self, payload: Mapping[str, Any]) -> str:
        status = str(payload.get("operation_status") or "unknown").strip() or "unknown"
        entrypoint = str(payload.get("entrypoint") or "unknown_entrypoint").strip() or "unknown_entrypoint"
        return f"Recovery operation {status}: {entrypoint}"

    def _build_detail(self, payload: Mapping[str, Any]) -> str:
        parts = [
            f"operation_status={payload.get('operation_status') or ''}",
            f"recovery_reason={payload.get('recovery_reason') or ''}",
        ]
        retry_status = str(payload.get("retry_status") or "").strip()
        ownership_status = str(payload.get("ownership_status") or "").strip()
        if retry_status:
            parts.append(f"retry_status={retry_status}")
        if ownership_status:
            parts.append(f"ownership_status={ownership_status}")
        return " / ".join(part for part in parts if part)

    def _severity_for_status(self, operation_status: str) -> str:
        if operation_status in {"blocked", "failed"}:
            return "warning"
        return "info"


def get_recovery_audit_timeline_service(db: Any = None) -> RecoveryAuditTimelineService:
    return RecoveryAuditTimelineService(db)
