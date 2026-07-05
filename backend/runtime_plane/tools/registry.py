"""
Tool Registry - 工具注册与管理

提供 @tool 装饰器自动从函数签名生成 ToolSpec，
以及 ToolRegistry 统一管理工具注册、查找、绑定。
与现有 ToolRuntimeService 桥接，不重复实现。
"""

from __future__ import annotations

import inspect
import logging
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# @tool decorator - 自动从函数生成工具定义
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ToolDef:
    """工具定义：名称、描述、参数 schema、处理函数。"""
    name: str
    description: str
    parameters: dict[str, Any]   # JSON Schema 格式
    handler: Callable
    permission_level: str = "auto"
    risk_level: str = "low"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "permission_level": self.permission_level,
            "risk_level": self.risk_level,
        }


def _python_type_to_json_schema(tp: type) -> dict:
    """Python 类型转 JSON Schema。"""
    mapping = {
        str: {"type": "string"},
        int: {"type": "integer"},
        float: {"type": "number"},
        bool: {"type": "boolean"},
        list: {"type": "array"},
        dict: {"type": "object"},
    }
    return mapping.get(tp, {"type": "string"})


def _build_parameters_schema(func: Callable) -> dict:
    """从函数签名构建 JSON Schema 参数定义。"""
    sig = inspect.signature(func)
    properties = {}
    required = []

    for name, param in sig.parameters.items():
        if name in ("self", "cls", "state", "context", "tool_context"):
            continue

        annotation = param.annotation
        prop = _python_type_to_json_schema(annotation if annotation != inspect.Parameter.empty else str)

        # 从 docstring 提取参数描述
        doc = func.__doc__ or ""
        # 简单提取 Args: 段落中的描述
        for line in doc.split("\n"):
            line = line.strip()
            if line.startswith(f"{name} (") or line.startswith(f"{name}:"):
                desc = line.split(")", 1)[-1].strip().lstrip(":").strip()
                if desc:
                    prop["description"] = desc
                break

        properties[name] = prop

        if param.default == inspect.Parameter.empty:
            required.append(name)

    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


def tool(
    func: Callable | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    permission_level: str = "auto",
    risk_level: str = "low",
) -> Callable | ToolDef:
    """装饰器：将函数转换为工具定义。

    Usage:
        @tool
        def get_weather(city: str) -> str:
            '''获取天气信息。'''
            return f"{city} is sunny"

        @tool(name="custom_name", risk_level="high")
        def risky_operation(data: str) -> dict:
            '''高风险操作。'''
            return {"result": "done"}
    """
    def decorator(fn: Callable) -> ToolDef:
        tool_name = name or fn.__name__
        tool_desc = description or (fn.__doc__ or "").strip().split("\n")[0]
        parameters = _build_parameters_schema(fn)

        return ToolDef(
            name=tool_name,
            description=tool_desc,
            parameters=parameters,
            handler=fn,
            permission_level=permission_level,
            risk_level=risk_level,
        )

    if func is not None:
        return decorator(func)
    return decorator


# ---------------------------------------------------------------------------
# ToolRegistry - 工具注册表
# ---------------------------------------------------------------------------

class ToolRegistry:
    """工具注册表：管理工具定义和处理函数。"""

    def __init__(self):
        self._tools: dict[str, ToolDef] = {}

    def register(self, tool_def: ToolDef | Callable, handler: Callable | None = None) -> None:
        """注册工具。支持 ToolDef 或 @tool 装饰器返回值。"""
        if isinstance(tool_def, ToolDef):
            self._tools[tool_def.name] = tool_def
        elif callable(tool_def) and handler:
            # 从函数和 handler 创建
            td = tool(tool_def)
            if isinstance(td, ToolDef):
                self._tools[td.name] = ToolDef(
                    name=td.name,
                    description=td.description,
                    parameters=td.parameters,
                    handler=handler,
                    permission_level=td.permission_level,
                    risk_level=td.risk_level,
                )
        else:
            raise ValueError(f"Invalid tool registration: {tool_def}")

    def register_function(self, func: Callable, **kwargs) -> ToolDef:
        """注册普通函数为工具。"""
        td = tool(func, **kwargs)
        if isinstance(td, ToolDef):
            self._tools[td.name] = td
            return td
        raise ValueError(f"Failed to register function as tool: {func}")

    def get(self, name: str) -> tuple[ToolDef | None, Callable | None]:
        """获取工具定义和处理函数。"""
        td = self._tools.get(name)
        if td:
            return td, td.handler
        return None, None

    def list_tools(self) -> list[ToolDef]:
        """列出所有注册的工具。"""
        return list(self._tools.values())

    def list_tool_names(self) -> list[str]:
        """列出所有工具名。"""
        return list(self._tools.keys())

    def has(self, name: str) -> bool:
        """检查工具是否已注册。"""
        return name in self._tools

    def remove(self, name: str) -> None:
        """移除工具。"""
        self._tools.pop(name, None)

    def get_tools_for_model(self, tool_names: list[str] | None = None) -> list[dict]:
        """获取工具列表，格式适合传给模型的 tool_choice。"""
        tools = self._tools.values()
        if tool_names:
            tools = [t for t in tools if t.name in tool_names]
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]

    def to_langchain_tools(self, tool_names: list[str] | None = None) -> list:
        """转换为 LangChain Tool 对象列表（需要 langchain-core）。"""
        try:
            from langchain_core.tools import StructuredTool
            tools = self._tools.values()
            if tool_names:
                tools = [t for t in tools if t.name in tool_names]
            result = []
            for t in tools:
                try:
                    st = StructuredTool.from_function(
                        func=t.handler,
                        name=t.name,
                        description=t.description,
                        args_schema=t.parameters,
                    )
                    result.append(st)
                except Exception as e:
                    logger.warning(f"Failed to convert tool '{t.name}' to LangChain: {e}")
            return result
        except ImportError:
            logger.warning("langchain-core not installed, cannot convert to LangChain tools")
            return []
