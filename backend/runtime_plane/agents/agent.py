"""
Agent Definition - 智能体定义

对标 OpenAI Agents SDK 的 Agent 和 Google ADK 的 Agent。
每个 Agent 包含：name, instructions, model, tools, handoffs, guardrails。
Agent 可以转换为 StateGraph 执行，也可以作为工具被其他 Agent 调用。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from ..graph.engine import END, START, StateGraph
from ..graph.nodes import LLMNode, ToolNode
from ..graph.state import MessagesState
from ..tools.registry import ToolDef, ToolRegistry

logger = logging.getLogger(__name__)


@dataclass
class Agent:
    """智能体定义。

    Usage:
        agent = Agent(
            name="weather_agent",
            instructions="你是一个天气助手。",
            model="gpt-4o",
            tools=[get_weather_tool],
        )
        graph = agent.to_graph()
        result = graph.invoke({"messages": [("user", "北京天气怎么样？")]})
    """
    name: str
    instructions: str = ""
    model: str = "gpt-4o"
    tools: list[ToolDef] = field(default_factory=list)
    handoffs: list["Agent"] = field(default_factory=list)
    guardrails: list[Callable] = field(default_factory=list)
    output_type: type | None = None
    description: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        # 确保 tools 是 ToolDef 列表
        validated_tools = []
        for t in self.tools:
            if isinstance(t, ToolDef):
                validated_tools.append(t)
            elif callable(t):
                # 尝试用 @tool 装饰器包装
                from ..tools.registry import tool
                td = tool(t)
                if isinstance(td, ToolDef):
                    validated_tools.append(td)
        self.tools = validated_tools

    def as_tool(self, tool_name: str | None = None, description: str | None = None) -> ToolDef:
        """将此 Agent 作为工具供其他 Agent 调用。"""
        name = tool_name or f"call_{self.name}"
        desc = description or self.description or f"Call {self.name} agent"

        def handler(**kwargs) -> str:
            # 简化实现：同步调用
            user_input = kwargs.get("input", kwargs.get("query", str(kwargs)))
            graph = self.to_graph()
            result = graph.invoke({"messages": [{"role": "user", "content": user_input}]})
            messages = result.get("messages", [])
            if messages:
                last = messages[-1]
                if isinstance(last, dict):
                    return last.get("content", str(last))
                return str(last)
            return "No response"

        return ToolDef(
            name=name,
            description=desc,
            parameters={
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "The input for the agent"},
                },
                "required": ["input"],
            },
            handler=handler,
        )

    def to_graph(self, *, model_call: Callable | None = None) -> StateGraph:
        """将 Agent 转换为可执行的状态图。

        Args:
            model_call: 模型调用函数 (messages, tools) -> response dict。
                       如果不提供，使用默认的 OpenAI 调用。
        """
        graph = StateGraph(MessagesState)

        # 构建工具注册表
        registry = ToolRegistry()
        for t in self.tools:
            registry.register(t)

        # 添加 handoff 工具
        for ha in self.handoffs:
            handoff_tool = ha.as_tool()
            registry.register(handoff_tool)

        # 创建模型调用节点
        effective_model_call = model_call or self._default_model_call
        llm_node = LLMNode(
            name=f"{self.name}_llm",
            model_call=effective_model_call,
            tools=self.tools,
        )

        # 创建工具执行节点
        tool_node = ToolNode(
            name=f"{self.name}_tools",
            tool_registry=registry,
        )

        # 添加节点
        graph.add_node("agent", llm_node)
        graph.add_node("tools", tool_node)

        # 定义路由函数
        def should_continue(state: dict) -> str:
            messages = state.get("messages", [])
            if not messages:
                return END
            last = messages[-1]
            if isinstance(last, dict) and last.get("tool_calls"):
                return "tools"
            return END

        # 添加边
        graph.add_edge(START, "agent")
        graph.add_conditional_edges("agent", should_continue, ["tools", END])
        graph.add_edge("tools", "agent")

        return graph

    def _default_model_call(self, messages: list, tools: list = None) -> dict:
        """默认模型调用（需要配置 API key）。"""
        try:
            from langchain_openai import ChatOpenAI
            model = ChatOpenAI(model=self.model, temperature=0)

            # 转换消息格式
            lc_messages = []
            for m in messages:
                if isinstance(m, dict):
                    role = m.get("role", "user")
                    content = m.get("content", "")
                    if role == "system":
                        from langchain_core.messages import SystemMessage
                        lc_messages.append(SystemMessage(content=content))
                    elif role == "assistant":
                        from langchain_core.messages import AIMessage
                        lc_messages.append(AIMessage(content=content))
                    elif role == "tool":
                        from langchain_core.messages import ToolMessage
                        lc_messages.append(ToolMessage(
                            content=content,
                            tool_call_id=m.get("tool_call_id", ""),
                        ))
                    else:
                        from langchain_core.messages import HumanMessage
                        lc_messages.append(HumanMessage(content=content))
                else:
                    lc_messages.append(m)

            # 注入系统提示词
            if self.instructions and (not lc_messages or lc_messages[0].type != "system"):
                from langchain_core.messages import SystemMessage
                lc_messages.insert(0, SystemMessage(content=self.instructions))

            # 绑定工具
            if tools:
                lc_tools = []
                for t in tools:
                    if isinstance(t, ToolDef):
                        lc_tools.append({
                            "type": "function",
                            "function": {
                                "name": t.name,
                                "description": t.description,
                                "parameters": t.parameters,
                            },
                        })
                if lc_tools:
                    model = model.bind_tools(lc_tools)

            response = model.invoke(lc_messages)

            # 转换为标准格式
            result = {
                "role": "assistant",
                "content": response.content,
            }
            if hasattr(response, "tool_calls") and response.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tc.get("id", ""),
                        "name": tc.get("name", ""),
                        "args": tc.get("args", {}),
                    }
                    for tc in response.tool_calls
                ]
            return result

        except ImportError:
            logger.warning("langchain-openai not installed, using mock model call")
            return {
                "role": "assistant",
                "content": f"[Mock {self.name}] I received {len(messages)} messages but no model is configured.",
            }
        except Exception as e:
            logger.error(f"Model call error: {e}")
            return {
                "role": "assistant",
                "content": f"Error: {e}",
            }


    def to_agent_card(self) -> dict:
        """导出为 AgentCard（用于注册和发现）。"""
        return {
            "agent_id": self.name,
            "name": self.name,
            "description": self.description or self.instructions[:100],
            "model": self.model,
            "tools": [t.name for t in self.tools],
            "handoffs": [ha.name for ha in self.handoffs],
            "capabilities": self._infer_capabilities(),
            "metadata": self.metadata,
        }

    def _infer_capabilities(self) -> list[str]:
        """推断 agent 能力。"""
        caps = ["chat"]
        if self.tools:
            caps.append("tool_call")
        if self.handoffs:
            caps.append("multi_agent")
        if any(t.risk_level == "high" for t in self.tools):
            caps.append("approval")
        return caps
