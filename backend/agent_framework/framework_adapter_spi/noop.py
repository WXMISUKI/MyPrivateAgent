"""Placeholder framework adapter implementation."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence

from ..events import AgentEventFactory, AgentEventType
from .base import AgentFrameworkAdapter
from .health import FrameworkAdapterHealth


class NoopFrameworkAdapter(AgentFrameworkAdapter):
    """Declarative adapter placeholder used to make the SPI visible before binding packages."""

    def __init__(
        self,
        *,
        adapter_id: str,
        framework_name: str,
        supported_run_kinds: Iterable[str] = ("chat",),
        capability_requirements: Iterable[str] = (),
        required_env: Iterable[str] = (),
        required_packages: Iterable[str] = (),
        detail: str = "Adapter SPI reserved; external framework package is not installed.",
    ):
        self.adapter_id = str(adapter_id)
        self.framework_name = str(framework_name)
        self.supported_run_kinds = tuple(str(item) for item in supported_run_kinds)
        self.capability_requirements = tuple(str(item) for item in capability_requirements)
        self.required_env = tuple(str(item) for item in required_env)
        self.required_packages = tuple(str(item) for item in required_packages)
        self.detail = str(detail)

    def health_check(self) -> FrameworkAdapterHealth:
        missing_env = tuple(
            item for item in self.required_env
            if not str(item or "").strip()
        )
        return FrameworkAdapterHealth(
            adapter_id=self.adapter_id,
            framework_name=self.framework_name,
            status="not_configured",
            detail=self.detail,
            supported_run_kinds=self.supported_run_kinds,
            capability_requirements=self.capability_requirements,
            package_installed=False,
            runtime_enabled=False,
            execution_mode="placeholder",
            required_env=self.required_env,
            execution_block_reason=self.detail,
            configuration_status="not_configured",
            missing_env=missing_env,
            missing_packages=self.required_packages,
            required_packages=self.required_packages,
        )

    def translate_input(
        self,
        *,
        run_id: str,
        messages: Sequence[Mapping[str, Any]],
        execution_context: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "framework_name": self.framework_name,
            "run_id": run_id,
            "messages": [dict(message) for message in messages],
            "execution_context": dict(execution_context or {}),
        }

    def stream_events(
        self,
        *,
        translated_input: Mapping[str, Any],
        execution_context: Optional[Mapping[str, Any]] = None,
    ) -> Iterator[Dict[str, Any]]:
        raise NotImplementedError(
            f"{self.adapter_id} is a Phase B SPI placeholder and cannot execute external framework runs."
        )

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
                "execution_context": dict(execution_context or {}),
            },
        )
        return [event.to_dict()]
