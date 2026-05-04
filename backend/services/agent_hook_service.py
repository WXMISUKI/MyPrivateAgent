"""Minimal hooks/permission governance service for tool and fallback lifecycle."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    from services.policy_engine_service import get_policy_engine_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.policy_engine_service import get_policy_engine_service

@dataclass
class HookDecision:
    allowed: bool
    reason: str = ""
    metadata: Optional[Dict[str, Any]] = None


class AgentHookService:
    """Provide lightweight governance hooks similar to mature agent frameworks."""

    def __init__(self):
        self.enabled_hooks = ("pre_tool_use", "post_tool_use", "on_fallback")
        self.policy_engine = get_policy_engine_service()

    def pre_tool_use(self, *, tool_name: str, tool_args: Dict[str, Any], context: Dict[str, Any]) -> HookDecision:
        decision = self.policy_engine.evaluate_tool_use(
            tool_name=tool_name,
            tool_args=tool_args,
            context=context,
        )
        return HookDecision(
            allowed=decision.allowed,
            reason=decision.reason,
            metadata=decision.metadata or {"policy": "default_allow", "tool_name": tool_name},
        )

    def post_tool_use(self, *, tool_name: str, tool_result: str, context: Dict[str, Any]) -> Dict[str, Any]:
        result_text = str(tool_result or "")
        return {
            "tool_name": tool_name,
            "result_length": len(result_text),
            "policy": "post_observation_recorded",
        }

    def on_fallback(self, *, reason: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "reason": reason,
            "policy": "fallback_governance_recorded",
            "conversation_id": context.get("conversation_id"),
        }

    def build_runtime_contract(self) -> Dict[str, Any]:
        return {
            "enabled_hooks": list(self.enabled_hooks),
            "high_risk_tool_keywords": list(self.policy_engine.high_risk_tool_keywords),
            "governance_model": "minimal_default_allow_with_high_risk_block",
            "policy_engine": self.policy_engine.build_runtime_contract(),
        }


_agent_hook_service: Optional[AgentHookService] = None


def get_agent_hook_service() -> AgentHookService:
    global _agent_hook_service
    if _agent_hook_service is None:
        _agent_hook_service = AgentHookService()
    return _agent_hook_service
