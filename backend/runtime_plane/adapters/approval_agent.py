"""
Approval-oriented runtime-plane adapter.

This Stage 1 slice proves that high-risk tool intent can be normalized into
an approval-pending envelope without executing the tool or creating production
approval state.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

from ..agents import Agent
from ..contracts import AgentManifest, ExecutionEvent, ExecutionRequest, ExecutionResult
from ..governance_bridge import build_runtime_plane_governance_projection
from ..tools import ToolDef
from .base import ExecutionAdapter


def _clean_str(value: Any) -> str:
    return str(value or "").strip()


def _approval_tool(tool_def: ToolDef | None) -> bool:
    if tool_def is None:
        return False
    permission = _clean_str(tool_def.permission_level).lower()
    risk = _clean_str(tool_def.risk_level).lower()
    return permission in {"ask", "approval_required", "high_risk"} or risk == "high"


def _tool_index(agent: Agent) -> dict[str, ToolDef]:
    return {tool.name: tool for tool in getattr(agent, "tools", []) or [] if isinstance(tool, ToolDef)}


def _approval_args_summary(args: Any) -> dict[str, Any]:
    if not isinstance(args, dict):
        return {"kind": type(args).__name__, "field_count": 0, "fields": []}
    fields = sorted(str(key) for key in args.keys())
    return {
        "kind": "object",
        "field_count": len(fields),
        "fields": fields[:20],
    }


def _collect_tool_calls(message: dict[str, Any]) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    for tool_call in message.get("tool_calls") or []:
        if isinstance(tool_call, dict):
            calls.append(dict(tool_call))
    return calls


@dataclass
class ApprovalAgentAdapter(ExecutionAdapter):
    """Normalize high-risk tool intent into an approval interrupt envelope."""

    agent: Agent
    model_call: Callable | None = None
    runtime_name: str = "local"
    governance_bridge: Any | None = None
    adapter_id: str = "approval_agent"
    _last_state: dict[str, Any] = field(default_factory=dict, init=False, repr=False)
    _last_events: list[ExecutionEvent] = field(default_factory=list, init=False, repr=False)

    def health_check(self) -> dict[str, Any]:
        approval_tools = self._approval_tools()
        status = "ready" if self.agent and approval_tools else "blocked"
        detail = "approval_agent adapter is ready" if status == "ready" else "at least one approval-capable tool is required"
        return {
            "adapter_id": self.adapter_id,
            "runtime_name": self.runtime_name,
            "status": status,
            "detail": detail,
            "supported_run_kinds": ["approval_agent"],
            "adapter_type": "runtime_plane",
            "approval_tool_count": len(approval_tools),
        }

    def can_execute(self) -> tuple[bool, str]:
        if not self.agent:
            return False, "agent is required"
        if not self._approval_tools():
            return False, "approval_capable_tool_required"
        if self.model_call is None:
            return False, "model_call is required"
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

        state = self._plan_once(request)
        self._last_state = state

        approval_request = state.get("approval_request")
        if isinstance(approval_request, dict):
            self._last_events.append(
                ExecutionEvent.create(
                    run_id=run_id,
                    stage="approval",
                    type="approval_required",
                    payload_summary=f"tool={approval_request.get('tool_name')} reason={approval_request.get('approval_reason')}",
                    raw_ref=request.request_id,
                    metadata=dict(approval_request),
                )
            )
            yield self._last_events[-1]
            return

        assistant_text = str((state.get("messages") or [{}])[-1].get("content") or "")
        self._last_events.append(
            ExecutionEvent.create(
                run_id=run_id,
                stage="generating",
                type="completed",
                payload_summary=assistant_text[:160] or "assistant response generated",
                raw_ref=request.request_id,
                metadata={"message_count": len(state.get("messages") or [])},
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
        approval_request = state.get("approval_request")
        if isinstance(approval_request, dict):
            return ExecutionResult(
                status="approval_pending",
                final_answer="",
                artifacts=(),
                tool_calls=tuple(state.get("tool_calls") or ()),
                citations=(),
                trace_ref=request.request_id,
                metadata={
                    "request_id": request.request_id,
                    "agent_id": request.agent_id,
                    "runtime": self.runtime_name,
                    "event_count": len(events),
                    "approval_request": dict(approval_request),
                },
            )

        assistant_text = str((state.get("messages") or [{}])[-1].get("content") or "")
        return ExecutionResult(
            status="success" if assistant_text else "completed",
            final_answer=assistant_text,
            artifacts=(),
            tool_calls=tuple(state.get("tool_calls") or ()),
            citations=(),
            trace_ref=request.request_id,
            metadata={
                "request_id": request.request_id,
                "agent_id": request.agent_id,
                "runtime": self.runtime_name,
                "event_count": len(events),
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

    def _approval_tools(self) -> list[ToolDef]:
        return [tool for tool in getattr(self.agent, "tools", []) or [] if _approval_tool(tool)]

    def _plan_once(self, request: ExecutionRequest) -> dict[str, Any]:
        input_payload = self.translate_input(request)
        messages = list(input_payload["messages"])
        if self.governance_bridge:
            self.governance_bridge.on_run_start(request.request_id, request.agent_id, request.user_input)

        response = self.model_call(messages, tools=getattr(self.agent, "tools", []) or [])
        if not isinstance(response, dict):
            response = {"role": "assistant", "content": str(response)}
        messages.append(response)

        tool_calls = _collect_tool_calls(response)
        approval_request = self._build_approval_request(request, tool_calls)
        state: dict[str, Any] = {
            "messages": messages,
            "tool_calls": tool_calls,
        }
        if approval_request:
            state["approval_request"] = approval_request
            if self.governance_bridge:
                self.governance_bridge.on_run_end(
                    request.request_id,
                    {
                        "status": "approval_pending",
                        "approval_request": approval_request,
                    },
                )
            return state

        if self.governance_bridge:
            self.governance_bridge.on_run_end(
                request.request_id,
                {
                    "status": "success",
                    "final_answer": str(response.get("content") or ""),
                },
            )
        return state

    def _build_approval_request(
        self,
        request: ExecutionRequest,
        tool_calls: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        tools = _tool_index(self.agent)
        for call in tool_calls:
            tool_name = _clean_str(call.get("name"))
            tool_def = tools.get(tool_name)
            if not _approval_tool(tool_def):
                continue
            return {
                "request_id": request.request_id,
                "agent_id": request.agent_id,
                "tool_name": tool_name,
                "tool_call_id": _clean_str(call.get("id")) or None,
                "risk_level": _clean_str(tool_def.risk_level).lower(),
                "permission_level": _clean_str(tool_def.permission_level).lower(),
                "approval_reason": "high_risk_tool_intent",
                "args_summary": _approval_args_summary(call.get("args")),
                "will_execute": False,
                "production_approval_submitted": False,
            }
        return None
