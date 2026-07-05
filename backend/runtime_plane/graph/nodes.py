"""
Graph Nodes - 节点类型定义

图引擎中的节点类型：
- LLMNode: 调用语言模型
- ToolNode: 执行工具调用
- HumanNode: 中断等待人工审批
- SubGraphNode: 嵌套子图
- CustomNode: 自定义函数节点
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Node function protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class NodeFunc(Protocol):
    """节点函数协议：接收 state，返回 state 增量。"""
    def __call__(self, state: dict[str, Any]) -> dict[str, Any]: ...


# ---------------------------------------------------------------------------
# Node types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class NodeDef:
    """节点定义：名称 + 可调用函数 + 元数据。"""
    name: str
    func: Callable
    node_type: str = "custom"      # llm / tool / human / subgraph / custom
    metadata: dict = field(default_factory=dict)


class LLMNode:
    """LLM 节点：调用语言模型，支持 tool binding。"""

    def __init__(self, name: str, model_call: Callable, *, tools: list | None = None):
        self.name = name
        self.model_call = model_call
        self.tools = tools or []

    def __call__(self, state: dict) -> dict:
        messages = state.get("messages", [])
        result = self.model_call(messages, tools=self.tools)
        return {"messages": [result]}


class ToolNode:
    """工具节点：执行消息中的 tool_calls。"""

    def __init__(self, name: str, tool_registry):
        self.name = name
        self.tool_registry = tool_registry

    def __call__(self, state: dict) -> dict:
        messages = state.get("messages", [])
        if not messages:
            return {"messages": []}

        last_msg = messages[-1]
        tool_calls = last_msg.get("tool_calls", [])
        if not tool_calls:
            return {"messages": []}

        results = []
        for tc in tool_calls:
            tool_name = tc.get("name", "")
            tool_args = tc.get("args", {})
            tool_call_id = tc.get("id", "")

            spec, handler = self.tool_registry.get(tool_name)
            if handler is None:
                result = {"error": f"Tool '{tool_name}' not found"}
            else:
                try:
                    result = handler(**tool_args)
                except Exception as e:
                    logger.error(f"Tool '{tool_name}' execution error: {e}")
                    result = {"error": str(e)}

            results.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": str(result),
                "name": tool_name,
            })

        return {"messages": results}


class HumanNode:
    """人工节点：中断执行，等待人工输入。"""

    def __init__(self, name: str, prompt: str = "Waiting for human input"):
        self.name = name
        self.prompt = prompt

    def __call__(self, state: dict) -> dict:
        from .interrupt import interrupt as do_interrupt
        response = do_interrupt(self.prompt)
        return {"messages": [{"role": "human", "content": str(response)}]}


class SubGraphNode:
    """子图节点：嵌套执行另一个编译后的图。"""

    def __init__(self, name: str, compiled_graph, *, input_key: str = "messages"):
        self.name = name
        self.compiled_graph = compiled_graph
        self.input_key = input_key

    def __call__(self, state: dict) -> dict:
        sub_input = {self.input_key: state.get(self.input_key, [])}
        sub_result = self.compiled_graph.invoke(sub_input)
        return sub_result
