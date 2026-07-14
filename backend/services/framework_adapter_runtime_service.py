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
            "authoring_template": self._build_authoring_template(adapter=adapter, precheck=precheck),
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

    def build_langgraph_controlled_pilot_readiness(
        self,
        *,
        adapter_id: str = "langgraph_draft",
    ) -> Dict[str, Any]:
        normalized_id = str(adapter_id or "").strip()
        checklist = self.build_adapter_authoring_checklist(adapter_id=normalized_id)
        blockers: list[Dict[str, Any]] = []
        if checklist.get("checklist_status") == "blocked":
            blockers.extend(list(checklist.get("promotion_review", {}).get("blockers") or []))

        if normalized_id != "langgraph_draft":
            registered = checklist.get("precheck_summary", {}).get("status") != "missing"
            blockers.append({
                "component": "pilot_target",
                "status": "blocked",
                "reason_code": (
                    "unsupported_controlled_pilot_target"
                    if registered
                    else "adapter_not_registered"
                ),
                "detail": (
                    "LangGraph controlled pilot readiness only supports `langgraph_draft`"
                    if registered
                    else normalized_id or "missing_adapter_id"
                ),
            })

        template = checklist.get("authoring_template") if isinstance(checklist.get("authoring_template"), Mapping) else {}
        proof_slices = {
            str(item.get("proof_slice") or "").strip()
            for item in template.get("runtime_plane_mapping", [])
            if isinstance(item, Mapping)
        }
        required_proofs = {"simple_agent", "tool_agent", "approval_agent"}
        missing_proofs = sorted(required_proofs - proof_slices)
        for proof_slice in missing_proofs:
            blockers.append({
                "component": "authoring_template",
                "status": "blocked",
                "reason_code": "missing_stage_1_proof_mapping",
                "detail": proof_slice,
            })

        boundary = template.get("boundaries") if isinstance(template.get("boundaries"), Mapping) else {}
        if boundary.get("default_chat_entry") != "disabled":
            blockers.append({
                "component": "boundary",
                "status": "blocked",
                "reason_code": "default_chat_boundary_drift",
                "detail": str(boundary.get("default_chat_entry") or ""),
            })

        unique_blockers = self._dedupe_readiness_blockers(blockers)
        ready = normalized_id == "langgraph_draft" and not unique_blockers
        precheck = checklist.get("precheck_summary") if isinstance(checklist.get("precheck_summary"), Mapping) else {}
        return {
            "contract_version": "langgraph-controlled-pilot-readiness-v1",
            "adapter_id": checklist.get("adapter_id") or normalized_id or None,
            "framework_name": checklist.get("framework_name") or "LangGraph",
            "readiness_status": "ready" if ready else "blocked",
            "can_start_controlled_pilot": ready,
            "next_allowed_action": (
                "run_explicit_controlled_pilot_smoke"
                if ready
                else "resolve_controlled_pilot_blockers"
            ),
            "pilot_target": {
                "adapter_id": "langgraph_draft",
                "framework_name": "LangGraph",
                "execution_mode": "draft_external_runtime",
                "run_kind": "framework_adapter_external_pilot",
            },
            "precheck_summary": {
                "ready": bool(precheck.get("ready")),
                "status": precheck.get("status") or "unknown",
                "configuration_status": precheck.get("configuration_status") or "unknown",
                "execution_mode": precheck.get("execution_mode") or "",
                "missing_packages": list(precheck.get("missing_packages") or []),
                "missing_env": list(precheck.get("missing_env") or []),
                "execution_block_reason": str(precheck.get("execution_block_reason") or "").strip(),
            },
            "authoring_template_summary": {
                "template_version": template.get("template_version") or "",
                "registration_status": template.get("registration_status") or "",
                "stage_1_proof_mapping": sorted(proof_slices),
                "runtime_surface_profile": (
                    template.get("projection_mapping", {}).get("runtime_surface_profile")
                    if isinstance(template.get("projection_mapping"), Mapping)
                    else ""
                ),
                "minimum_smoke_tests": list(template.get("minimum_smoke_tests") or []),
            },
            "required_gates": [
                "adapter_registered",
                "langgraph_package_available",
                "langgraph_runtime_endpoint_configured",
                "langgraph_assistant_id_configured",
                "langgraph_runtime_execution_enabled",
                "langgraph_external_pilot_enabled",
                "authoring_template_stage_1_mapping_present",
                "default_chat_entry_disabled",
            ],
            "blockers": unique_blockers,
            "boundaries": {
                "will_execute": False,
                "external_framework_call": "not_performed",
                "trace_write": "not_performed",
                "audit_write": "not_performed",
                "tool_registration": "not_performed",
                "default_chat_entry": "disabled",
                "production_promotion": "disabled",
            },
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

    @staticmethod
    def _dedupe_readiness_blockers(blockers: Sequence[Mapping[str, Any]]) -> list[Dict[str, Any]]:
        seen: set[tuple[str, str, str]] = set()
        unique: list[Dict[str, Any]] = []
        for blocker in blockers:
            item = dict(blocker or {})
            key = (
                str(item.get("component") or "").strip(),
                str(item.get("reason_code") or "").strip(),
                str(item.get("detail") or "").strip(),
            )
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)
        return unique

    @classmethod
    def _build_unknown_adapter_checklist(cls, adapter_id: str) -> Dict[str, Any]:
        return {
            "contract_version": "framework-adapter-authoring-checklist-v1",
            "adapter_id": adapter_id or None,
            "framework_name": "",
            "checklist_status": "blocked",
            "authoring_sections": {},
            "authoring_template": cls._build_authoring_template(
                adapter=None,
                precheck={
                    "adapter_id": adapter_id or None,
                    "framework_name": "",
                    "ready": False,
                    "execution_block_reason": "adapter_not_registered",
                },
            ),
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
    def _build_authoring_template(*, adapter: Any, precheck: Mapping[str, Any]) -> Dict[str, Any]:
        adapter_id = str(precheck.get("adapter_id") or getattr(adapter, "adapter_id", "") or "").strip()
        framework_name = str(precheck.get("framework_name") or getattr(adapter, "framework_name", "") or "").strip()
        target_framework = framework_name or "unregistered_framework"
        registration_status = "registered" if adapter is not None else "missing"
        return {
            "template_version": "framework-adapter-authoring-template-v1",
            "adapter_id": adapter_id or None,
            "target_framework": target_framework,
            "registration_status": registration_status,
            "next_action": "author_controlled_pilot_adapter" if registration_status == "registered" else "register_adapter_before_authoring_review",
            "recommended_files": [
                {
                    "path": "backend/agent_framework/framework_adapter_spi/<adapter_id>.py",
                    "purpose": "implement AgentFrameworkAdapter translation, health, and event normalization",
                    "owner": "framework_adapter",
                },
                {
                    "path": "backend/agent_framework/framework_adapters.py",
                    "purpose": "register the adapter behind explicit config gates",
                    "owner": "framework_adapter_registry",
                },
                {
                    "path": "tests/agent_framework/test_<adapter_id>_adapter.py",
                    "purpose": "verify health, translation, blocked execution, and normalized events",
                    "owner": "adapter_smoke_tests",
                },
                {
                    "path": "docs/architecture/runtime_plane_integration_strategy.md",
                    "purpose": "document borrowed framework semantics and MyPrivateAgent boundaries",
                    "owner": "architecture_docs",
                },
            ],
            "required_contracts": [
                {
                    "name": "AgentFrameworkAdapter",
                    "module": "backend.agent_framework.framework_adapter_spi",
                    "responsibility": "translate external runtime input, events, health, and output into platform-owned shapes",
                },
                {
                    "name": "ExecutionRequest",
                    "module": "backend.runtime_plane.contracts.execution",
                    "responsibility": "represent caller-owned request metadata without framework clients or active iterators",
                },
                {
                    "name": "ExecutionEvent",
                    "module": "backend.runtime_plane.contracts.execution",
                    "responsibility": "normalize framework lifecycle events into compact governance-safe evidence",
                },
                {
                    "name": "ExecutionResult",
                    "module": "backend.runtime_plane.contracts.execution",
                    "responsibility": "return final status, artifacts, tool calls, citations, and trace references",
                },
                {
                    "name": "runtime_plane_governance_profile",
                    "module": "backend.services.runtime_surface_runtime_plane_builder",
                    "responsibility": "expose read-only projection readiness without executing adapters or persisting traces",
                },
            ],
            "runtime_plane_mapping": [
                {
                    "proof_slice": "simple_agent",
                    "validates": "request/event/result envelope and final output normalization",
                    "adapter_responsibility": "map framework start/output events to ExecutionEvent and ExecutionResult",
                },
                {
                    "proof_slice": "tool_agent",
                    "validates": "controlled read-only tool observation and tool result metadata",
                    "adapter_responsibility": "surface tool calls as normalized observations without bypassing ToolRuntime policy",
                },
                {
                    "proof_slice": "approval_agent",
                    "validates": "high-risk tool intent becomes approval_pending without handler execution",
                    "adapter_responsibility": "convert framework interruptions or human-in-loop pauses into approval_required evidence",
                },
            ],
            "projection_mapping": {
                "source_read_model": "runtime_plane_governance_projection",
                "runtime_surface_profile": "runtime_plane_governance_profile",
                "expected_projection_fields": [
                    "request_id",
                    "run_id",
                    "agent_id",
                    "runtime",
                    "adapter_id",
                    "result_status",
                    "stage_counts",
                    "tool_call_count",
                    "approval_required",
                    "trace_ref",
                ],
                "read_model_only": True,
            },
            "minimum_smoke_tests": [
                "health_check_without_external_execution",
                "translate_input_preserves_request_context",
                "stream_events_returns_normalized_lifecycle_events",
                "translate_output_returns_final_result_event",
                "blocked_precheck_does_not_execute_adapter",
                "checklist_generation_does_not_write_trace_or_audit",
            ],
            "promotion_gate_requirements": [
                "adapter_registered",
                "precheck_ready",
                "stage_1_runtime_plane_mapping_declared",
                "governance_projection_mapping_declared",
                "minimum_smoke_tests_passed",
                "controlled_pilot_review_approved",
                "default_chat_entry_remains_disabled",
            ],
            "non_goals": [
                "execute_external_runtime_from_template",
                "implement_langgraph_or_agentrun_engine",
                "create_worker_scheduler_checkpoint_or_sandbox",
                "register_tools_or_modify_tool_runtime",
                "persist_trace_or_audit_from_checklist",
                "promote_default_main_chat_execution",
            ],
            "boundaries": {
                "will_execute": False,
                "default_chat_entry": "disabled",
                "external_framework_call": "not_performed",
                "trace_write": "not_performed",
                "audit_write": "not_performed",
                "tool_registration": "not_performed",
                "runtime_behavior_changed": False,
            },
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
