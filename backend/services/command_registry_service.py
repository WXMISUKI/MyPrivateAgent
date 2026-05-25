"""Framework command registry for slash-command style operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

try:
    from agent_framework.harness import build_agent_harness_facade_contract
    from agent_framework.runtime_dependencies import get_default_embedded_runtime_factory
    from agent_framework.sdk import build_embedded_sdk_contract
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.agent_framework.harness import build_agent_harness_facade_contract
    from backend.agent_framework.runtime_dependencies import get_default_embedded_runtime_factory
    from backend.agent_framework.sdk import build_embedded_sdk_contract


@dataclass(frozen=True)
class FrameworkCommand:
    id: str
    name: str
    description: str
    icon: str
    action: str
    category: str
    has_param: bool = False
    param_hint: str = ""
    param_examples: List[str] | None = None
    parameters_schema: Dict[str, Any] = field(default_factory=dict)
    required_capabilities: List[str] = field(default_factory=list)
    permission_level: str = "read"
    execution_handler: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "action": self.action,
            "category": self.category,
            "has_param": self.has_param,
            "param_hint": self.param_hint,
            "param_examples": list(self.param_examples or []),
            "command_id": self.id,
            "parameters_schema": dict(self.parameters_schema or {}),
            "required_capabilities": list(self.required_capabilities or []),
            "permission_level": self.permission_level,
            "execution_handler": self.execution_handler or f"command_handlers.{self.action}",
        }

    def to_definition(self) -> Dict[str, Any]:
        return {
            "command_id": self.id,
            "name": self.name,
            "description": self.description,
            "parameters_schema": dict(self.parameters_schema or {}),
            "required_capabilities": list(self.required_capabilities or []),
            "permission_level": self.permission_level,
            "execution_handler": self.execution_handler or f"command_handlers.{self.action}",
            "category": self.category,
            "action": self.action,
        }


class CommandRegistryService:
    def __init__(self):
        self._commands: List[FrameworkCommand] = [
            FrameworkCommand("new", "new", "开始一个新对话", "➕", "new_conversation", "conversation"),
            FrameworkCommand("clear", "clear", "清空当前对话", "🗑️", "clear_conversation", "conversation"),
            FrameworkCommand("export", "export", "导出当前对话", "📤", "export_conversation", "conversation"),
            FrameworkCommand("skills", "skills", "打开 Skills 管理页面", "🧠", "open_skills", "governance"),
            FrameworkCommand("learnings", "learnings", "打开学习记录页面", "📚", "open_learnings", "governance"),
            FrameworkCommand("feedback", "feedback", "打开反馈分析页面", "📊", "open_feedback_analytics", "governance"),
            FrameworkCommand("settings", "settings", "打开设置页面", "⚙️", "open_settings", "governance"),
            FrameworkCommand(
                "search",
                "search",
                "搜索会话历史",
                "🔍",
                "open_search",
                "conversation",
                True,
                "/search <query>",
                ["error analysis", "舟山 路由"],
            ),
            FrameworkCommand("help", "help", "显示帮助信息", "❓", "show_help", "system"),
            FrameworkCommand(
                "doctor",
                "doctor",
                "运行框架健康检查或治理门禁",
                "🩺",
                "run_doctor",
                "framework",
                True,
                "/doctor <startup|governance> [warning]",
                ["startup", "governance", "governance warning"],
                {
                    "type": "object",
                    "properties": {
                        "mode": {"type": "string", "enum": ["startup", "governance"]},
                        "severity": {"type": "string", "enum": ["all", "warning"]},
                    },
                    "required": ["mode"],
                    "additionalProperties": False,
                },
                ["governance.runtime_read"],
                "read",
                "command_handlers.run_doctor",
            ),
            FrameworkCommand(
                "snapshot",
                "snapshot",
                "按快照 ID 打开治理时间线定位视图",
                "🧷",
                "open_snapshot",
                "framework",
                True,
                "/snapshot <snapshot_id>",
                ["MCP-REF-1", "DOC-REF-1"],
            ),
            FrameworkCommand("plan", "plan", "打开计划与调度面板", "🗂️", "open_planner", "framework"),
            FrameworkCommand(
                "gaps",
                "gaps",
                "查看能力缺口治理面板",
                "🧭",
                "open_gaps",
                "framework",
                True,
                "/gaps <all|warning|snapshot <id>>",
                ["all", "warning", "snapshot GOV-REF-1"],
            ),
            FrameworkCommand(
                "permissions",
                "permissions",
                "查看权限治理面板",
                "🔐",
                "open_permissions",
                "framework",
                True,
                "/permissions <all|warning|snapshot <id>>",
                ["all", "warning", "snapshot PERM-REF-1"],
            ),
            FrameworkCommand(
                "mcp",
                "mcp",
                "查看 MCP 注册与连接状态",
                "🔌",
                "open_mcp",
                "framework",
                True,
                "/mcp <all|warning|snapshot <id>>",
                ["all", "warning", "snapshot MCP-REF-1"],
            ),
            FrameworkCommand("memory", "memory", "查看分层记忆与指令面", "🧩", "open_memory", "framework"),
            FrameworkCommand(
                "model",
                "model",
                "切换当前模型或打开模型设置",
                "🧠",
                "open_model",
                "framework",
                True,
                "/model <name>",
                ["doubao", "deepseek-chat"],
            ),
        ]

    def list_commands(self) -> List[Dict[str, Any]]:
        return [command.to_dict() for command in self._commands]

    def build_runtime_contract(self) -> Dict[str, Any]:
        commands = self.list_commands()
        command_definitions = [command.to_definition() for command in self._commands]
        return {
            "contract_version": "phase-b-command-runtime-v1",
            "total_commands": len(commands),
            "command_definitions": command_definitions,
            "embedded_sdk": build_embedded_sdk_contract(),
            "agent_harness_facade": build_agent_harness_facade_contract(),
            "embedded_runtime_factory": get_default_embedded_runtime_factory().build_runtime_contract(),
            "framework_commands": [item for item in commands if item["category"] == "framework"],
            "conversation_commands": [item for item in commands if item["category"] == "conversation"],
            "governance_commands": [item for item in commands if item["category"] == "governance"],
            "system_commands": [item for item in commands if item["category"] == "system"],
        }


_command_registry_service: CommandRegistryService | None = None


def get_command_registry_service() -> CommandRegistryService:
    global _command_registry_service
    if _command_registry_service is None:
        _command_registry_service = CommandRegistryService()
    return _command_registry_service
