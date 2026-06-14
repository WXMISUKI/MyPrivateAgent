"""Runtime execution helpers for framework adapter pilots."""

from __future__ import annotations

import sys
from typing import Any, Dict, Mapping, Optional, Sequence

try:
    from agent_framework import framework_adapters as framework_adapters_module
    from agent_framework.framework_adapters import get_framework_adapter_registry
    from services.framework_adapter_external_pilot_service import FrameworkAdapterExternalPilotService
    from services.framework_adapter_timeline_service import FrameworkAdapterTimelineRecorder
    from services.query_control_event_mapper_service import get_query_control_event_mapper_service
    from services.run_trace_service import get_run_trace_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.agent_framework import framework_adapters as framework_adapters_module
    from backend.agent_framework.framework_adapters import get_framework_adapter_registry
    from backend.services.framework_adapter_external_pilot_service import FrameworkAdapterExternalPilotService
    from backend.services.framework_adapter_timeline_service import FrameworkAdapterTimelineRecorder
    from backend.services.query_control_event_mapper_service import get_query_control_event_mapper_service
    from backend.services.run_trace_service import get_run_trace_service


class FrameworkAdapterRuntimeService:
    """Execute pilot adapters through the platform trace and audit boundary."""

    def __init__(
        self,
        *,
        framework_adapter_registry: Any = None,
        external_pilot_transport: Any = None,
        query_control_event_mapper: Any = None,
        query_control_timeline_service: Any = None,
    ):
        self.framework_adapter_registry = framework_adapter_registry or get_framework_adapter_registry()
        self.external_pilot_transport = external_pilot_transport
        self.timeline_recorder = FrameworkAdapterTimelineRecorder(
            trace_service_factory=lambda db: get_run_trace_service(db),
        )
        self.query_control_event_mapper = query_control_event_mapper or get_query_control_event_mapper_service()
        self.query_control_timeline_service = query_control_timeline_service

    def execute_adapter_run(
        self,
        *,
        adapter_id: str,
        run_id: str,
        messages: Sequence[Mapping[str, Any]],
        execution_context: Optional[Mapping[str, Any]] = None,
        db: Any = None,
        user_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        adapter = self._get_adapter(adapter_id)
        can_execute, block_reason = adapter.can_execute()
        if not can_execute:
            raise ValueError(
                block_reason
                or f"framework adapter `{adapter_id}` is registered but runtime execution is not enabled"
            )
        context = dict(execution_context or {})
        translated_input = adapter.translate_input(
            run_id=run_id,
            messages=messages,
            execution_context=context,
        )
        stream_events = list(adapter.stream_events(
            translated_input=translated_input,
            execution_context=context,
        ))
        final_content = self._build_final_content(messages=translated_input.get("messages") or [])
        output_events = adapter.translate_output(
            run_id=run_id,
            output={"content": final_content},
            execution_context=context,
        )
        events = [*stream_events, *output_events]
        snapshot_ref = self.timeline_recorder.append_adapter_run(
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
            adapter=adapter,
            run_id=run_id,
            execution_context=context,
            events=events,
        )
        return {
            "adapter_id": adapter_id,
            "run_id": run_id,
            "translated_input": translated_input,
            "events": events,
            "final_output": final_content,
            "snapshot_ref": snapshot_ref,
        }

    def execute_external_adapter_run(
        self,
        *,
        adapter_id: str,
        run_id: str,
        messages: Sequence[Mapping[str, Any]],
        execution_context: Optional[Mapping[str, Any]] = None,
        db: Any = None,
        user_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        adapter = self._get_adapter(adapter_id)
        if str(getattr(adapter, "adapter_id", "")).strip() != "langgraph_draft":
            raise ValueError("external pilot only supports `langgraph_draft`")
        can_execute, block_reason = adapter.can_execute()
        if not can_execute:
            raise ValueError(
                block_reason
                or f"framework adapter `{adapter_id}` is registered but runtime execution is not enabled"
            )

        context = dict(execution_context or {})
        result = FrameworkAdapterExternalPilotService(
            transport=self.external_pilot_transport,
            setting_reader=_framework_adapter_setting,
        ).execute(
            adapter=adapter,
            run_id=run_id,
            messages=messages,
            execution_context=context,
        )

        snapshot_ref = self.timeline_recorder.append_external_pilot(
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
            adapter=adapter,
            run_id=run_id,
            execution_context=context,
            events=result.get("events") or [],
            status=str(result.get("status") or ""),
        )
        result = {
            **result,
            "snapshot_ref": snapshot_ref,
        }
        query_control_result = self._record_external_adapter_query_control_events(
            db=db,
            conversation_id=conversation_id,
            run_id=run_id,
            events=result.get("events") or [],
        )
        if query_control_result["recordings"]:
            result["query_control_recordings"] = query_control_result["recordings"]
        if query_control_result["failures"]:
            result["query_control_recording_failures"] = query_control_result["failures"]
        return result

    def _validate_external_pilot_request(self, translated_input: Mapping[str, Any]) -> None:
        FrameworkAdapterExternalPilotService(
            transport=self.external_pilot_transport,
            setting_reader=_framework_adapter_setting,
        ).validate_request(translated_input)

    def _validate_external_pilot_probe(
        self,
        *,
        probe_result: Mapping[str, Any],
        assistant_id: str,
    ) -> None:
        FrameworkAdapterExternalPilotService(
            transport=self.external_pilot_transport,
            setting_reader=_framework_adapter_setting,
        ).validate_probe(
            probe_result=probe_result,
            assistant_id=assistant_id,
        )

    def precheck_adapter(
        self,
        *,
        adapter_id: str,
        db: Any = None,
        user_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
        execution_context: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        adapter = self._get_adapter(adapter_id)
        health = adapter.health_check().to_dict()
        can_execute, block_reason = adapter.can_execute()
        result = {
            "adapter_id": health.get("adapter_id") or str(adapter_id or "").strip(),
            "framework_name": health.get("framework_name") or "",
            "ready": bool(can_execute),
            "status": health.get("status") or "unknown",
            "configuration_status": health.get("configuration_status") or "unknown",
            "execution_mode": health.get("execution_mode") or "",
            "package_installed": bool(health.get("package_installed")),
            "runtime_enabled": bool(health.get("runtime_enabled")),
            "required_packages": list(health.get("required_packages") or []),
            "missing_packages": list(health.get("missing_packages") or []),
            "required_env": list(health.get("required_env") or []),
            "missing_env": list(health.get("missing_env") or []),
            "execution_block_reason": block_reason or str(health.get("execution_block_reason") or "").strip(),
            "detail": str(health.get("detail") or "").strip(),
        }
        timeline_recording = self.timeline_recorder.append_precheck(
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
            execution_context=dict(execution_context or {}),
            result=result,
        )
        if timeline_recording:
            result["timeline_recording"] = timeline_recording
        return result

    def build_adapter_authoring_checklist(
        self,
        *,
        adapter_id: str,
    ) -> Dict[str, Any]:
        normalized_id = str(adapter_id or "").strip()
        try:
            adapter = self._get_adapter(normalized_id)
        except ValueError:
            return self._build_unknown_adapter_checklist(normalized_id)

        precheck = self.precheck_adapter(adapter_id=normalized_id)
        ready = bool(precheck.get("ready"))
        promotion_status = "pilot_candidate" if ready else "blocked"
        blockers = self._build_authoring_blockers(precheck)
        return {
            "contract_version": "framework-adapter-authoring-checklist-v1",
            "adapter_id": precheck.get("adapter_id") or normalized_id,
            "framework_name": precheck.get("framework_name") or getattr(adapter, "framework_name", ""),
            "checklist_status": "ready" if ready else "blocked",
            "authoring_sections": self._build_authoring_sections(adapter=adapter, precheck=precheck),
            "promotion_review": {
                "status": promotion_status,
                "will_execute": False,
                "default_chat_entry": "disabled",
                "next_allowed_action": "controlled_pilot_review" if ready else "resolve_precheck_blockers",
                "blockers": blockers,
            },
            "precheck_summary": {
                "ready": ready,
                "status": precheck.get("status") or "unknown",
                "configuration_status": precheck.get("configuration_status") or "unknown",
                "execution_mode": precheck.get("execution_mode") or "",
                "missing_packages": list(precheck.get("missing_packages") or []),
                "missing_env": list(precheck.get("missing_env") or []),
                "execution_block_reason": str(precheck.get("execution_block_reason") or "").strip(),
            },
            "boundary": self._adapter_authoring_boundary(),
        }

    def _get_adapter(self, adapter_id: str) -> Any:
        normalized_id = str(adapter_id or "").strip()
        for adapter in self.framework_adapter_registry.list_adapters():
            if str(getattr(adapter, "adapter_id", "")).strip() == normalized_id:
                return adapter
        raise ValueError(f"framework adapter `{normalized_id}` is not registered")

    @staticmethod
    def _build_authoring_sections(*, adapter: Any, precheck: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            "identity": {
                "adapter_id": precheck.get("adapter_id") or getattr(adapter, "adapter_id", ""),
                "framework_name": precheck.get("framework_name") or getattr(adapter, "framework_name", ""),
                "supported_run_kinds": list(getattr(adapter, "supported_run_kinds", ()) or []),
                "capability_requirements": list(getattr(adapter, "capability_requirements", ()) or []),
            },
            "lifecycle_mapping": {
                "required_events": [
                    "framework_adapter_status",
                    "framework_adapter_reasoning",
                    "framework_adapter_output",
                    "framework_adapter_external_error",
                ],
                "query_control_channel": "external_adapter",
                "default_chat_entry": "disabled",
            },
            "readiness_checks": {
                "package_installed": bool(precheck.get("package_installed")),
                "runtime_enabled": bool(precheck.get("runtime_enabled")),
                "required_packages": list(precheck.get("required_packages") or []),
                "missing_packages": list(precheck.get("missing_packages") or []),
                "required_env": list(precheck.get("required_env") or []),
                "missing_env": list(precheck.get("missing_env") or []),
            },
            "governance_timeline": {
                "precheck_event": "framework_adapter_precheck_completed",
                "run_events": [
                    "framework_adapter_status",
                    "framework_adapter_reasoning",
                    "framework_adapter_output",
                    "framework_adapter_external_error",
                ],
                "trace_write": "not_performed_by_checklist",
                "audit_write": "not_performed_by_checklist",
            },
            "promotion_gate": {
                "pilot_ready_requires": [
                    "adapter_registered",
                    "precheck_ready",
                    "lifecycle_mapping_declared",
                    "governance_boundary_declared",
                ],
                "default_chat_entry": "disabled",
                "main_chat_promotion_requires_future_change": True,
            },
            "non_goals": [
                "default_main_chat_execution",
                "new_framework_dependency",
                "tool_runtime_changes",
                "worker_execution",
                "query_detail_history_workspace_promotion",
            ],
        }

    @staticmethod
    def _build_authoring_blockers(precheck: Mapping[str, Any]) -> list[Dict[str, Any]]:
        blockers: list[Dict[str, Any]] = []
        for package_name in precheck.get("missing_packages") or []:
            blockers.append({
                "component": "readiness",
                "status": "blocked",
                "reason_code": "missing_package",
                "detail": str(package_name),
            })
        for env_name in precheck.get("missing_env") or []:
            blockers.append({
                "component": "readiness",
                "status": "blocked",
                "reason_code": "missing_env",
                "detail": str(env_name),
            })
        block_reason = str(precheck.get("execution_block_reason") or "").strip()
        if block_reason:
            blockers.append({
                "component": "execution_gate",
                "status": "blocked",
                "reason_code": "execution_blocked",
                "detail": block_reason,
            })
        return blockers

    @classmethod
    def _build_unknown_adapter_checklist(cls, adapter_id: str) -> Dict[str, Any]:
        return {
            "contract_version": "framework-adapter-authoring-checklist-v1",
            "adapter_id": adapter_id or None,
            "framework_name": "",
            "checklist_status": "blocked",
            "authoring_sections": {},
            "promotion_review": {
                "status": "blocked",
                "will_execute": False,
                "default_chat_entry": "disabled",
                "next_allowed_action": "register_adapter_before_review",
                "blockers": [{
                    "component": "adapter_registry",
                    "status": "blocked",
                    "reason_code": "adapter_not_registered",
                    "detail": adapter_id or "missing_adapter_id",
                }],
            },
            "precheck_summary": {
                "ready": False,
                "status": "missing",
                "configuration_status": "missing",
                "execution_mode": "",
                "missing_packages": [],
                "missing_env": [],
                "execution_block_reason": "adapter_not_registered",
            },
            "boundary": cls._adapter_authoring_boundary(),
        }

    @staticmethod
    def _adapter_authoring_boundary() -> Dict[str, Any]:
        return {
            "adapter_execution": "not_performed",
            "external_framework_call": "not_performed",
            "default_chat_entry": "disabled",
            "trace_write": "not_performed",
            "audit_write": "not_performed",
            "tool_registration": "not_performed",
            "worker_execution": "not_performed",
            "runtime_behavior_changed": False,
        }

    def _build_final_content(self, *, messages: Sequence[Mapping[str, Any]]) -> str:
        last_user_message = ""
        for message in messages:
            if str(message.get("role") or "").strip() == "user":
                last_user_message = str(message.get("content") or "").strip()
        return f"Local fake adapter processed: {last_user_message or 'empty_input'}"

    def _record_external_adapter_query_control_events(
        self,
        *,
        db: Any,
        conversation_id: Optional[int],
        run_id: str,
        events: Sequence[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        recordings = []
        failures = []
        if db is None or self.query_control_timeline_service is None:
            return {"recordings": recordings, "failures": failures}
        for event in events:
            event_dict = dict(event or {})
            mapping = self.query_control_event_mapper.map_external_adapter_event(event_dict)
            if mapping is None:
                continue
            payload = self.query_control_event_mapper.build_record_payload(event_dict)
            try:
                recordings.append(self.query_control_timeline_service.record_stage(
                    db=db,
                    conversation_id=conversation_id,
                    channel=mapping["channel"],
                    stage=mapping["stage"],
                    query_id=run_id,
                    summary=str(event_dict.get("summary") or f"External adapter {mapping['stage']}"),
                    detail=str(event_dict.get("detail") or ""),
                    severity=str(event_dict.get("severity") or "info"),
                    payload=payload,
                ))
            except Exception as exc:  # pragma: no cover - exact recorder failure belongs to integration.
                failures.append({
                    "stage": mapping["stage"],
                    "event_type": event_dict.get("type"),
                    "error": str(exc),
                })
        return {"recordings": recordings, "failures": failures}


_framework_adapter_runtime_service: FrameworkAdapterRuntimeService | None = None


def get_framework_adapter_runtime_service() -> FrameworkAdapterRuntimeService:
    global _framework_adapter_runtime_service
    if _framework_adapter_runtime_service is None:
        _framework_adapter_runtime_service = FrameworkAdapterRuntimeService()
    return _framework_adapter_runtime_service


def _framework_adapter_setting(name: str, default: Any) -> Any:
    for module_name in ("backend.agent_framework.framework_adapters", "agent_framework.framework_adapters"):
        module = sys.modules.get(module_name)
        if module is not None and hasattr(module, name):
            return getattr(module, name)
    return getattr(framework_adapters_module, name, default)
