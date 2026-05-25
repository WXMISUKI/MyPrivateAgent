"""Base SPI for external framework adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Mapping, Optional, Sequence

from .health import FrameworkAdapterHealth


class AgentFrameworkAdapter(ABC):
    """Stable SPI boundary for LangGraph / DeepAgents-style / CrewAI-style adapters."""

    adapter_id: str
    framework_name: str
    supported_run_kinds: Sequence[str]
    capability_requirements: Sequence[str]

    @abstractmethod
    def health_check(self) -> FrameworkAdapterHealth:
        """Return adapter health without invoking the external framework."""

    @abstractmethod
    def translate_input(
        self,
        *,
        run_id: str,
        messages: Sequence[Mapping[str, Any]],
        execution_context: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Translate platform input into the external framework's input shape."""

    @abstractmethod
    def stream_events(
        self,
        *,
        translated_input: Mapping[str, Any],
        execution_context: Optional[Mapping[str, Any]] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Stream framework events after translating them to platform event dicts."""

    @abstractmethod
    def translate_output(
        self,
        *,
        run_id: str,
        output: Any,
        execution_context: Optional[Mapping[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Translate the framework's final output into Phase A AgentEvent dictionaries."""

    def can_execute(self) -> tuple[bool, str]:
        health = self.health_check()
        return (
            bool(health.package_installed and health.runtime_enabled),
            str(health.execution_block_reason or health.detail or "").strip(),
        )
