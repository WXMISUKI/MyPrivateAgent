"""Structured runtime events for agent execution."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Union


class AgentEventType(str, Enum):
    """Canonical event types emitted by the runtime."""

    STATUS = "status"
    REASONING = "reasoning"
    CONTENT = "content"
    TOOL_CALL_START = "tool_call_start"
    TOOL_RESULT = "tool_result"
    TOOL_PERMISSION_REQUIRED = "tool_permission_required"
    TOOL_DENIED = "tool_denied"
    PLAN_UPDATED = "plan_updated"
    DONE = "done"
    ERROR = "error"


@dataclass(frozen=True)
class AgentEvent:
    """A single runtime event with backward-compatible payload flattening."""

    type: str
    run_id: str
    conversation_id: Optional[int] = None
    iteration: Optional[int] = None
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "type": self.type,
            "run_id": self.run_id,
            "conversation_id": self.conversation_id,
            "iteration": self.iteration,
            "payload": dict(self.payload),
        }
        for key, value in self.payload.items():
            if key not in data:
                data[key] = value
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False) + "\n"


class AgentEventFactory:
    """Builds consistent agent events for a single run."""

    def __init__(self, run_id: str, conversation_id: Optional[int] = None):
        self.run_id = run_id
        self.conversation_id = conversation_id

    def build(
        self,
        event_type: Union[AgentEventType, str],
        payload: Optional[Dict[str, Any]] = None,
        *,
        iteration: Optional[int] = None,
    ) -> AgentEvent:
        event_name = event_type.value if isinstance(event_type, AgentEventType) else str(event_type)
        return AgentEvent(
            type=event_name,
            run_id=self.run_id,
            conversation_id=self.conversation_id,
            iteration=iteration,
            payload=payload or {},
        )
