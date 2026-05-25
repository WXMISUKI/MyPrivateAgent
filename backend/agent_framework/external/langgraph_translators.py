from dataclasses import dataclass
from typing import Any, Iterable

try:
    from agent_framework.events import AgentEventFactory, AgentEventType
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.agent_framework.events import AgentEventFactory, AgentEventType


_EXECUTION_CONTEXT_WHITELIST = (
    "plan_id",
    "plan_item_id",
    "run_kind",
    "scheduler_run_id",
    "child_run_id",
)


@dataclass(frozen=True)
class LangGraphRequestTranslator:
    adapter_id: str
    framework_name: str
    assistant_id: str
    endpoint: str

    def translate(
        self,
        run_id: str,
        messages: Iterable[dict[str, Any]],
        execution_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "framework_name": self.framework_name,
            "run_id": run_id,
            "assistant_id": self.assistant_id,
            "endpoint": self.endpoint,
            "messages": [self._normalize_message(message) for message in messages],
            "execution_context": self._filter_execution_context(execution_context),
        }

    @staticmethod
    def _normalize_message(message: dict[str, Any]) -> dict[str, str]:
        raw_role = message.get("role")
        normalized_role = str(raw_role).strip().lower() if raw_role else ""
        role = normalized_role or "user"

        raw_content = message.get("content")
        content = "" if raw_content is None else str(raw_content).strip()

        return {
            "role": role,
            "content": content,
        }

    @staticmethod
    def _filter_execution_context(
        execution_context: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if not execution_context:
            return {}

        return {
            key: execution_context[key]
            for key in _EXECUTION_CONTEXT_WHITELIST
            if key in execution_context
        }


@dataclass(frozen=True)
class LangGraphEventTranslator:
    adapter_id: str
    framework_name: str

    def translate_chunk(
        self,
        run_id: str,
        chunk: dict[str, Any],
        execution_context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        chunk_type = str(chunk.get("type") or "").strip().lower()
        if not chunk_type:
            return []

        event_type_map = {
            "status": (
                AgentEventType.STATUS,
                "framework_adapter_status",
            ),
            "reasoning": (
                AgentEventType.REASONING,
                "framework_adapter_reasoning",
            ),
            "error": (
                AgentEventType.ERROR,
                "framework_adapter_external_error",
            ),
        }
        mapped = event_type_map.get(chunk_type)
        if mapped is None:
            return []

        platform_event_type, adapter_event_type = mapped
        payload = self._build_payload(
            chunk=chunk,
            execution_context=execution_context,
            framework_adapter_event_type=adapter_event_type,
        )
        event = AgentEventFactory(run_id=run_id).build(platform_event_type, payload)
        return [event.to_dict()]

    def _build_payload(
        self,
        *,
        chunk: dict[str, Any],
        execution_context: dict[str, Any] | None,
        framework_adapter_event_type: str,
    ) -> dict[str, Any]:
        payload = {
            "source": "framework_adapter",
            "adapter_id": self.adapter_id,
            "framework_name": self.framework_name,
            "execution_context": LangGraphRequestTranslator._filter_execution_context(execution_context),
            "framework_adapter_event_type": framework_adapter_event_type,
        }
        for key, value in chunk.items():
            if key == "type":
                continue
            payload[key] = value
        return payload


@dataclass(frozen=True)
class LangGraphOutputTranslator:
    adapter_id: str
    framework_name: str

    def translate_final(
        self,
        run_id: str,
        output: Any,
        execution_context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        content = output.get("content") if isinstance(output, dict) else output
        payload = {
            "source": "framework_adapter",
            "adapter_id": self.adapter_id,
            "framework_name": self.framework_name,
            "content": "" if content is None else str(content),
            "execution_context": LangGraphRequestTranslator._filter_execution_context(execution_context),
            "framework_adapter_event_type": "framework_adapter_output",
        }
        event = AgentEventFactory(run_id=run_id).build(AgentEventType.CONTENT, payload)
        return [event.to_dict()]
