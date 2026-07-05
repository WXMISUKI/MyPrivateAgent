"""
Agent Bootstrap - 启动时注册示例 Agent

从 domain_agents/*/agent.yaml 读取定义，创建 Agent 实例并注册到运行时。
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# 示例工具函数
def get_weather(city: str) -> dict:
    """获取指定城市的天气信息。"""
    weather_data = {
        "北京": {"city": "北京", "temperature": "25°C", "condition": "晴", "humidity": "40%"},
        "上海": {"city": "上海", "temperature": "28°C", "condition": "多云", "humidity": "65%"},
        "广州": {"city": "广州", "temperature": "32°C", "condition": "雷阵雨", "humidity": "80%"},
        "深圳": {"city": "深圳", "temperature": "31°C", "condition": "阴", "humidity": "75%"},
    }
    data = weather_data.get(city)
    if data:
        return {"status": "success", "data": data}
    return {"status": "success", "data": {"city": city, "temperature": "20°C", "condition": "未知", "humidity": "50%"}}


def search_knowledge(query: str) -> dict:
    """搜索知识库。"""
    return {
        "status": "success",
        "results": [
            {"title": f"关于'{query}'的搜索结果", "content": f"这是关于{query}的知识库内容。", "score": 0.95},
        ],
    }


def execute_refund(order_id: str, amount: float) -> dict:
    """执行退款操作（高风险）。"""
    return {
        "status": "pending_approval",
        "order_id": order_id,
        "amount": amount,
        "message": f"退款请求已提交，订单 {order_id}，金额 {amount} 元，等待审批。",
    }


def register_example_agents():
    """注册示例 Agent。"""
    from ..runtime_plane.agents import Agent
    from ..runtime_plane.tools import tool, ToolRegistry
    from ..routers.agent_runtime import register_agent

    # 创建工具
    weather_tool = tool(get_weather)
    knowledge_tool = tool(search_knowledge)
    refund_tool = tool(execute_refund, risk_level="high", permission_level="ask")

    # Agent 1: 简单对话
    simple = Agent(
        name="simple_agent",
        instructions="你是一个友好的 AI 助手。请用中文回答用户的问题。",
        model="gpt-4o",
        description="一个纯对话 Agent，不使用工具。",
    )
    register_agent(simple)

    # Agent 2: 工具调用
    tool_agent = Agent(
        name="tool_agent",
        instructions="你是一个智能助手，可以使用工具回答问题。当用户问天气时使用 get_weather 工具，当需要搜索信息时使用 search_knowledge 工具。",
        model="gpt-4o",
        tools=[weather_tool, knowledge_tool],
        description="一个带工具调用的 Agent。",
    )
    register_agent(tool_agent)

    # Agent 3: 审批流程
    approval_agent = Agent(
        name="approval_agent",
        instructions="你是一个客服助手。可以查询天气和处理退款。执行退款前请确认订单信息。退款是高风险操作，会触发人工审批。",
        model="gpt-4o",
        tools=[weather_tool, refund_tool],
        description="一个带审批流程的 Agent。",
    )
    register_agent(approval_agent)

    logger.info(f"Registered {3} example agents: simple_agent, tool_agent, approval_agent")
    return {"simple_agent": simple, "tool_agent": tool_agent, "approval_agent": approval_agent}
