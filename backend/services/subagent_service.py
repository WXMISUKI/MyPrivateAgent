"""Subagent runtime helpers with a formal role registry and runtime contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

try:
    from services.subagent_registry_service import SubagentProfile, get_subagent_registry_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.subagent_registry_service import SubagentProfile, get_subagent_registry_service

ROLE_INSTRUCTIONS = {
    "frontend": "聚焦前端界面、交互、组件结构、样式与用户体验实现。",
    "backend": "聚焦后端接口、服务层、数据模型、持久化与稳定性实现。",
    "qa": "聚焦测试策略、回归验证、失败场景与质量风险识别。",
    "docs": "聚焦设计说明、实施记录、迁移说明与使用文档整理。",
    "planner": "聚焦目标拆解、执行顺序、风险分级与下一步编排。",
}


@dataclass(frozen=True)
class SubagentContext:
    """Normalized execution context for a specialized subagent run."""

    agent_role: str
    agent_id: str
    plan_id: Optional[int] = None
    plan_item_id: Optional[int] = None
    plan_item_title: str = ""
    handoff_status: str = ""
    required_capabilities: Tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: Optional[Dict[str, Any]]) -> Optional["SubagentContext"]:
        if not payload:
            return None

        role = str(payload.get("agent_role") or "").strip().lower()
        agent_id = str(payload.get("agent_id") or "").strip()
        if not role or role == "general" or not agent_id:
            return None

        return cls(
            agent_role=role,
            agent_id=agent_id,
            plan_id=payload.get("plan_id"),
            plan_item_id=payload.get("plan_item_id"),
            plan_item_title=str(payload.get("plan_item_title") or "").strip(),
            handoff_status=str(payload.get("handoff_status") or "").strip(),
            required_capabilities=tuple(
                str(value).strip()
                for value in (payload.get("required_capabilities") or [])
                if str(value).strip()
            ),
        )


class SubagentRuntimeService:
    """Build spawn/collect/merge runtime protocol for subagent execution."""

    def __init__(self) -> None:
        self.registry = get_subagent_registry_service()

    def normalize_context(self, payload: Optional[Dict[str, Any]]) -> Optional[SubagentContext]:
        return SubagentContext.from_dict(payload)

    def get_profile(self, role: str) -> Optional[SubagentProfile]:
        return self.registry.get_profile(role)

    def list_profiles(self) -> List[SubagentProfile]:
        return self.registry.list_profiles()

    def infer_roles_from_text(self, text: str) -> List[str]:
        return self.registry.infer_roles_from_text(text)

    def build_runtime_contract(self) -> Dict[str, Any]:
        return self.registry.build_runtime_contract()

    def build_role_system_prompt(self, context: SubagentContext) -> str:
        profile = self.get_profile(context.agent_role)
        role_instruction = ROLE_INSTRUCTIONS.get(
            context.agent_role,
            "聚焦当前分配职责，输出清晰的执行结果、风险和后续建议。",
        )
        profile_text = ""
        if profile is not None:
            profile_text = (
                f"该角色注册描述：{profile.description}。"
                f"可用工具范围：{', '.join(profile.allowed_tools) if profile.allowed_tools else '未限制'}。"
                f"上下文策略：{profile.context_policy}。"
            )
        title = context.plan_item_title or "当前计划项"
        capability_text = ""
        if context.required_capabilities:
            capability_text = f"该步骤依赖的 MCP capabilities: {', '.join(context.required_capabilities)}。"
        return (
            f"你正在以 `{context.agent_role}` 子智能体身份执行任务。"
            f"agent_id={context.agent_id}。"
            f"计划项：{title}。"
            f"{capability_text}"
            f"{profile_text}"
            f"{role_instruction}"
            "不要泛化成全栈答复，优先给出该角色负责范围内的可执行结果。"
        )

    def build_spawn_event(self, context: SubagentContext) -> Dict[str, Any]:
        return {
            "type": "status",
            "status_kind": "subagent_spawned",
            "agent_role": context.agent_role,
            "agent_id": context.agent_id,
            "plan_id": context.plan_id,
            "plan_item_id": context.plan_item_id,
            "plan_item_title": context.plan_item_title,
            "required_capabilities": list(context.required_capabilities),
            "content": f"已创建 {context.agent_role} 子智能体执行单元",
        }

    def build_collect_event(self, context: SubagentContext, *, output_text: str) -> Dict[str, Any]:
        excerpt = str(output_text or "").strip()
        if len(excerpt) > 120:
            excerpt = excerpt[:117].rstrip() + "..."
        return {
            "type": "status",
            "status_kind": "subagent_collected",
            "agent_role": context.agent_role,
            "agent_id": context.agent_id,
            "plan_id": context.plan_id,
            "plan_item_id": context.plan_item_id,
            "plan_item_title": context.plan_item_title,
            "required_capabilities": list(context.required_capabilities),
            "content": f"已收集 {context.agent_role} 子智能体结果",
            "subagent_output_excerpt": excerpt,
        }

    def build_merge_event(self, context: SubagentContext) -> Dict[str, Any]:
        return {
            "type": "status",
            "status_kind": "subagent_merged",
            "agent_role": context.agent_role,
            "agent_id": context.agent_id,
            "plan_id": context.plan_id,
            "plan_item_id": context.plan_item_id,
            "plan_item_title": context.plan_item_title,
            "required_capabilities": list(context.required_capabilities),
            "content": f"已合并 {context.agent_role} 子智能体结果到主响应",
        }


_subagent_runtime_service: Optional[SubagentRuntimeService] = None


def get_subagent_runtime_service() -> SubagentRuntimeService:
    global _subagent_runtime_service
    if _subagent_runtime_service is None:
        _subagent_runtime_service = SubagentRuntimeService()
    return _subagent_runtime_service
