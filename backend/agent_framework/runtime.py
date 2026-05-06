"""Runtime state and execution context."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class AgentState(str, Enum):
    """Explicit agent execution states."""

    INIT = "init"
    PLANNING = "planning"
    GENERATING = "generating"
    TOOL_CALLING = "tool_calling"
    WAITING_APPROVAL = "waiting_approval"
    WAITING_PERMISSION = "waiting_permission"
    OBSERVING = "observing"
    MERGING = "merging"
    FINALIZING = "finalizing"
    DONE = "done"
    FAILED = "failed"
    ABORTED = "aborted"


class AgentRunKind(str, Enum):
    """Top-level run categories for execution tracking."""

    CHAT = "chat"
    PLANNER = "planner"
    CHILD = "child"
    BACKGROUND = "background"
    GOVERNANCE = "governance"


_STATE_TRANSITIONS: dict[AgentState, set[AgentState]] = {
    AgentState.INIT: {AgentState.PLANNING, AgentState.GENERATING, AgentState.FAILED, AgentState.ABORTED},
    AgentState.PLANNING: {
        AgentState.GENERATING,
        AgentState.TOOL_CALLING,
        AgentState.WAITING_APPROVAL,
        AgentState.WAITING_PERMISSION,
        AgentState.FINALIZING,
        AgentState.FAILED,
        AgentState.ABORTED,
    },
    AgentState.GENERATING: {
        AgentState.TOOL_CALLING,
        AgentState.WAITING_APPROVAL,
        AgentState.WAITING_PERMISSION,
        AgentState.OBSERVING,
        AgentState.MERGING,
        AgentState.FINALIZING,
        AgentState.DONE,
        AgentState.FAILED,
        AgentState.ABORTED,
    },
    AgentState.TOOL_CALLING: {
        AgentState.WAITING_APPROVAL,
        AgentState.WAITING_PERMISSION,
        AgentState.OBSERVING,
        AgentState.MERGING,
        AgentState.FINALIZING,
        AgentState.FAILED,
        AgentState.ABORTED,
    },
    AgentState.WAITING_APPROVAL: {
        AgentState.TOOL_CALLING,
        AgentState.OBSERVING,
        AgentState.MERGING,
        AgentState.FINALIZING,
        AgentState.FAILED,
        AgentState.ABORTED,
    },
    AgentState.WAITING_PERMISSION: {
        AgentState.TOOL_CALLING,
        AgentState.OBSERVING,
        AgentState.MERGING,
        AgentState.FINALIZING,
        AgentState.FAILED,
        AgentState.ABORTED,
    },
    AgentState.OBSERVING: {
        AgentState.GENERATING,
        AgentState.MERGING,
        AgentState.FINALIZING,
        AgentState.DONE,
        AgentState.FAILED,
        AgentState.ABORTED,
    },
    AgentState.MERGING: {
        AgentState.GENERATING,
        AgentState.FINALIZING,
        AgentState.DONE,
        AgentState.FAILED,
        AgentState.ABORTED,
    },
    AgentState.FINALIZING: {AgentState.DONE, AgentState.FAILED, AgentState.ABORTED},
    AgentState.DONE: {AgentState.DONE, AgentState.FAILED, AgentState.ABORTED},
    AgentState.FAILED: {AgentState.FAILED, AgentState.ABORTED},
    AgentState.ABORTED: {AgentState.ABORTED, AgentState.FAILED},
}


@dataclass
class AgentRunContext:
    """Mutable execution context that survives across loop iterations."""

    conversation_id: Optional[int] = None
    user_id: Optional[int] = None
    model_name: str = "unknown"
    run_id: str = field(default_factory=lambda: f"run_{uuid4().hex}")
    parent_run_id: Optional[str] = None
    run_kind: AgentRunKind = AgentRunKind.CHAT
    state: AgentState = AgentState.INIT
    iteration: int = 0
    stop_reason: Optional[str] = None
    tool_history: List[Dict[str, Any]] = field(default_factory=list)
    state_history: List[Dict[str, Any]] = field(default_factory=list)
    last_state_transition: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def begin_iteration(self) -> int:
        self.iteration += 1
        self.transition_to(AgentState.GENERATING)
        return self.iteration

    def set_state(self, state: AgentState, *, stop_reason: Optional[str] = None) -> Dict[str, Any]:
        return self.transition_to(state, stop_reason=stop_reason)

    def transition_to(self, state: AgentState, *, stop_reason: Optional[str] = None) -> Dict[str, Any]:
        if not isinstance(state, AgentState):
            state = AgentState(str(state))
        previous_state = self.state
        if state != previous_state and state not in _STATE_TRANSITIONS.get(previous_state, set()):
            raise ValueError(f"非法状态迁移: {previous_state.value} -> {state.value}")
        self.state = state
        if stop_reason is not None:
            self.stop_reason = stop_reason
        transition = {
            "previous_state": previous_state.value,
            "state": self.state.value,
            "stop_reason": self.stop_reason,
            "iteration": self.iteration,
        }
        self.last_state_transition = transition
        self.state_history.append(dict(transition))
        self.metadata["last_state_transition"] = dict(transition)
        self.metadata["state_history"] = list(self.state_history)
        return transition

    def snapshot(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "parent_run_id": self.parent_run_id,
            "run_kind": self.run_kind.value,
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "model_name": self.model_name,
            "state": self.state.value,
            "iteration": self.iteration,
            "stop_reason": self.stop_reason,
            "tool_history": list(self.tool_history),
            "state_history": list(self.state_history),
            "metadata": dict(self.metadata),
        }

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
