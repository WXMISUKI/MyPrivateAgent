"""Map runtime events onto the query control plane lifecycle."""

from __future__ import annotations

from typing import Any, Optional


class QueryControlEventMapperService:
    """Translate Embedded SDK events into canonical query lifecycle stages."""

    MAIN_CHAT_CHANNEL = "main_chat"
    EMBEDDED_SDK_CHANNEL = "embedded_sdk"
    EXTERNAL_ADAPTER_CHANNEL = "external_adapter"
    SUBAGENT_CHANNEL = "subagent_lane"

    _MAIN_CHAT_STATUS_STAGE_MAP = {
        "main_chat_input_received": "input_received",
    }
    _STATUS_STAGE_MAP = {
        "run_created": "input_received",
        "tool_permission_required": "tool_decision",
        "tool_call_started": "tool_execution",
        "tool_result": "observation",
        "execution_loop_reviewed": "review",
        "execution_loop_done": "final_output",
    }
    _LOOP_STEP_STAGE_MAP = {
        "planning": "planning",
        "generating": "model_stream",
        "observing": "observation",
        "finalizing": "review",
        "done": "final_output",
    }
    _EXTERNAL_ADAPTER_EVENT_STAGE_MAP = {
        "framework_adapter_status": "model_stream",
        "framework_adapter_reasoning": "planning",
        "framework_adapter_output": "final_output",
        "framework_adapter_external_error": "final_output",
    }
    _SUBAGENT_EVENT_STAGE_MAP = {
        "child_run_created": "input_received",
        "subagent_spawned": "planning",
        "subagent_collected": "observation",
        "subagent_merged": "final_output",
    }

    def map_embedded_sdk_event(self, event: dict[str, Any]) -> Optional[dict[str, str]]:
        event = dict(event or {})
        status_kind = str(event.get("status_kind") or "").strip()
        if status_kind == "execution_loop_step":
            stage = self._LOOP_STEP_STAGE_MAP.get(str(event.get("loop_step") or "").strip())
        else:
            stage = self._STATUS_STAGE_MAP.get(status_kind)
        if not stage:
            return None
        return {
            "channel": self.EMBEDDED_SDK_CHANNEL,
            "stage": stage,
        }

    def map_main_chat_event(self, event: dict[str, Any]) -> Optional[dict[str, str]]:
        event = dict(event or {})
        event_type = str(event.get("type") or "").strip()
        status_kind = str(event.get("status_kind") or "").strip()

        if event_type == "status":
            stage = self._MAIN_CHAT_STATUS_STAGE_MAP.get(status_kind)
            if not stage and status_kind == "execution_progress":
                phase = str(event.get("phase") or "").strip()
                if phase in {"completion_retry", "boundary_fallback"}:
                    stage = "review"
            if not stage:
                return None
            return {
                "channel": self.MAIN_CHAT_CHANNEL,
                "stage": stage,
            }

        if event_type == "reasoning":
            return {
                "channel": self.MAIN_CHAT_CHANNEL,
                "stage": "planning",
            }

        if event_type in {"content", "answer"}:
            if event.get("completion_check"):
                return {
                    "channel": self.MAIN_CHAT_CHANNEL,
                    "stage": "review",
                }
            return {
                "channel": self.MAIN_CHAT_CHANNEL,
                "stage": "model_stream",
            }

        if event_type == "tool_permission_required":
            return {
                "channel": self.MAIN_CHAT_CHANNEL,
                "stage": "tool_decision",
            }

        if event_type == "tool_result":
            status = str(event.get("status") or "").strip()
            if status == "pending_permission":
                return None
            return {
                "channel": self.MAIN_CHAT_CHANNEL,
                "stage": "observation",
            }

        if event_type == "done":
            state = str(event.get("state") or "").strip().lower()
            stop_reason = str(event.get("stop_reason") or "").strip().lower()
            if state == "waiting_approval" or stop_reason == "approval_required":
                return None
            return {
                "channel": self.MAIN_CHAT_CHANNEL,
                "stage": "final_output",
            }

        return None

    def map_external_adapter_event(self, event: dict[str, Any]) -> Optional[dict[str, str]]:
        payload = dict((event or {}).get("payload") or {})
        adapter_event_type = str(payload.get("framework_adapter_event_type") or "").strip()
        stage = self._EXTERNAL_ADAPTER_EVENT_STAGE_MAP.get(adapter_event_type)
        if not stage:
            return None
        return {
            "channel": self.EXTERNAL_ADAPTER_CHANNEL,
            "stage": stage,
        }

    def map_subagent_event(self, event: dict[str, Any]) -> Optional[dict[str, str]]:
        status_kind = str((event or {}).get("status_kind") or "").strip()
        stage = self._SUBAGENT_EVENT_STAGE_MAP.get(status_kind)
        if not stage:
            return None
        return {
            "channel": self.SUBAGENT_CHANNEL,
            "stage": stage,
        }

    def build_record_payload(self, event: dict[str, Any]) -> dict[str, Any]:
        event = dict(event or {})
        payload = {
            "source_event_id": event.get("id"),
            "source_run_id": event.get("run_id"),
            "source_parent_run_id": event.get("parent_run_id"),
            "source_child_run_id": event.get("child_run_id"),
            "source_child_display_id": event.get("child_display_id"),
            "source_status_kind": event.get("status_kind"),
            "source_event_type": event.get("type"),
            "source_loop_step": event.get("loop_step"),
        }
        tool_runtime_observation = self._build_tool_runtime_observation(event)
        if tool_runtime_observation:
            payload["tool_runtime_observation"] = tool_runtime_observation
        return {
            key: value
            for key, value in payload.items()
            if value is not None and str(value).strip()
        }

    def _build_tool_runtime_observation(self, event: dict[str, Any]) -> Optional[dict[str, Any]]:
        event = dict(event or {})
        event_type = str(event.get("type") or "").strip()
        status_kind = str(event.get("status_kind") or "").strip()
        if event_type != "tool_result" and status_kind != "tool_result":
            return None

        event_payload = dict(event.get("payload") or {})
        execution = dict(event.get("execution") or event_payload.get("execution") or {})
        if not execution:
            return None

        retry = dict(execution.get("retry") or {})
        timeout = dict(execution.get("timeout") or {})
        schema_validation = dict(execution.get("schema_validation") or {})
        policy_decision = dict(execution.get("policy_decision") or {})
        observation = dict(execution.get("observation") or {})

        summary = {
            "tool_name": event.get("tool_name") or event.get("name") or event_payload.get("tool_name") or event_payload.get("name"),
            "status": observation.get("status") or event.get("status") or event_payload.get("status"),
            "executor": execution.get("executor"),
            "policy_status": policy_decision.get("status"),
            "policy_permission_level": policy_decision.get("permission_level"),
            "policy_reason_code": policy_decision.get("reason_code"),
            "schema_validation_status": schema_validation.get("status"),
            "retry_status": retry.get("status"),
            "retry_attempt_count": retry.get("attempt_count"),
            "retry_max_attempts": retry.get("max_attempts"),
            "timeout_status": timeout.get("status"),
            "timeout_seconds": timeout.get("timeout_seconds"),
            "timeout_enforcement": timeout.get("enforcement"),
        }
        return {
            key: value
            for key, value in summary.items()
            if value is not None and str(value).strip()
        }


_query_control_event_mapper_service: QueryControlEventMapperService | None = None


def get_query_control_event_mapper_service() -> QueryControlEventMapperService:
    global _query_control_event_mapper_service
    if _query_control_event_mapper_service is None:
        _query_control_event_mapper_service = QueryControlEventMapperService()
    return _query_control_event_mapper_service
