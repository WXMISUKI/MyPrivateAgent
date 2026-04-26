"""
工具注册表 - 参考 Claude Code 的工具管理方式
"""
import logging
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

try:
    from agent_framework.tools import ToolSpec
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.agent_framework.tools import ToolSpec

logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    """权限级别"""
    AUTO = "auto"      # 自动批准
    ASK = "ask"        # 需要用户确认
    DENY = "deny"     # 拒绝执行


class BaseTool:
    """
    基础工具类（兼容旧格式）

    所有工具都继承自这个基类，包含：
    - 名称和描述
    - 执行函数
    - 权限级别
    - 参数模式
    """

    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        permission_level: PermissionLevel = PermissionLevel.AUTO,
        parameters: Dict[str, Any] = None
    ):
        self.name = name
        self.description = description
        self.func = func
        self.permission_level = permission_level
        self.parameters = parameters or {}

    async def invoke(self, args: Dict[str, Any]) -> str:
        """执行工具"""
        try:
            result = await self.func(**args)
            return str(result)
        except Exception as e:
            logger.error(f"[BaseTool] {self.name} 执行失败: {e}")
            return f"执行错误: {str(e)}"

    def get_schema(self) -> Dict[str, Any]:
        """获取工具模式（用于绑定到模型）"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.parameters
            }
        }


class ToolRegistry:
    """
    工具注册表

    统一管理所有可用工具，提供：
    - 工具注册
    - 工具获取
    - 模式生成
    - bind_tools 支持
    """

    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self._langchain_tools: Dict[str, Any] = {}
        self._tool_definitions: List[Dict[str, Any]] = []
        self._tool_specs: Dict[str, ToolSpec] = {}

    def register(self, tool: BaseTool) -> None:
        """注册工具（兼容旧格式）"""
        self.tools[tool.name] = tool
        logger.info(f"[ToolRegistry] 注册工具（BaseTool）: {tool.name}")

    def register_langchain_tool(self, tool: Any) -> None:
        """注册 LangChain 工具"""
        self._langchain_tools[tool.name] = tool
        logger.info(f"[ToolRegistry] 注册 LangChain 工具: {tool.name}")

    def register_tool_spec(self, tool_spec: ToolSpec) -> None:
        """注册工具元数据规范。"""
        self._tool_specs[tool_spec.name] = tool_spec
        logger.info(f"[ToolRegistry] 注册工具元数据: {tool_spec.name}")

    def register_tool_definition(self, tool_def: Dict[str, Any]) -> None:
        """
        注册符合豆包格式的工具定义

        Args:
            tool_def: 符合豆包函数调用文档格式的工具定义
        """
        tool_name = tool_def.get('function', {}).get('name', 'unknown')
        self._tool_definitions = [
            item
            for item in self._tool_definitions
            if item.get("function", {}).get("name") != tool_name
        ]
        self._tool_definitions.append(tool_def)
        logger.info(f"[ToolRegistry] 注册工具定义: {tool_name}")

    def unregister(self, name: str) -> None:
        """取消注册工具及其相关元数据。"""
        self.tools.pop(name, None)
        self._langchain_tools.pop(name, None)
        self._tool_specs.pop(name, None)
        self._tool_definitions = [
            item
            for item in self._tool_definitions
            if item.get("function", {}).get("name") != name
        ]

    def get(self, name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self.tools.get(name)

    def get_langchain_tool(self, name: str) -> Optional[Any]:
        """获取 LangChain 工具"""
        return self._langchain_tools.get(name)

    def get_tool_spec(self, name: str) -> Optional[ToolSpec]:
        """获取工具元数据。"""
        return self._tool_specs.get(name)

    def list_all(self) -> List[BaseTool]:
        """列出所有工具"""
        return list(self.tools.values())

    def get_langchain_tools(self) -> List[Any]:
        """获取所有 LangChain 工具列表"""
        return list(self._langchain_tools.values())

    def list_tool_specs(self) -> List[ToolSpec]:
        """列出所有工具元数据。"""
        return list(self._tool_specs.values())

    def get_schemas(self) -> List[Dict[str, Any]]:
        """获取所有工具的模式（用于绑定到模型）"""
        schemas = []
        for tool in self.tools.values():
            schemas.append(tool.get_schema())
        for tool in self._langchain_tools.values():
            schemas.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.args_schema.schema() if hasattr(tool, 'args_schema') else {"type": "object", "properties": {}}
            })
        return schemas

    def get_doubao_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        获取符合豆包函数调用文档格式的工具定义

        参考：https://www.volcengine.com/docs/82379/1262342?lang=zh

        Returns:
            符合豆包格式的工具定义列表，包含 strict: True
        """
        return self._tool_definitions

    def clear(self) -> None:
        """清空所有工具"""
        self.tools.clear()
        self._langchain_tools.clear()
        self._tool_definitions.clear()
        self._tool_specs.clear()


global_tool_registry = ToolRegistry()


def register_default_tools():
    """注册默认工具（兼容旧格式）"""
    from .tools.search_tool import search_tool
    from .tools.datetime_tool import datetime_tool

    global_tool_registry.register(search_tool)
    global_tool_registry.register(datetime_tool)


def register_langchain_tools():
    """注册 LangChain 工具"""
    from .tools.langchain_tools import get_tools, TOOL_DEFINITIONS, TOOL_SPECS

    for tool in get_tools():
        global_tool_registry.register_langchain_tool(tool)

    for tool_def in TOOL_DEFINITIONS:
        global_tool_registry.register_tool_definition(tool_def)

    for tool_spec in TOOL_SPECS:
        global_tool_registry.register_tool_spec(tool_spec)


def get_registry() -> ToolRegistry:
    """获取全局工具注册表"""
    return global_tool_registry
