"""Tool policy adapters for harness execution loops."""

from __future__ import annotations

from typing import Any, Callable, Dict

from .execution_loop import ExecutionToolDecision
from .runtime import AgentRunContext

try:
    from services.policy_engine_service import PolicyEngineService, get_policy_engine_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.policy_engine_service import PolicyEngineService, get_policy_engine_service


def build_policy_engine_tool_policy(
    *,
    tool_name: str,
    tool_args: Dict[str, Any] | None = None,
    context: Dict[str, Any] | None = None,
    policy_engine: PolicyEngineService | None = None,
) -> Callable[[AgentRunContext], ExecutionToolDecision]:
    """Build an ExecutionLoop-compatible tool policy from PolicyEngineService."""

    normalized_tool_name = str(tool_name or "").strip() or "unknown_tool"
    normalized_tool_args = dict(tool_args or {})
    static_context = dict(context or {})
    engine = policy_engine or get_policy_engine_service()

    def evaluate(run_context: AgentRunContext) -> ExecutionToolDecision:
        runtime_context = {
            "user_id": run_context.user_id,
            "conversation_id": run_context.conversation_id,
            "run_id": run_context.run_id,
            "parent_run_id": run_context.parent_run_id,
            "run_kind": run_context.run_kind.value,
            **dict(run_context.metadata or {}),
            **static_context,
        }
        decision = engine.evaluate_tool_use(
            tool_name=normalized_tool_name,
            tool_args=normalized_tool_args,
            context=runtime_context,
        )
        status = "allowed"
        if decision.requires_approval:
            status = "approval_required"
        elif not decision.allowed:
            status = "denied"

        decision_metadata = dict(decision.metadata or {})
        if decision.reason_code:
            decision_metadata["reason_code"] = decision.reason_code
        return ExecutionToolDecision(
            status=status,
            tool_name=normalized_tool_name,
            tool_args=dict(normalized_tool_args),
            reason=decision.reason,
            metadata=decision_metadata,
        )

    return evaluate
