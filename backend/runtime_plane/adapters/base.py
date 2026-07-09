"""Execution adapter 基类与协议。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable

from ..contracts import ExecutionEvent, ExecutionRequest, ExecutionResult


class ExecutionAdapter(ABC):
    """统一运行层适配器抽象。"""

    adapter_id: str = "unknown"
    runtime_name: str = "unknown"

    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def can_execute(self) -> tuple[bool, str]:
        raise NotImplementedError

    @abstractmethod
    def translate_input(self, request: ExecutionRequest) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def stream_events(self, request: ExecutionRequest) -> Iterable[ExecutionEvent]:
        raise NotImplementedError

    @abstractmethod
    def translate_output(
        self,
        request: ExecutionRequest,
        state: dict[str, Any],
        events: list[ExecutionEvent],
    ) -> ExecutionResult:
        raise NotImplementedError
