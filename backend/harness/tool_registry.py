"""
工具注册表 - 参考 Claude Code 的工具管理方式
"""
import logging
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    """权限级别"""
    AUTO = "auto"      # 自动批准
    ASK = "ask"        # 需要用户确认
    DENY = "deny"     # 拒绝执行


class BaseTool:
    """
    基础工具类

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
    """

    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """注册工具"""
        self.tools[tool.name] = tool
        logger.info(f"[ToolRegistry] 注册工具: {tool.name}")

    def get(self, name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self.tools.get(name)

    def list_all(self) -> List[BaseTool]:
        """列出所有工具"""
        return list(self.tools.values())

    def get_schemas(self) -> List[Dict[str, Any]]:
        """获取所有工具的模式（用于绑定到模型）"""
        return [tool.get_schema() for tool in self.tools.values()]

    def clear(self) -> None:
        """清空所有工具"""
        self.tools.clear()


# 全局工具注册表实例
global_tool_registry = ToolRegistry()


def register_default_tools():
    """注册默认工具"""
    from .tools.search_tool import search_tool
    from .tools.datetime_tool import datetime_tool

    global_tool_registry.register(search_tool)
    global_tool_registry.register(datetime_tool)


def get_registry() -> ToolRegistry:
    """获取全局工具注册表"""
    return global_tool_registry
