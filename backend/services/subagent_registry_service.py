"""Subagent registry service with deterministic role profiles and governance metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class SubagentProfile:
    name: str
    description: str
    allowed_tools: Tuple[str, ...] = ()
    preferred_models: Tuple[str, ...] = ()
    context_policy: str = "isolated"
    trigger_conditions: Tuple[str, ...] = ()
    enabled: bool = True
    max_turns: int = 6


class SubagentRegistryService:
    """Centralized subagent registry for scheduler/runtime/hook governance."""

    def __init__(self) -> None:
        self._profiles: Dict[str, SubagentProfile] = {
            "frontend": SubagentProfile(
                name="frontend",
                description="聚焦前端界面、交互、组件结构、样式与用户体验实现。",
                allowed_tools=("search", "mcp_filesystem_read"),
                preferred_models=("doubao", "llama3.1"),
                context_policy="ui_focused",
                trigger_conditions=("frontend", "ui", "vue", "页面", "组件", "交互"),
            ),
            "backend": SubagentProfile(
                name="backend",
                description="聚焦后端接口、服务层、数据模型、持久化与稳定性实现。",
                allowed_tools=("search", "mcp_filesystem_read"),
                preferred_models=("doubao", "llama3.1"),
                context_policy="service_focused",
                trigger_conditions=("backend", "api", "服务", "接口", "数据库"),
            ),
            "qa": SubagentProfile(
                name="qa",
                description="聚焦测试策略、回归验证、失败场景与质量风险识别。",
                allowed_tools=("search", "mcp_filesystem_read"),
                preferred_models=("doubao",),
                context_policy="verification_focused",
                trigger_conditions=("qa", "测试", "回归", "验证", "smoke"),
            ),
            "docs": SubagentProfile(
                name="docs",
                description="聚焦设计说明、实施记录、迁移说明与使用文档整理。",
                allowed_tools=("search", "mcp_filesystem_read"),
                preferred_models=("doubao",),
                context_policy="documentation_focused",
                trigger_conditions=("docs", "文档", "readme", "说明", "日志"),
            ),
            "researcher": SubagentProfile(
                name="researcher",
                description="聚焦信息检索、事实整理、来源比对与证据摘要。",
                allowed_tools=("search", "get_current_datetime", "mcp_filesystem_read"),
                preferred_models=("doubao", "llama3.1"),
                context_policy="isolated_with_summary",
                trigger_conditions=("research", "compare", "fact_check", "benchmark"),
            ),
            "planner": SubagentProfile(
                name="planner",
                description="聚焦目标拆解、执行顺序、风险分级与计划追踪。",
                allowed_tools=("search", "get_current_datetime"),
                preferred_models=("doubao",),
                context_policy="plan_oriented",
                trigger_conditions=("planning", "todo", "decompose", "workflow"),
            ),
            "executor": SubagentProfile(
                name="executor",
                description="聚焦单步落地执行、结果交付与收尾检查。",
                allowed_tools=("search", "get_current_datetime", "mcp_filesystem_read"),
                preferred_models=("doubao", "llama3.1"),
                context_policy="task_focused",
                trigger_conditions=("execute", "implement", "deliver"),
            ),
        }

    def get_profile(self, role: str) -> Optional[SubagentProfile]:
        role_key = str(role or "").strip().lower()
        profile = self._profiles.get(role_key)
        if profile is None or not profile.enabled:
            return None
        return profile

    def list_profiles(self) -> List[SubagentProfile]:
        return [self._profiles[key] for key in sorted(self._profiles.keys()) if self._profiles[key].enabled]

    def infer_roles_from_text(self, text: str) -> List[str]:
        normalized = str(text or "").strip().lower()
        if not normalized:
            return []
        matched: List[str] = []
        for profile in self.list_profiles():
            if any(trigger.lower() in normalized for trigger in profile.trigger_conditions):
                matched.append(profile.name)
        return matched

    def build_runtime_contract(self) -> Dict[str, Any]:
        profiles = self.list_profiles()
        return {
            "total_profiles": len(profiles),
            "profiles": [
                {
                    "name": profile.name,
                    "description": profile.description,
                    "allowed_tools": list(profile.allowed_tools),
                    "preferred_models": list(profile.preferred_models),
                    "context_policy": profile.context_policy,
                    "trigger_conditions": list(profile.trigger_conditions),
                    "enabled": profile.enabled,
                    "max_turns": profile.max_turns,
                }
                for profile in profiles
            ],
        }


_subagent_registry_service: Optional[SubagentRegistryService] = None


def get_subagent_registry_service() -> SubagentRegistryService:
    global _subagent_registry_service
    if _subagent_registry_service is None:
        _subagent_registry_service = SubagentRegistryService()
    return _subagent_registry_service

