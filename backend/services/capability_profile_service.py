"""Agent identity and capability profile builders for the general agent demo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    from harness.tool_registry import ToolRegistry
    from harness.tool_registry import get_registry
    from services.mcp_registry_service import get_mcp_registry_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.harness.tool_registry import ToolRegistry
    from backend.harness.tool_registry import get_registry
    from backend.services.mcp_registry_service import get_mcp_registry_service


@dataclass
class CapabilityProfile:
    """Structured runtime capability contract."""

    system_prompt: str
    available_capabilities: List[str] = field(default_factory=list)
    limited_capabilities: List[str] = field(default_factory=list)
    enabled_mcp_capabilities: List[str] = field(default_factory=list)
    tool_summaries: List[Dict[str, Any]] = field(default_factory=list)
    skill_summaries: List[Dict[str, Any]] = field(default_factory=list)


class CapabilityProfileService:
    """Build a concise runtime identity/capability contract for the main agent."""

    IDENTITY_SUMMARY = (
        "MyPrivateAgent 主协调智能体。负责识别用户意图、决定是否需要计划、"
        "选择已注册能力、评估结果是否足够，并在能力不足时输出阶段性结论与补强建议。"
    )
    OPERATING_PRINCIPLES = [
        "仅把当前显式注册的工具、Skill、MCP capability 视为真实可用能力。",
        "复合任务中，工具结果默认视为中间观察，不直接等价于最终答复。",
        "当需求超出能力边界时，必须说明已完成部分、当前缺口与建议补强能力。",
        "优先输出保守、结构化、可执行的结果，禁止伪造未接入能力。",
    ]

    _COMMON_CAPABILITY_BOUNDARIES = (
        ("交通路线检索", ("transport", "route", "traffic", "navigation", "map", "travel_route")),
        ("网页浏览与开放网络检索", ("browser", "web", "crawl", "internet", "search_web")),
        ("景点 / POI 结构化检索", ("poi", "attraction", "travel_guide", "scenic", "location")),
        ("外部业务交易或预订执行", ("booking", "payment", "order", "trade", "reservation")),
        ("本地文件读写与代码执行", ("filesystem", "file", "code", "shell", "python", "workspace")),
    )

    def __init__(self):
        self.mcp_registry_service = get_mcp_registry_service()

    def build_profile(
        self,
        *,
        tool_registry: ToolRegistry,
        runtime_skills: Any = None,
        runtime_knowledge: Any = None,
        execution_context: Optional[Dict[str, Any]] = None,
    ) -> CapabilityProfile:
        tool_summaries = self._build_tool_summaries(tool_registry)
        enabled_mcp_capabilities = self._build_enabled_mcp_capabilities()
        skill_summaries = self._build_skill_summaries(runtime_skills)
        available_capabilities = self._build_available_capabilities(
            tool_summaries=tool_summaries,
            enabled_mcp_capabilities=enabled_mcp_capabilities,
            skill_summaries=skill_summaries,
        )
        limited_capabilities = self._build_limited_capabilities(
            tool_summaries=tool_summaries,
            enabled_mcp_capabilities=enabled_mcp_capabilities,
        )
        system_prompt = self._build_system_prompt(
            tool_summaries=tool_summaries,
            enabled_mcp_capabilities=enabled_mcp_capabilities,
            skill_summaries=skill_summaries,
            available_capabilities=available_capabilities,
            limited_capabilities=limited_capabilities,
            runtime_knowledge=runtime_knowledge,
            execution_context=execution_context or {},
        )
        return CapabilityProfile(
            system_prompt=system_prompt,
            available_capabilities=available_capabilities,
            limited_capabilities=limited_capabilities,
            enabled_mcp_capabilities=enabled_mcp_capabilities,
            tool_summaries=tool_summaries,
            skill_summaries=skill_summaries,
        )

    def build_runtime_contract(self) -> Dict[str, Any]:
        """构建不依赖具体会话上下文的运行时能力合同摘要。"""
        tool_registry = get_registry()
        tool_summaries = self._build_tool_summaries(tool_registry)
        enabled_mcp_capabilities = self._build_enabled_mcp_capabilities()
        available_capabilities = self._build_available_capabilities(
            tool_summaries=tool_summaries,
            enabled_mcp_capabilities=enabled_mcp_capabilities,
            skill_summaries=[],
        )
        limited_capabilities = self._build_limited_capabilities(
            tool_summaries=tool_summaries,
            enabled_mcp_capabilities=enabled_mcp_capabilities,
        )
        return {
            "identity_summary": self.IDENTITY_SUMMARY,
            "operating_principles": list(self.OPERATING_PRINCIPLES),
            "available_capabilities": available_capabilities,
            "limited_capabilities": limited_capabilities,
            "enabled_mcp_capabilities": enabled_mcp_capabilities,
            "registered_tools": tool_summaries,
        }

    def _build_tool_summaries(self, tool_registry: ToolRegistry) -> List[Dict[str, Any]]:
        specs = {spec.name: spec for spec in tool_registry.list_tool_specs()}
        tool_names = sorted({tool.name for tool in tool_registry.list_all()} | set(specs.keys()))
        summaries: List[Dict[str, Any]] = []
        for name in tool_names:
            spec = specs.get(name)
            tags = list(spec.tags) if spec is not None else []
            summaries.append(
                {
                    "name": name,
                    "description": spec.description if spec is not None else "",
                    "permission_level": getattr(spec, "permission_level", "auto") if spec is not None else "auto",
                    "tags": tags,
                    "kind": "mcp_runtime" if name.startswith("mcp_") else "tool",
                }
            )
        return summaries

    def _build_enabled_mcp_capabilities(self) -> List[str]:
        catalog = self.mcp_registry_service.build_capability_catalog()
        return [item["capability"] for item in catalog.get("capabilities", []) if item.get("capability")]

    def _build_skill_summaries(self, runtime_skills: Any) -> List[Dict[str, Any]]:
        selected_skills = list(getattr(runtime_skills, "selected_skills", []) or [])
        summaries = []
        for item in selected_skills:
            summaries.append(
                {
                    "name": getattr(item, "name", ""),
                    "domain": getattr(item, "domain", ""),
                    "agent_roles": list(getattr(item, "agent_roles", []) or []),
                    "required_capabilities": list(getattr(item, "required_capabilities", []) or []),
                }
            )
        return summaries

    def _build_available_capabilities(
        self,
        *,
        tool_summaries: List[Dict[str, Any]],
        enabled_mcp_capabilities: List[str],
        skill_summaries: List[Dict[str, Any]],
    ) -> List[str]:
        capabilities = [
            "用户意图识别与多步执行协调",
            "计划 / Todo 编排与执行摘要输出",
        ]

        if any(item["name"] == "search" for item in tool_summaries):
            capabilities.append("天气、日期时间与基础信息查询")
        if any(item["name"] == "get_current_datetime" for item in tool_summaries):
            capabilities.append("当前日期时间查询")
        if enabled_mcp_capabilities:
            capabilities.append(f"MCP 外部能力调用（{len(enabled_mcp_capabilities)} 项已启用）")
        if skill_summaries:
            capabilities.append(f"运行时 Skill 注入（{len(skill_summaries)} 项已命中）")

        return capabilities

    def _build_limited_capabilities(
        self,
        *,
        tool_summaries: List[Dict[str, Any]],
        enabled_mcp_capabilities: List[str],
    ) -> List[str]:
        combined_tokens = " ".join(
            [
                item["name"].lower()
                + " "
                + item.get("description", "").lower()
                + " "
                + " ".join(str(tag).lower() for tag in item.get("tags", []))
                for item in tool_summaries
            ]
            + [value.lower() for value in enabled_mcp_capabilities]
        )
        limited: List[str] = []
        for label, hints in self._COMMON_CAPABILITY_BOUNDARIES:
            if not any(hint in combined_tokens for hint in hints):
                limited.append(label)
        return limited

    def _build_system_prompt(
        self,
        *,
        tool_summaries: List[Dict[str, Any]],
        enabled_mcp_capabilities: List[str],
        skill_summaries: List[Dict[str, Any]],
        available_capabilities: List[str],
        limited_capabilities: List[str],
        runtime_knowledge: Any,
        execution_context: Dict[str, Any],
    ) -> str:
        tool_lines = []
        for item in tool_summaries[:12]:
            tag_text = f"；tags={','.join(item['tags'])}" if item.get("tags") else ""
            tool_lines.append(
                f"- {item['name']}：{item.get('description') or '无描述'}；权限={item.get('permission_level', 'auto')}{tag_text}"
            )
        if not tool_lines:
            tool_lines.append("- 当前未注册任何外部工具。")

        mcp_lines = [f"- {item}" for item in enabled_mcp_capabilities[:12]] or ["- 当前未启用 MCP capability。"]
        skill_lines = [f"- {item['name']}" for item in skill_summaries[:8]] or ["- 当前未命中运行时 Skill。"]
        available_lines = [f"- {item}" for item in available_capabilities]
        limited_lines = [f"- {item}" for item in limited_capabilities[:8]] or ["- 暂未检测到明显缺失的通用能力类别。"]

        knowledge_scope = getattr(runtime_knowledge, "metadata", {}).get("scope", "global") if runtime_knowledge is not None else "global"
        required_capabilities = execution_context.get("required_capabilities") or []
        required_line = ", ".join(required_capabilities) if required_capabilities else "无显式能力前置条件"

        return (
            f"你是 {self.IDENTITY_SUMMARY}\n\n"
            "请遵守以下规则：\n"
            f"1. {self.OPERATING_PRINCIPLES[0]}\n"
            f"2. {self.OPERATING_PRINCIPLES[2]}\n"
            f"3. {self.OPERATING_PRINCIPLES[1]}\n"
            "4. 不要假装拥有网页浏览、交通路线、POI/攻略、预订交易、文件写入等未显式接入能力。\n"
            f"5. {self.OPERATING_PRINCIPLES[3]}\n\n"
            f"当前内部执行上下文要求：{required_line}。\n"
            f"当前运行时知识作用域：{knowledge_scope}。\n\n"
            "当前可用能力：\n"
            f"{chr(10).join(available_lines)}\n\n"
            "当前注册工具：\n"
            f"{chr(10).join(tool_lines)}\n\n"
            "当前已启用 MCP capability：\n"
            f"{chr(10).join(mcp_lines)}\n\n"
            "当前命中 Skill：\n"
            f"{chr(10).join(skill_lines)}\n\n"
            "当前受限或未显式接入的常见能力：\n"
            f"{chr(10).join(limited_lines)}\n\n"
            "当任务无法完整完成时，优先输出三段：\n"
            "1. 已完成\n"
            "2. 当前缺口\n"
            "3. 建议补强能力\n"
        )


_capability_profile_service: Optional[CapabilityProfileService] = None


def get_capability_profile_service() -> CapabilityProfileService:
    global _capability_profile_service
    if _capability_profile_service is None:
        _capability_profile_service = CapabilityProfileService()
    return _capability_profile_service
