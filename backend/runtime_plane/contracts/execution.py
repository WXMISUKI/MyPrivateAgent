"""
ExecutionAdapter 标准合同。

这组合同定义运行层与治理层之间的标准化通信 envelope：
- ExecutionRequest: 执行请求
- ExecutionEvent: 执行事件
- ExecutionResult: 执行结果
- AgentManifest: Agent 清单
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Mapping


def _clean_str(value: Any) -> str:
    return str(value or "").strip()


def _to_tuple(values: Any) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, tuple):
        return tuple(_clean_str(value) for value in values if _clean_str(value))
    if isinstance(values, list):
        return tuple(_clean_str(value) for value in values if _clean_str(value))
    cleaned = _clean_str(values)
    return (cleaned,) if cleaned else ()


def _to_dict(value: Any) -> dict[str, Any]:
    return dict(value or {})


@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    request_id: str
    agent_id: str
    user_input: str
    thread_id: str | None = None
    runtime: str = "local"
    context_refs: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        request_id = _clean_str(self.request_id)
        agent_id = _clean_str(self.agent_id)
        user_input = _clean_str(self.user_input)
        runtime = _clean_str(self.runtime) or "local"
        thread_id = _clean_str(self.thread_id) or None
        context_refs = _to_tuple(self.context_refs)
        metadata = _to_dict(self.metadata)

        if not request_id:
            raise ValueError("request_id is required")
        if not agent_id:
            raise ValueError("agent_id is required")
        if not user_input:
            raise ValueError("user_input is required")

        object.__setattr__(self, "request_id", request_id)
        object.__setattr__(self, "agent_id", agent_id)
        object.__setattr__(self, "user_input", user_input)
        object.__setattr__(self, "thread_id", thread_id)
        object.__setattr__(self, "runtime", runtime)
        object.__setattr__(self, "context_refs", context_refs)
        object.__setattr__(self, "metadata", metadata)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "agent_id": self.agent_id,
            "user_input": self.user_input,
            "thread_id": self.thread_id,
            "runtime": self.runtime,
            "context_refs": list(self.context_refs),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ExecutionEvent:
    event_id: str
    run_id: str
    stage: str
    type: str
    payload_summary: str
    raw_ref: str | None = None
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        event_id = _clean_str(self.event_id)
        run_id = _clean_str(self.run_id)
        stage = _clean_str(self.stage)
        event_type = _clean_str(self.type)
        payload_summary = _clean_str(self.payload_summary)
        raw_ref = _clean_str(self.raw_ref) or None
        metadata = _to_dict(self.metadata)

        if not event_id:
            raise ValueError("event_id is required")
        if not run_id:
            raise ValueError("run_id is required")
        if not stage:
            raise ValueError("stage is required")
        if not event_type:
            raise ValueError("type is required")

        object.__setattr__(self, "event_id", event_id)
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "stage", stage)
        object.__setattr__(self, "type", event_type)
        object.__setattr__(self, "payload_summary", payload_summary)
        object.__setattr__(self, "raw_ref", raw_ref)
        object.__setattr__(self, "timestamp", float(self.timestamp))
        object.__setattr__(self, "metadata", metadata)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "run_id": self.run_id,
            "stage": self.stage,
            "type": self.type,
            "payload_summary": self.payload_summary,
            "raw_ref": self.raw_ref,
            "timestamp": self.timestamp,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def create(
        cls,
        *,
        run_id: str,
        stage: str,
        type: str,
        payload_summary: str,
        raw_ref: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        event_id: str | None = None,
        timestamp: float | None = None,
    ) -> "ExecutionEvent":
        return cls(
            event_id=event_id or f"{run_id}:{stage}:{type}:{int(time.time() * 1000)}",
            run_id=run_id,
            stage=stage,
            type=type,
            payload_summary=payload_summary,
            raw_ref=raw_ref,
            timestamp=timestamp if timestamp is not None else time.time(),
            metadata=dict(metadata or {}),
        )


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    status: str
    final_answer: str
    artifacts: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    tool_calls: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    citations: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    trace_ref: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        status = _clean_str(self.status)
        final_answer = _clean_str(self.final_answer)
        artifacts = tuple(_to_dict(item) for item in (self.artifacts or ()))
        tool_calls = tuple(_to_dict(item) for item in (self.tool_calls or ()))
        citations = tuple(_to_dict(item) for item in (self.citations or ()))
        trace_ref = _clean_str(self.trace_ref)
        metadata = _to_dict(self.metadata)

        if not status:
            raise ValueError("status is required")

        object.__setattr__(self, "status", status)
        object.__setattr__(self, "final_answer", final_answer)
        object.__setattr__(self, "artifacts", artifacts)
        object.__setattr__(self, "tool_calls", tool_calls)
        object.__setattr__(self, "citations", citations)
        object.__setattr__(self, "trace_ref", trace_ref)
        object.__setattr__(self, "metadata", metadata)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "final_answer": self.final_answer,
            "artifacts": [dict(item) for item in self.artifacts],
            "tool_calls": [dict(item) for item in self.tool_calls],
            "citations": [dict(item) for item in self.citations],
            "trace_ref": self.trace_ref,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class AgentManifest:
    agent_id: str
    role: str = ""
    capabilities: tuple[str, ...] = field(default_factory=tuple)
    governance_boundaries: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        agent_id = _clean_str(self.agent_id)
        role = _clean_str(self.role)
        capabilities = _to_tuple(self.capabilities)
        governance_boundaries = _to_tuple(self.governance_boundaries)
        metadata = _to_dict(self.metadata)

        if not agent_id:
            raise ValueError("agent_id is required")

        object.__setattr__(self, "agent_id", agent_id)
        object.__setattr__(self, "role", role)
        object.__setattr__(self, "capabilities", capabilities)
        object.__setattr__(self, "governance_boundaries", governance_boundaries)
        object.__setattr__(self, "metadata", metadata)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "capabilities": list(self.capabilities),
            "governance_boundaries": list(self.governance_boundaries),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_agent(
        cls,
        agent: Any,
        *,
        role: str | None = None,
        governance_boundaries: Any = None,
    ) -> "AgentManifest":
        to_agent_card = getattr(agent, "to_agent_card", None)
        card = dict(to_agent_card() or {}) if callable(to_agent_card) else {}
        metadata = dict(getattr(agent, "metadata", {}) or {})
        metadata.update(card.get("metadata") or {})
        return cls(
            agent_id=str(card.get("agent_id") or getattr(agent, "name", "") or "").strip(),
            role=str(role or metadata.get("role") or ""),
            capabilities=tuple(card.get("capabilities") or ()),
            governance_boundaries=_to_tuple(
                governance_boundaries if governance_boundaries is not None else metadata.get("governance_boundaries")
            ),
            metadata=metadata,
        )
