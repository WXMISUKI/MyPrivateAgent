"""Runtime state and execution context."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class AgentState(str, Enum):
    """Explicit agent execution states."""

    INIT = "init"
    GENERATING = "generating"
    TOOL_CALLING = "tool_calling"
    WAITING_PERMISSION = "waiting_permission"
    OBSERVING = "observing"
    FINALIZING = "finalizing"
    DONE = "done"
    FAILED = "failed"
    ABORTED = "aborted"


@dataclass
class AgentRunContext:
    """Mutable execution context that survives across loop iterations."""

    conversation_id: Optional[int] = None
    user_id: Optional[int] = None
    model_name: str = "unknown"
    run_id: str = field(default_factory=lambda: f"run_{uuid4().hex}")
    state: AgentState = AgentState.INIT
    iteration: int = 0
    stop_reason: Optional[str] = None
    tool_history: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def begin_iteration(self) -> int:
        self.iteration += 1
        self.state = AgentState.GENERATING
        return self.iteration

    def set_state(self, state: AgentState, *, stop_reason: Optional[str] = None) -> None:
        self.state = state
        if stop_reason is not None:
            self.stop_reason = stop_reason

    def record_tool_result(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: str,
        tool_call_id: str,
        *,
        execution: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.tool_history.append(
            {
                "tool_name": tool_name,
                "args": dict(args),
                "result": result,
                "tool_call_id": tool_call_id,
                "iteration": self.iteration,
                "execution": dict(execution or {}),
            }
        )
