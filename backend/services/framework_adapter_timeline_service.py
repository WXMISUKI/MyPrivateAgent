"""Trace and audit recording helpers for framework adapter runtime actions."""

from __future__ import annotations

from typing import Any, Callable, Dict, Mapping, Optional, Sequence

try:
    from services.chat_service import _build_run_trace_from_runtime_event
    from services.run_trace_service import get_run_trace_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.chat_service import _build_run_trace_from_runtime_event
    from backend.services.run_trace_service import get_run_trace_service


class FrameworkAdapterTimelineRecorder:
    """Record framework adapter runtime outcomes through platform trace/audit."""

    def __init__(self, *, trace_service_factory: Callable[[Any], Any] = get_run_trace_service):
        self.trace_service_factory = trace_service_factory

    def append_adapter_run(
        self,
        *,
        db: Any,
        user_id: Optional[int],
        conversation_id: Optional[int],
        adapter: Any,
        run_id: str,
        execution_context: Mapping[str, Any],
        events: Sequence[Mapping[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        return self._append_run_events(
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
            adapter=adapter,
            run_id=run_id,
            execution_context=execution_context,
            events=events,
            completion_event_type="framework_adapter_run_completed",
            audit_content=f"{getattr(adapter, 'framework_name', 'FrameworkAdapter')} pilot completed",
            base_scope_extra={},
        )

    def append_external_pilot(
        self,
        *,
        db: Any,
        user_id: Optional[int],
        conversation_id: Optional[int],
        adapter: Any,
        run_id: str,
        execution_context: Mapping[str, Any],
        events: Sequence[Mapping[str, Any]],
        status: str,
    ) -> Optional[Dict[str, Any]]:
        return self._append_run_events(
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
            adapter=adapter,
            run_id=run_id,
            execution_context=execution_context,
            events=events,
            completion_event_type="framework_adapter_external_pilot_completed",
            audit_content=f"{getattr(adapter, 'framework_name', 'FrameworkAdapter')} external pilot {status}",
            base_scope_extra={
                "pilot_mode": "external",
                "execution_status": status,
            },
            default_run_kind="framework_adapter_external_pilot",
        )

    def append_precheck(
        self,
        *,
        db: Any,
        user_id: Optional[int],
        conversation_id: Optional[int],
        execution_context: Mapping[str, Any],
        result: Mapping[str, Any],
    ) -> Optional[Dict[str, Any]]:
        if db is None or conversation_id is None:
            return None
        trace_service = self.trace_service_factory(db)
        snapshot_ref = trace_service.build_snapshot_ref(
            source="framework_adapter",
            event_type="framework_adapter_precheck_completed",
            conversation_id=conversation_id,
        )
        dedupe_key = (
            f"framework_adapter_precheck_completed:{conversation_id}:"
            f"{result.get('adapter_id')}:{result.get('configuration_status')}:"
            f"{result.get('execution_block_reason') or result.get('detail')}"
        )
        payload = {
            "adapter_id": result.get("adapter_id"),
            "framework_name": result.get("framework_name"),
            "ready": result.get("ready"),
            "status": result.get("status"),
            "configuration_status": result.get("configuration_status"),
            "execution_mode": result.get("execution_mode"),
            "package_installed": result.get("package_installed"),
            "runtime_enabled": result.get("runtime_enabled"),
            "required_packages": result.get("required_packages"),
            "missing_packages": result.get("missing_packages"),
            "required_env": result.get("required_env"),
            "missing_env": result.get("missing_env"),
            "execution_block_reason": result.get("execution_block_reason"),
            "detail": result.get("detail"),
            "snapshot_ref": snapshot_ref,
            "dedupe_key": dedupe_key,
            "plan_id": execution_context.get("plan_id"),
            "plan_item_id": execution_context.get("plan_item_id"),
            "child_run_id": execution_context.get("child_run_id"),
            "child_display_id": execution_context.get("child_display_id") or execution_context.get("child_run_id"),
            "run_kind": execution_context.get("run_kind") or "framework_adapter_precheck",
        }
        summary = (
            f"Framework adapter `{result.get('framework_name') or result.get('adapter_id') or 'unknown'}` 预检完成"
        )
        detail = str(result.get("execution_block_reason") or result.get("detail") or "").strip()
        compact_payload = self._compact_payload(payload)
        if trace_service.has_runtime_trace_dedupe_key(
            user_id=user_id,
            conversation_id=conversation_id,
            plan_id=execution_context.get("plan_id"),
            item_id=execution_context.get("plan_item_id"),
            source="framework_adapter",
            event_type="framework_adapter_precheck_completed",
            dedupe_key=dedupe_key,
        ):
            return {
                "conversation_id": conversation_id,
                "snapshot_ref": snapshot_ref,
                "trace_written": False,
                "audit_written": False,
                "dedupe_key": dedupe_key,
                "dedupe_source": "persisted_trace",
            }
        trace_written = trace_service.append_runtime_trace(
            user_id=user_id,
            conversation_id=conversation_id,
            plan_id=execution_context.get("plan_id"),
            item_id=execution_context.get("plan_item_id"),
            source="framework_adapter",
            event_type="framework_adapter_precheck_completed",
            summary=summary,
            detail=detail,
            severity="success" if bool(result.get("ready")) else "warning",
            payload=compact_payload,
        )
        audit_written = trace_service.append_runtime_audit(
            user_id=user_id,
            conversation_id=conversation_id,
            plan_id=execution_context.get("plan_id"),
            item_id=execution_context.get("plan_item_id"),
            event_type="framework_adapter_precheck_completed",
            content=summary,
            payload=compact_payload,
        )
        return {
            "conversation_id": conversation_id,
            "snapshot_ref": snapshot_ref,
            "trace_written": bool(trace_written),
            "audit_written": bool(audit_written),
            "dedupe_key": dedupe_key,
            "dedupe_source": "",
        }

    def _append_run_events(
        self,
        *,
        db: Any,
        user_id: Optional[int],
        conversation_id: Optional[int],
        adapter: Any,
        run_id: str,
        execution_context: Mapping[str, Any],
        events: Sequence[Mapping[str, Any]],
        completion_event_type: str,
        audit_content: str,
        base_scope_extra: Mapping[str, Any],
        default_run_kind: str = "framework_adapter",
    ) -> Optional[Dict[str, Any]]:
        if db is None or conversation_id is None:
            return None
        trace_service = self.trace_service_factory(db)
        snapshot_ref = trace_service.build_snapshot_ref(
            source="framework_adapter",
            event_type=completion_event_type,
            conversation_id=conversation_id,
        )
        base_scope = {
            "run_id": run_id,
            "plan_id": execution_context.get("plan_id"),
            "plan_item_id": execution_context.get("plan_item_id"),
            "child_run_id": execution_context.get("child_run_id"),
            "child_display_id": execution_context.get("child_display_id") or execution_context.get("child_run_id"),
            "scheduler_run_id": execution_context.get("scheduler_run_id"),
            "run_kind": execution_context.get("run_kind") or default_run_kind,
            "adapter_id": getattr(adapter, "adapter_id", ""),
            "framework_name": getattr(adapter, "framework_name", ""),
            "snapshot_ref": snapshot_ref,
            **dict(base_scope_extra or {}),
        }
        for event in events:
            trace_event = _build_run_trace_from_runtime_event(dict(event))
            if trace_event is None:
                continue
            trace_payload = dict(trace_event.get("payload") or {})
            trace_payload.update({
                key: value
                for key, value in base_scope.items()
                if value not in (None, "") and key not in trace_payload
            })
            dedupe_key = self._build_external_error_dedupe_key(
                conversation_id=conversation_id,
                trace_event=trace_event,
                payload=trace_payload,
            )
            if dedupe_key:
                trace_payload["dedupe_key"] = dedupe_key
                if trace_service.has_runtime_trace_dedupe_key(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    plan_id=execution_context.get("plan_id"),
                    item_id=execution_context.get("plan_item_id"),
                    run_id=run_id,
                    child_run_id=execution_context.get("child_run_id"),
                    source=trace_event["source"],
                    event_type=trace_event["event_type"],
                    dedupe_key=dedupe_key,
                ):
                    continue
            trace_service.append_runtime_trace(
                user_id=user_id,
                conversation_id=conversation_id,
                plan_id=execution_context.get("plan_id"),
                item_id=execution_context.get("plan_item_id"),
                run_id=run_id,
                child_run_id=execution_context.get("child_run_id"),
                source=trace_event["source"],
                event_type=trace_event["event_type"],
                summary=trace_event["summary"],
                detail=trace_event["detail"],
                severity=trace_event["severity"],
                payload=trace_payload,
            )
        trace_service.append_runtime_audit(
            user_id=user_id,
            conversation_id=conversation_id,
            plan_id=execution_context.get("plan_id"),
            item_id=execution_context.get("plan_item_id"),
            run_id=run_id,
            child_run_id=execution_context.get("child_run_id"),
            event_type=completion_event_type,
            content=audit_content,
            payload=self._compact_payload(base_scope),
        )
        return snapshot_ref

    @staticmethod
    def _build_external_error_dedupe_key(
        *,
        conversation_id: Optional[int],
        trace_event: Mapping[str, Any],
        payload: Mapping[str, Any],
    ) -> str:
        if str(trace_event.get("event_type") or "").strip() != "framework_adapter_external_error":
            return ""
        error_type = str(payload.get("error_type") or "").strip() or "unknown_error"
        detail = str(payload.get("detail") or "").strip()
        adapter_id = str(payload.get("adapter_id") or "").strip() or "unknown_adapter"
        return f"framework_adapter_external_error:{conversation_id}:{adapter_id}:{error_type}:{detail}"

    @staticmethod
    def _compact_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            key: value
            for key, value in dict(payload or {}).items()
            if value not in (None, "")
        }
