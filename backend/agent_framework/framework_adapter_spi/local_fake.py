"""Local fake adapter used to validate the adapter SPI lifecycle."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence

from ..events import AgentEventFactory, AgentEventType
from .base import AgentFrameworkAdapter
from .health import FrameworkAdapterHealth


class LocalFakeFrameworkAdapter(AgentFrameworkAdapter):
    """Local pilot adapter for validating the end-to-end SPI lifecycle without external dependencies."""

    def __init__(
        self,
        *,
        adapter_id: str = "local_fake_framework",
        framework_name: str = "LocalFakeFramework",
        supported_run_kinds: Iterable[str] = ("chat",),
        capability_requirements: Iterable[str] = ("tool_runtime", "adapter_health", "audit"),
    ):
        self.adapter_id = str(adapter_id)
        self.framework_name = str(framework_name)
        self.supported_run_kinds = tuple(str(item) for item in supported_run_kinds)
        self.capability_requirements = tuple(str(item) for item in capability_requirements)

    def health_check(self) -> FrameworkAdapterHealth:
        return FrameworkAdapterHealth(
            adapter_id=self.adapter_id,
            framework_name=self.framework_name,
            status="healthy",
            detail="Local fake adapter pilot is active.",
            supported_run_kinds=self.supported_run_kinds,
            capability_requirements=self.capability_requirements,
            package_installed=True,
            runtime_enabled=True,
            execution_mode="local_fake_pilot",
            required_env=(),
            execution_block_reason="",
            configuration_status="ready",
            missing_env=(),
            missing_packages=(),
            required_packages=(),
        )

    def translate_input(
        self,
        *,
        run_id: str,
        messages: Sequence[Mapping[str, Any]],
        execution_context: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        normalized_messages = []
        for message in messages:
            role = str(message.get("role") or "user")
            content = str(message.get("content") or "")
            normalized_messages.append({"role": role, "content": content})
        return {
            "adapter_id": self.adapter_id,
            "framework_name": self.framework_name,
            "run_id": str(run_id),
            "messages": normalized_messages,
            "message_count": len(normalized_messages),
            "execution_context": dict(execution_context or {}),
        }

    def stream_events(
        self,
        *,
        translated_input: Mapping[str, Any],
        execution_context: Optional[Mapping[str, Any]] = None,
    ) -> Iterator[Dict[str, Any]]:
        run_id = str(translated_input.get("run_id") or "")
        event_factory = AgentEventFactory(run_id=run_id)
        merged_context = dict(translated_input.get("execution_context") or {})
        merged_context.update(dict(execution_context or {}))
        message_count = int(translated_input.get("message_count") or 0)
        yield event_factory.build(
            AgentEventType.STATUS,
            {
                "source": "framework_adapter",
                "adapter_id": self.adapter_id,
                "framework_name": self.framework_name,
                "status": "stream_started",
                "summary": f"{self.framework_name} adapter stream started",
                "detail": f"received {message_count} messages",
                "execution_context": merged_context,
            },
        ).to_dict()
        yield event_factory.build(
            AgentEventType.REASONING,
            {
                "source": "framework_adapter",
                "adapter_id": self.adapter_id,
                "framework_name": self.framework_name,
                "summary": "local fake adapter is planning next action",
                "detail": "phase_c2_local_pilot",
                "execution_context": merged_context,
            },
        ).to_dict()

    def translate_output(
        self,
        *,
        run_id: str,
        output: Any,
        execution_context: Optional[Mapping[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        content = output.get("content") if isinstance(output, Mapping) else output
        event = AgentEventFactory(run_id=run_id).build(
            AgentEventType.CONTENT,
            {
                "source": "framework_adapter",
                "adapter_id": self.adapter_id,
                "framework_name": self.framework_name,
                "content": "" if content is None else str(content),
                "summary": f"{self.framework_name} adapter output translated",
                "execution_context": dict(execution_context or {}),
            },
        )
        return [event.to_dict()]
