"""
工具型运行层适配器。

这是 Stage 1 的第二个最小 runtime-plane slice：
- 只验证一个受控工具的调用闭环
- 只验证 tool schema、tool result 和 normalized envelope
- 不引入审批分支和多智能体委派
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

from ..agents import Agent
from ..contracts import AgentManifest, ExecutionEvent, ExecutionRequest, ExecutionResult
from ..governance_bridge import build_runtime_plane_governance_projection
from .base import ExecutionAdapter


def _collect_last_assistant_message(state: dict[str, Any]) -> str:
    messages = list(state.get("messages") or [])
    for message in reversed(messages):
        if not isinstance(message, dict):
            continue
        if str(message.get("role") or "").strip().lower() == "assistant":
            return str(message.get("content") or "")
    return ""


def _collect_tool_calls(state: dict[str, Any]) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    for message in state.get("messages") or []:
        if not isinstance(message, dict):
            continue
        for tool_call in message.get("tool_calls") or []:
            if isinstance(tool_call, dict):
                calls.append(dict(tool_call))
    return calls


def _collect_last_tool_message(state: dict[str, Any]) -> str:
    messages = list(state.get("messages") or [])
    for message in reversed(messages):
        if not isinstance(message, dict):
            continue
        if str(message.get("role") or "").strip().lower() == "tool":
            return str(message.get("content") or "")
    return ""


@dataclass
class ToolAgentAdapter(ExecutionAdapter):
    """把一个本地 Agent 跑成标准化 tool execution envelope。"""

    agent: Agent
    model_call: Callable | None = None
    runtime_name: str = "local"
    governance_bridge: Any | None = None
    adapter_id: str = "tool_agent"
    _last_state: dict[str, Any] = field(default_factory=dict, init=False, repr=False)
    _last_events: list[ExecutionEvent] = field(default_factory=list, init=False, repr=False)

    def health_check(self) -> dict[str, Any]:
        tool_count = len(getattr(self.agent, "tools", []) or [])
        status = "ready" if self.agent and tool_count > 0 else "blocked"
        detail = "tool_agent adapter is ready" if status == "ready" else "at least one tool is required"
        return {
            "adapter_id": self.adapter_id,
            "runtime_name": self.runtime_name,
            "status": status,
            "detail": detail,
            "supported_run_kinds": ["tool_agent"],
            "adapter_type": "runtime_plane",
            "tool_count": tool_count,
        }

    def can_execute(self) -> tuple[bool, str]:
        if not self.agent:
            return False, "agent is required"
        if not getattr(self.agent, "tools", []):
            return False, "at least one tool is required"
        return True, ""

    def manifest(self) -> AgentManifest:
        return AgentManifest.from_agent(self.agent)

    def translate_input(self, request: ExecutionRequest) -> dict[str, Any]:
        return {
            "messages": [{"role": "user", "content": request.user_input}],
            "context": {
                "request_id": request.request_id,
                "agent_id": request.agent_id,
                "thread_id": request.thread_id,
                "runtime": request.runtime,
                "context_refs": list(request.context_refs),
            },
            "metadata": dict(request.metadata),
        }

    def stream_events(self, request: ExecutionRequest) -> Iterable[ExecutionEvent]:
        allowed, reason = self.can_execute()
        if not allowed:
            raise ValueError(reason)

        start_ts = time.time()
        run_id = request.request_id
        self._last_events = [
            ExecutionEvent.create(
                run_id=run_id,
                stage="planning",
                type="started",
                payload_summary=f"agent={request.agent_id}",
                raw_ref=request.request_id,
                metadata={"runtime": self.runtime_name},
                timestamp=start_ts,
            )
        ]
        yield self._last_events[0]

        state = self._execute(request)
        self._last_state = state

        tool_calls = _collect_tool_calls(state)
        tool_summary = ",".join(call.get("name", "") for call in tool_calls if call.get("name"))
        self._last_events.append(
            ExecutionEvent.create(
                run_id=run_id,
                stage="tool_calling",
                type="completed",
                payload_summary=tool_summary[:160] or "tool call completed",
                raw_ref=request.request_id,
                metadata={"tool_call_count": len(tool_calls)},
            )
        )
        yield self._last_events[-1]

        tool_observation = _collect_last_tool_message(state)
        self._last_events.append(
            ExecutionEvent.create(
                run_id=run_id,
                stage="observing",
                type="completed",
                payload_summary=tool_observation[:160] or "tool observation recorded",
                raw_ref=request.request_id,
                metadata={"tool_message_count": len([msg for msg in state.get("messages") or [] if isinstance(msg, dict) and str(msg.get("role") or "").strip().lower() == "tool"])},
            )
        )
        yield self._last_events[-1]

        self._last_events.append(
            ExecutionEvent.create(
                run_id=run_id,
                stage="finalizing",
                type="completed",
                payload_summary=f"status=success agent={request.agent_id}",
                raw_ref=request.request_id,
                metadata={"runtime": self.runtime_name},
            )
        )
        yield self._last_events[-1]

    def translate_output(
        self,
        request: ExecutionRequest,
        state: dict[str, Any],
        events: list[ExecutionEvent],
    ) -> ExecutionResult:
        assistant_text = _collect_last_assistant_message(state)
        tool_calls = _collect_tool_calls(state)
        trace_ref = request.request_id
        return ExecutionResult(
            status="success" if assistant_text or tool_calls else "completed",
            final_answer=assistant_text,
            artifacts=(),
            tool_calls=tuple(tool_calls),
            citations=(),
            trace_ref=trace_ref,
            metadata={
                "request_id": request.request_id,
                "agent_id": request.agent_id,
                "runtime": self.runtime_name,
                "event_count": len(events),
                "tool_call_count": len(tool_calls),
            },
        )

    def execute(self, request: ExecutionRequest) -> dict[str, Any]:
        events = list(self.stream_events(request))
        result = self.translate_output(request, self._last_state, events)
        manifest = self.manifest()
        return {
            "request": request.to_dict(),
            "manifest": manifest.to_dict(),
            "events": [event.to_dict() for event in events],
            "result": result.to_dict(),
            "governance_projection": build_runtime_plane_governance_projection(
                request=request,
                manifest=manifest,
                events=events,
                result=result,
                adapter_id=self.adapter_id,
            ),
            "state": dict(self._last_state),
        }

    def _execute(self, request: ExecutionRequest) -> dict[str, Any]:
        graph = self.agent.to_graph(model_call=self.model_call).compile()
        input_payload = self.translate_input(request)
        if self.governance_bridge:
            self.governance_bridge.on_run_start(request.request_id, request.agent_id, request.user_input)
        state = graph.invoke(input_payload)
        if self.governance_bridge:
            self.governance_bridge.on_run_end(
                request.request_id,
                {
                    "status": "success",
                    "final_answer": _collect_last_assistant_message(state),
                    "tool_call_count": len(_collect_tool_calls(state)),
                },
            )
        return state
