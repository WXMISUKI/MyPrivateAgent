"""
Agent Orchestrator - 多 Agent 编排

支持两种多 Agent 模式：
1. Handoff: agent A 转交到 agent B（串行）
2. Agent-as-Tool: agent A 调用 agent B 作为工具（嵌套）

对标：
- OpenAI Agents SDK 的 handoffs 和 agent.as_tool()
- Google ADK 的 sub_agents 自动委派
- LangGraph 的 subgraph
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from ..graph.engine import END, START, CompiledGraph, StateGraph
from ..graph.state import MessagesState
from ..graph.streaming import EventStream, StreamChunk
from ..tools.registry import ToolRegistry
from .agent import Agent

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """多 Agent 编排器。

    Usage:
        weather_agent = Agent(name="weather", instructions="...", tools=[...])
        booking_agent = Agent(name="booking", instructions="...", tools=[...])

        orchestrator = AgentOrchestrator(
            agents=[weather_agent, booking_agent],
            entry_agent=weather_agent,
        )
        result = orchestrator.run("What's the weather?")
    """

    def __init__(
        self,
        agents: list[Agent],
        entry_agent: Agent,
        *,
        model_call: Callable | None = None,
    ):
        self.agents = {a.name: a for a in agents}
        self.entry_agent = entry_agent
        self.model_call = model_call
        self._graph: CompiledGraph | None = None

    def build_graph(self) -> CompiledGraph:
        """构建多 Agent 执行图。"""
        graph = StateGraph(MessagesState)

        # 为每个 agent 创建节点
        for agent in self.agents.values():
            # agent 节点：调用模型
            agent_graph = agent.to_graph(model_call=self.model_call)
            # 作为子图节点
            from ..graph.nodes import SubGraphNode
            sub_node = SubGraphNode(name=agent.name, compiled_graph=agent_graph.compile())
            graph.add_node(agent.name, sub_node)

        # 入口：从 entry_agent 开始
        graph.add_edge(START, self.entry_agent.name)

        # 如果只有一个 agent，直接到 END
        if len(self.agents) == 1:
            graph.add_edge(self.entry_agent.name, END)
        else:
            # 多 agent：通过 handoff 路由
            def route_to_agent(state: dict) -> str:
                messages = state.get("messages", [])
                if not messages:
                    return END
                last = messages[-1]
                if isinstance(last, dict):
                    # 检查是否有 handoff 指令
                    content = last.get("content", "")
                    for agent_name in self.agents:
                        if f"@{agent_name}" in content or f"handoff:{agent_name}" in content:
                            return agent_name
                return END

            for agent_name in self.agents:
                graph.add_conditional_edges(
                    agent_name,
                    route_to_agent,
                    list(self.agents.keys()) + [END],
                )

        self._graph = graph.compile()
        return self._graph

    def run(self, user_input: str, config: dict | None = None) -> dict:
        """同步执行。"""
        if not self._graph:
            self.build_graph()
        return self._graph.invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config=config,
        )

    def stream(self, user_input: str, config: dict | None = None) -> EventStream:
        """流式执行。"""
        if not self._graph:
            self.build_graph()
        chunks = self._graph.stream(
            {"messages": [{"role": "user", "content": user_input}]},
            config=config,
        )
        return EventStream(iter(chunks))

    def get_agent(self, name: str) -> Agent | None:
        """获取指定名称的 agent。"""
        return self.agents.get(name)

    def list_agents(self) -> list[dict]:
        """列出所有 agent 的卡片信息。"""
        return [a.to_agent_card() for a in self.agents.values()]
