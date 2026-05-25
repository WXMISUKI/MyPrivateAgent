"""Minimal execution loop controller for harness-style agent runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable

from .events import AgentEventFactory, AgentEventType
from .runtime import AgentRunContext, AgentState


@dataclass(frozen=True)
class ExecutionLoopStep:
    """A single observable transition in the minimal harness loop."""

    name: str
    state: AgentState
    summary: str
    stop_reason: str | None = None


@dataclass(frozen=True)
class ExecutionReviewResult:
    """Normalized review result emitted by the execution loop."""

    reviewer: str = "default"
    status: str = "approved"
    summary: str = ""
    findings: tuple[str, ...] = ()
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reviewer": str(self.reviewer or "default").strip() or "default",
            "status": _normalize_review_status(self.status),
            "summary": str(self.summary or "").strip(),
            "findings": [str(item) for item in self.findings if str(item).strip()],
            "metadata": dict(self.metadata or {}),
        }


@dataclass(frozen=True)
class ExecutionReflectionResult:
    """Normalized reflection result emitted after observation."""

    reflector: str = "default"
    status: str = "accepted"
    summary: str = ""
    observations: tuple[str, ...] = ()
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reflector": str(self.reflector or "default").strip() or "default",
            "status": _normalize_reflection_status(self.status),
            "summary": str(self.summary or "").strip(),
            "observations": [str(item) for item in self.observations if str(item).strip()],
            "metadata": dict(self.metadata or {}),
        }


@dataclass(frozen=True)
class ExecutionToolResult:
    """Normalized tool execution result emitted by the loop act stage."""

    tool_name: str
    result: str
    args: Dict[str, Any] = field(default_factory=dict)
    tool_call_id: str = ""
    execution: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": str(self.tool_name or "").strip() or "unknown_tool",
            "args": dict(self.args or {}),
            "result": str(self.result or ""),
            "tool_call_id": str(self.tool_call_id or "").strip(),
            "execution": dict(self.execution or {}),
        }


@dataclass(frozen=True)
class ExecutionToolDecision:
    """Governance decision evaluated before the loop act stage."""

    status: str = "allowed"
    tool_name: str = ""
    tool_args: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": _normalize_tool_decision_status(self.status),
            "tool_name": str(self.tool_name or "").strip() or "unknown_tool",
            "tool_args": dict(self.tool_args or {}),
            "reason": str(self.reason or "").strip(),
            "metadata": dict(self.metadata or {}),
        }


@dataclass(frozen=True)
class ExecutionFallbackResult:
    """Normalized fallback decision emitted when a loop callable fails."""

    strategy: str = "fail_closed"
    status: str = "failed"
    summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": str(self.strategy or "fail_closed").strip() or "fail_closed",
            "status": _normalize_fallback_status(self.status),
            "summary": str(self.summary or "").strip(),
            "metadata": dict(self.metadata or {}),
        }


DEFAULT_MINIMAL_LOOP_STEPS = (
    ExecutionLoopStep("planning", AgentState.PLANNING, "Execution loop entered planning"),
    ExecutionLoopStep("generating", AgentState.GENERATING, "Execution loop entered generation"),
    ExecutionLoopStep("observing", AgentState.OBSERVING, "Execution loop observed current result", "loop_observed"),
    ExecutionLoopStep("finalizing", AgentState.FINALIZING, "Execution loop entered finalization", "loop_finalizing"),
    ExecutionLoopStep("done", AgentState.DONE, "Execution loop completed", "loop_completed"),
)


ReviewCallable = Callable[[AgentRunContext], ExecutionReviewResult | Dict[str, Any] | None]
ReflectionCallable = Callable[[AgentRunContext], ExecutionReflectionResult | Dict[str, Any] | None]
ToolExecutorCallable = Callable[[AgentRunContext], ExecutionToolResult | Dict[str, Any] | None]
ToolPolicyCallable = Callable[[AgentRunContext], ExecutionToolDecision | Dict[str, Any] | None]
FallbackCallable = Callable[[Exception, AgentRunContext], ExecutionFallbackResult | Dict[str, Any] | None]


class ExecutionLoopController:
    """Drive a run through a small, evented harness loop.

    This controller is intentionally conservative: it only owns loop state
    transitions and event envelopes. Model calls, tool execution, review, and
    fallback policies should attach to this seam later instead of being hidden
    inside SDK or facade methods.
    """

    def __init__(
        self,
        steps: Iterable[ExecutionLoopStep] | None = None,
        *,
        tool_policy: ToolPolicyCallable | None = None,
        tool_executor: ToolExecutorCallable | None = None,
        reflector: ReflectionCallable | None = None,
        reviewer: ReviewCallable | None = None,
        fallback_handler: FallbackCallable | None = None,
        fail_on_review_rejection: bool = True,
        max_iterations: int = 1,
    ) -> None:
        self.steps = tuple(steps or DEFAULT_MINIMAL_LOOP_STEPS)
        self.tool_policy = tool_policy
        self.tool_executor = tool_executor
        self.reflector = reflector
        self.reviewer = reviewer
        self.fallback_handler = fallback_handler
        self.fail_on_review_rejection = fail_on_review_rejection
        self.max_iterations = max(1, int(max_iterations or 1))

    def run_until_stop(
        self,
        run_context: AgentRunContext,
        *,
        event_factory: AgentEventFactory,
        append_event: Callable[[Dict[str, Any]], None],
    ) -> Dict[str, Any]:
        if run_context.state in {AgentState.DONE, AgentState.FAILED, AgentState.ABORTED}:
            raise ValueError(f"run `{run_context.run_id}` is already terminal: {run_context.state.value}.")

        produced_events: list[Dict[str, Any]] = []
        completed_steps: list[str] = []
        step_index = 0
        while step_index < len(self.steps):
            step = self.steps[step_index]
            previous_state = run_context.state.value
            if step.state == AgentState.GENERATING:
                iteration = run_context.begin_iteration()
                transition = run_context.last_state_transition
            else:
                transition = run_context.transition_to(step.state, stop_reason=step.stop_reason)
                iteration = run_context.iteration

            state_event = event_factory.build_state_event(
                previous_state=previous_state,
                state=transition["state"],
                stop_reason=transition["stop_reason"],
                iteration=iteration,
            ).to_dict()
            self._append(append_event, produced_events, state_event)

            completed_steps.append(step.name)
            review_result = None
            if step.state == AgentState.FINALIZING and self.reviewer is not None:
                try:
                    review_result = self._run_review(run_context)
                except Exception as exc:  # pragma: no cover - exact exception type belongs to caller.
                    fallback_result = self._handle_exception(
                        exc,
                        run_context=run_context,
                        event_factory=event_factory,
                        append_event=append_event,
                        produced_events=produced_events,
                        iteration=iteration,
                        loop_step=step.name,
                    )
                    if fallback_result["status"] == "handled":
                        completed_steps.append("fallback")
                        step_index += 1
                        continue
                    completed_steps.append("fallback")
                    run_context.metadata["execution_loop"] = {
                        "controller": "minimal",
                        "completed": False,
                        "steps": list(completed_steps),
                        "stop_reason": "loop_exception",
                    }
                    return {
                        "run": run_context.snapshot(),
                        "events": produced_events,
                    }
                run_context.metadata["execution_review"] = dict(review_result)
                review_event = event_factory.build(
                    AgentEventType.STATUS,
                    {
                        "status_kind": "execution_loop_reviewed",
                        "summary": review_result.get("summary") or "Execution loop review completed",
                        "loop_step": step.name,
                        "review": dict(review_result),
                    },
                    iteration=iteration,
                ).to_dict()
                self._append(append_event, produced_events, review_event)
                if review_result["status"] == "rejected" and self.fail_on_review_rejection:
                    failed_transition = run_context.transition_to(AgentState.FAILED, stop_reason="review_rejected")
                    failed_state_event = event_factory.build_state_event(
                        previous_state=failed_transition["previous_state"],
                        state=failed_transition["state"],
                        stop_reason=failed_transition["stop_reason"],
                        iteration=iteration,
                    ).to_dict()
                    self._append(append_event, produced_events, failed_state_event)
                    rejected_event = event_factory.build(
                        AgentEventType.ERROR,
                        {
                            "status_kind": "execution_loop_review_rejected",
                            "summary": review_result.get("summary") or "Execution loop review rejected the run",
                            "loop_step": step.name,
                            "review": dict(review_result),
                        },
                        iteration=iteration,
                    ).to_dict()
                    self._append(append_event, produced_events, rejected_event)
                    run_context.metadata["execution_loop"] = {
                        "controller": "minimal",
                        "completed": False,
                        "steps": list(completed_steps),
                        "stop_reason": "review_rejected",
                    }
                    return {
                        "run": run_context.snapshot(),
                        "events": produced_events,
                    }

            if step.state == AgentState.DONE:
                done_event = event_factory.build(
                    AgentEventType.DONE,
                    {
                        "status_kind": "execution_loop_done",
                        "summary": step.summary,
                        "loop_step": step.name,
                        "completed_steps": list(completed_steps),
                        "run": run_context.snapshot(),
                    },
                    iteration=iteration,
                ).to_dict()
                self._append(append_event, produced_events, done_event)
            else:
                status_event = event_factory.build(
                    AgentEventType.STATUS,
                    {
                        "status_kind": "execution_loop_step",
                        "summary": step.summary,
                        "loop_step": step.name,
                        "state": step.state.value,
                    },
                    iteration=iteration,
                ).to_dict()
                self._append(append_event, produced_events, status_event)

            if step.state == AgentState.GENERATING and self.tool_executor is not None:
                tool_decision = self._run_tool_policy(run_context)
                if tool_decision is not None and tool_decision["status"] == "approval_required":
                    run_context.metadata["execution_tool_decision"] = dict(tool_decision)
                    approval_transition = run_context.transition_to(
                        AgentState.WAITING_APPROVAL,
                        stop_reason="tool_approval_required",
                    )
                    approval_state_event = event_factory.build_state_event(
                        previous_state=approval_transition["previous_state"],
                        state=approval_transition["state"],
                        stop_reason=approval_transition["stop_reason"],
                        iteration=iteration,
                    ).to_dict()
                    self._append(append_event, produced_events, approval_state_event)
                    permission_event = event_factory.build(
                        AgentEventType.TOOL_PERMISSION_REQUIRED,
                        {
                            "status_kind": "tool_permission_required",
                            "tool_name": tool_decision["tool_name"],
                            "reason": tool_decision["reason"],
                            "tool_decision": dict(tool_decision),
                        },
                        iteration=iteration,
                    ).to_dict()
                    self._append(append_event, produced_events, permission_event)
                    completed_steps.append("tool_approval_required")
                    run_context.metadata["execution_loop"] = {
                        "controller": "minimal",
                        "completed": False,
                        "steps": list(completed_steps),
                        "stop_reason": "tool_approval_required",
                    }
                    return {
                        "run": run_context.snapshot(),
                        "events": produced_events,
                    }
                if tool_decision is not None and tool_decision["status"] == "denied":
                    run_context.metadata["execution_tool_decision"] = dict(tool_decision)
                    denied_transition = run_context.transition_to(
                        AgentState.FAILED,
                        stop_reason="tool_policy_denied",
                    )
                    denied_state_event = event_factory.build_state_event(
                        previous_state=denied_transition["previous_state"],
                        state=denied_transition["state"],
                        stop_reason=denied_transition["stop_reason"],
                        iteration=iteration,
                    ).to_dict()
                    self._append(append_event, produced_events, denied_state_event)
                    denied_event = event_factory.build(
                        AgentEventType.ERROR,
                        {
                            "status_kind": "tool_permission_denied",
                            "tool_name": tool_decision["tool_name"],
                            "reason": tool_decision["reason"],
                            "tool_decision": dict(tool_decision),
                        },
                        iteration=iteration,
                    ).to_dict()
                    self._append(append_event, produced_events, denied_event)
                    completed_steps.append("tool_policy_denied")
                    run_context.metadata["execution_loop"] = {
                        "controller": "minimal",
                        "completed": False,
                        "steps": list(completed_steps),
                        "stop_reason": "tool_policy_denied",
                    }
                    return {
                        "run": run_context.snapshot(),
                        "events": produced_events,
                    }
                tool_result = self._run_tool_executor(run_context)
                if tool_result is not None:
                    tool_transition = run_context.transition_to(AgentState.TOOL_CALLING, stop_reason="tool_calling")
                    tool_state_event = event_factory.build_state_event(
                        previous_state=tool_transition["previous_state"],
                        state=tool_transition["state"],
                        stop_reason=tool_transition["stop_reason"],
                        iteration=iteration,
                    ).to_dict()
                    self._append(append_event, produced_events, tool_state_event)
                    completed_steps.append("tool_calling")
                    tool_call_id = tool_result.get("tool_call_id") or f"tool_{run_context.iteration}_{len(run_context.tool_history) + 1}"
                    tool_result["tool_call_id"] = tool_call_id
                    start_event = event_factory.build(
                        AgentEventType.TOOL_CALL_START,
                        {
                            "status_kind": "tool_call_started",
                            "tool_name": tool_result["tool_name"],
                            "args": dict(tool_result["args"]),
                            "tool_call_id": tool_call_id,
                        },
                        iteration=iteration,
                    ).to_dict()
                    self._append(append_event, produced_events, start_event)
                    run_context.record_tool_result(
                        tool_result["tool_name"],
                        dict(tool_result["args"]),
                        str(tool_result["result"]),
                        tool_call_id,
                        execution=dict(tool_result.get("execution") or {}),
                    )
                    result_event = event_factory.build(
                        AgentEventType.TOOL_RESULT,
                        {
                            "status_kind": "tool_result",
                            "tool_name": tool_result["tool_name"],
                            "args": dict(tool_result["args"]),
                            "result": tool_result["result"],
                            "tool_call_id": tool_call_id,
                            "execution": dict(tool_result.get("execution") or {}),
                        },
                        iteration=iteration,
                    ).to_dict()
                    self._append(append_event, produced_events, result_event)

            if step.state == AgentState.OBSERVING and self.reflector is not None:
                reflection_result = self._run_reflection(run_context)
                reflections = list(run_context.metadata.get("execution_reflections") or [])
                reflections.append(dict(reflection_result))
                run_context.metadata["execution_reflections"] = reflections
                reflection_event = event_factory.build(
                    AgentEventType.STATUS,
                    {
                        "status_kind": "execution_loop_reflected",
                        "summary": reflection_result.get("summary") or "Execution loop reflection completed",
                        "loop_step": step.name,
                        "reflection": dict(reflection_result),
                    },
                    iteration=iteration,
                ).to_dict()
                self._append(append_event, produced_events, reflection_event)
                if reflection_result["status"] == "revise" and run_context.iteration < self.max_iterations:
                    revision_event = event_factory.build(
                        AgentEventType.STATUS,
                        {
                            "status_kind": "execution_loop_revision_requested",
                            "summary": reflection_result.get("summary") or "Execution loop requested another iteration",
                            "loop_step": step.name,
                            "reflection": dict(reflection_result),
                            "next_iteration": run_context.iteration + 1,
                        },
                        iteration=iteration,
                    ).to_dict()
                    self._append(append_event, produced_events, revision_event)
                    step_index = self._find_step_index(AgentState.GENERATING)
                    continue

            step_index += 1

        run_context.metadata["execution_loop"] = {
            "controller": "minimal",
            "completed": run_context.state == AgentState.DONE,
            "steps": list(completed_steps),
        }
        return {
            "run": run_context.snapshot(),
            "events": produced_events,
        }

    @staticmethod
    def _append(
        append_event: Callable[[Dict[str, Any]], None],
        produced_events: list[Dict[str, Any]],
        event: Dict[str, Any],
    ) -> None:
        event_copy = dict(event)
        append_event(event_copy)
        produced_events.append(event_copy)

    def _run_review(self, run_context: AgentRunContext) -> Dict[str, Any]:
        raw_result = self.reviewer(run_context) if self.reviewer is not None else None
        if isinstance(raw_result, ExecutionReviewResult):
            return raw_result.to_dict()
        if isinstance(raw_result, dict):
            return ExecutionReviewResult(
                reviewer=str(raw_result.get("reviewer") or "default"),
                status=str(raw_result.get("status") or "approved"),
                summary=str(raw_result.get("summary") or ""),
                findings=tuple(str(item) for item in raw_result.get("findings") or []),
                metadata=dict(raw_result.get("metadata") or {}),
            ).to_dict()
        return ExecutionReviewResult().to_dict()

    def _run_reflection(self, run_context: AgentRunContext) -> Dict[str, Any]:
        raw_result = self.reflector(run_context) if self.reflector is not None else None
        if isinstance(raw_result, ExecutionReflectionResult):
            return raw_result.to_dict()
        if isinstance(raw_result, dict):
            return ExecutionReflectionResult(
                reflector=str(raw_result.get("reflector") or "default"),
                status=str(raw_result.get("status") or "accepted"),
                summary=str(raw_result.get("summary") or ""),
                observations=tuple(str(item) for item in raw_result.get("observations") or []),
                metadata=dict(raw_result.get("metadata") or {}),
            ).to_dict()
        return ExecutionReflectionResult().to_dict()

    def _run_tool_policy(self, run_context: AgentRunContext) -> Dict[str, Any] | None:
        raw_result = self.tool_policy(run_context) if self.tool_policy is not None else None
        if raw_result is None:
            return None
        if isinstance(raw_result, ExecutionToolDecision):
            return raw_result.to_dict()
        if isinstance(raw_result, dict):
            return ExecutionToolDecision(
                status=str(raw_result.get("status") or "allowed"),
                tool_name=str(raw_result.get("tool_name") or "unknown_tool"),
                tool_args=dict(raw_result.get("tool_args") or {}),
                reason=str(raw_result.get("reason") or ""),
                metadata=dict(raw_result.get("metadata") or {}),
            ).to_dict()
        return None

    def _run_tool_executor(self, run_context: AgentRunContext) -> Dict[str, Any] | None:
        raw_result = self.tool_executor(run_context) if self.tool_executor is not None else None
        if raw_result is None:
            return None
        if isinstance(raw_result, ExecutionToolResult):
            return raw_result.to_dict()
        if isinstance(raw_result, dict):
            return ExecutionToolResult(
                tool_name=str(raw_result.get("tool_name") or "unknown_tool"),
                args=dict(raw_result.get("args") or {}),
                result=str(raw_result.get("result") or ""),
                tool_call_id=str(raw_result.get("tool_call_id") or ""),
                execution=dict(raw_result.get("execution") or {}),
            ).to_dict()
        return None

    def _handle_exception(
        self,
        exc: Exception,
        *,
        run_context: AgentRunContext,
        event_factory: AgentEventFactory,
        append_event: Callable[[Dict[str, Any]], None],
        produced_events: list[Dict[str, Any]],
        iteration: int,
        loop_step: str,
    ) -> Dict[str, Any]:
        fallback_result = self._run_fallback(exc, run_context)
        run_context.metadata["execution_fallback"] = dict(fallback_result)
        if fallback_result["status"] == "handled":
            fallback_event = event_factory.build(
                AgentEventType.STATUS,
                {
                    "status_kind": "execution_loop_fallback_applied",
                    "summary": fallback_result.get("summary") or "Execution loop fallback handled an exception",
                    "loop_step": loop_step,
                    "error": str(exc),
                    "fallback": dict(fallback_result),
                },
                iteration=iteration,
            ).to_dict()
            self._append(append_event, produced_events, fallback_event)
            return fallback_result

        failed_transition = run_context.transition_to(AgentState.FAILED, stop_reason="loop_exception")
        failed_state_event = event_factory.build_state_event(
            previous_state=failed_transition["previous_state"],
            state=failed_transition["state"],
            stop_reason=failed_transition["stop_reason"],
            iteration=iteration,
        ).to_dict()
        self._append(append_event, produced_events, failed_state_event)
        failed_event = event_factory.build(
            AgentEventType.ERROR,
            {
                "status_kind": "execution_loop_failed",
                "summary": fallback_result.get("summary") or "Execution loop failed",
                "loop_step": loop_step,
                "error": str(exc),
                "fallback": dict(fallback_result),
            },
            iteration=iteration,
        ).to_dict()
        self._append(append_event, produced_events, failed_event)
        return fallback_result

    def _run_fallback(self, exc: Exception, run_context: AgentRunContext) -> Dict[str, Any]:
        raw_result = self.fallback_handler(exc, run_context) if self.fallback_handler is not None else None
        if isinstance(raw_result, ExecutionFallbackResult):
            return raw_result.to_dict()
        if isinstance(raw_result, dict):
            return ExecutionFallbackResult(
                strategy=str(raw_result.get("strategy") or "custom"),
                status=str(raw_result.get("status") or "failed"),
                summary=str(raw_result.get("summary") or ""),
                metadata=dict(raw_result.get("metadata") or {}),
            ).to_dict()
        return ExecutionFallbackResult(
            summary=f"Unhandled execution loop exception: {exc}",
            metadata={"error_type": exc.__class__.__name__},
        ).to_dict()

    def _find_step_index(self, state: AgentState) -> int:
        for index, step in enumerate(self.steps):
            if step.state == state:
                return index
        return 0


def _normalize_review_status(value: Any) -> str:
    normalized = str(value or "approved").strip().lower()
    if normalized in {"approved", "warning", "rejected"}:
        return normalized
    return "warning"


def _normalize_reflection_status(value: Any) -> str:
    normalized = str(value or "accepted").strip().lower()
    if normalized in {"accepted", "revise", "blocked"}:
        return normalized
    return "accepted"


def _normalize_fallback_status(value: Any) -> str:
    normalized = str(value or "failed").strip().lower()
    if normalized in {"handled", "failed"}:
        return normalized
    return "failed"


def _normalize_tool_decision_status(value: Any) -> str:
    normalized = str(value or "allowed").strip().lower()
    if normalized in {"allowed", "approval_required", "denied"}:
        return normalized
    return "denied"
