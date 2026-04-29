"""Minimal hooks/permission governance service for tool and fallback lifecycle."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class HookDecision:
    allowed: bool
    reason: str = ""
    metadata: Optional[Dict[str, Any]] = None


class AgentHookService:
    """Provide lightweight governance hooks similar to mature agent frameworks."""

    def __init__(self):
        self.enabled_hooks = ("pre_tool_use", "post_tool_use", "on_fallback")
        self.high_risk_tool_keywords = ("filesystem_write", "delete", "remove", "payment", "booking")

    def pre_tool_use(self, *, tool_name: str, tool_args: Dict[str, Any], context: Dict[str, Any]) -> HookDecision:
        normalized_name = str(tool_name or "").strip().lower()
        if any(keyword in normalized_name for keyword in self.high_risk_tool_keywords):
            return HookDecision(
                allowed=False,
                reason="命中高风险工具治理策略，当前框架默认阻断自动执行。",
                metadata={"policy": "high_risk_tool_block", "tool_name": tool_name},
            )

        return HookDecision(
            allowed=True,
            reason="允许执行",
            metadata={"policy": "default_allow", "tool_name": tool_name},
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
            "high_risk_tool_keywords": list(self.high_risk_tool_keywords),
            "governance_model": "minimal_default_allow_with_high_risk_block",
        }


_agent_hook_service: Optional[AgentHookService] = None


def get_agent_hook_service() -> AgentHookService:
    global _agent_hook_service
    if _agent_hook_service is None:
        _agent_hook_service = AgentHookService()
    return _agent_hook_service

