"""Policy engine for subagent/tool governance and multi-provider selection hints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

try:
    from services.subagent_registry_service import get_subagent_registry_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.subagent_registry_service import get_subagent_registry_service


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str = ""
    metadata: Optional[Dict[str, Any]] = None


class PolicyEngineService:
    """Provide deterministic policy checks for runtime governance."""

    def __init__(self) -> None:
        self.subagent_registry = get_subagent_registry_service()
        self.high_risk_tool_keywords: Tuple[str, ...] = (
            "filesystem_write",
            "delete",
            "remove",
            "payment",
            "booking",
        )
        self.default_provider_order: Tuple[str, ...] = (
            "volcengine-ark",
            "anthropic",
            "openai",
        )

    def evaluate_tool_use(
        self,
        *,
        tool_name: str,
        tool_args: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyDecision:
        normalized_tool = str(tool_name or "").strip().lower()
        subagent_role = str((context or {}).get("agent_role") or "").strip().lower()
        profile = self.subagent_registry.get_profile(subagent_role) if subagent_role else None

        if any(keyword in normalized_tool for keyword in self.high_risk_tool_keywords):
            return PolicyDecision(
                allowed=False,
                reason="命中高风险工具治理策略，当前框架默认阻断自动执行。",
                metadata={
                    "policy": "high_risk_tool_block",
                    "tool_name": tool_name,
                    "agent_role": subagent_role or None,
                },
            )

        if profile is not None and profile.allowed_tools:
            if normalized_tool not in set(profile.allowed_tools):
                return PolicyDecision(
                    allowed=False,
                    reason=f"子智能体 `{subagent_role}` 的工具白名单不允许调用 `{tool_name}`。",
                    metadata={
                        "policy": "subagent_tool_allowlist_block",
                        "tool_name": tool_name,
                        "agent_role": subagent_role,
                        "allowed_tools": list(profile.allowed_tools),
                    },
                )

        return PolicyDecision(
            allowed=True,
            reason="允许执行",
            metadata={
                "policy": "default_allow",
                "tool_name": tool_name,
                "agent_role": subagent_role or None,
            },
        )

    def select_provider_hint(
        self,
        *,
        requested_model: str,
        requested_provider: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        profile_provider_order = list(self.default_provider_order)
        subagent_role = str((context or {}).get("agent_role") or "").strip().lower()
        profile = self.subagent_registry.get_profile(subagent_role) if subagent_role else None

        if requested_provider:
            provider = str(requested_provider).strip().lower()
            return {
                "selected_provider": provider,
                "provider_order": [provider] + [item for item in profile_provider_order if item != provider],
                "reason": "request_provider_override",
                "model_name": requested_model,
                "agent_role": subagent_role or None,
            }

        if profile is not None and profile.preferred_models and requested_model not in profile.preferred_models:
            return {
                "selected_provider": profile_provider_order[0],
                "provider_order": profile_provider_order,
                "reason": "subagent_model_mismatch_fallback",
                "model_name": requested_model,
                "agent_role": subagent_role,
                "preferred_models": list(profile.preferred_models),
            }

        return {
            "selected_provider": profile_provider_order[0],
            "provider_order": profile_provider_order,
            "reason": "default_provider_order",
            "model_name": requested_model,
            "agent_role": subagent_role or None,
        }

    def select_model_for_provider(
        self,
        *,
        requested_model: str,
        selected_provider: str,
        available_models: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        provider = str(selected_provider or "").strip().lower()
        requested = str(requested_model or "").strip().lower()
        normalized = [item for item in (available_models or []) if isinstance(item, dict)]
        same_provider = [
            item for item in normalized
            if str(item.get("provider") or "").strip().lower() == provider
        ]
        if not same_provider:
            return {
                "resolved_model": requested_model,
                "resolved_provider": provider,
                "reason": "provider_not_found_keep_requested_model",
            }

        requested_candidate = next(
            (item for item in same_provider if str(item.get("name") or "").strip().lower() == requested),
            None,
        )
        if requested_candidate is not None:
            return {
                "resolved_model": requested_candidate.get("name"),
                "resolved_provider": provider,
                "reason": "requested_model_matches_provider",
            }

        default_candidate = next((item for item in same_provider if bool(item.get("is_default", False))), None)
        if default_candidate is None:
            default_candidate = next((item for item in same_provider if bool(item.get("available", False))), None)
        if default_candidate is None:
            default_candidate = same_provider[0]
        return {
            "resolved_model": default_candidate.get("name"),
            "resolved_provider": provider,
            "reason": "provider_fallback_model_selected",
            "requested_model": requested_model,
        }

    def build_runtime_contract(self) -> Dict[str, Any]:
        return {
            "engine": "policy_engine_v1",
            "high_risk_tool_keywords": list(self.high_risk_tool_keywords),
            "default_provider_order": list(self.default_provider_order),
            "subagent_registry_profiles": self.subagent_registry.build_runtime_contract().get("total_profiles", 0),
        }


_policy_engine_service: Optional[PolicyEngineService] = None


def get_policy_engine_service() -> PolicyEngineService:
    global _policy_engine_service
    if _policy_engine_service is None:
        _policy_engine_service = PolicyEngineService()
    return _policy_engine_service
