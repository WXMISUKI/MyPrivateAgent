"""
Agent Runtime API - 运行层 API 端点

提供智能体运行时的 REST API：
- POST /api/agent-runtime/run              同步执行
- POST /api/agent-runtime/stream           流式执行（SSE）
- POST /api/agent-runtime/resume           恢复中断的执行
- GET  /api/agent-runtime/agents           列出所有注册的 agent
- GET  /api/agent-runtime/agents/{id}      获取 agent 详情
- POST /api/agent-runtime/agents/{id}/run  指定 agent 执行
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-runtime", tags=["agent-runtime"])


# ---------------------------------------------------------------------------
# Request/Response schemas
# ---------------------------------------------------------------------------

class RunRequest(BaseModel):
    agent_id: str = Field(..., description="Agent ID")
    messages: list[dict] = Field(default_factory=list, description="Message history")
    user_input: str = Field("", description="User input (shorthand)")
    thread_id: str | None = Field(None, description="Thread ID for checkpointing")
    config: dict = Field(default_factory=dict, description="Additional config")


class RunResponse(BaseModel):
    run_id: str
    agent_id: str
    status: str
    messages: list[dict]
    thread_id: str
    metadata: dict = Field(default_factory=dict)


class AgentCard(BaseModel):
    agent_id: str
    name: str
    description: str
    model: str
    tools: list[str]
    handoffs: list[str]
    capabilities: list[str]


class ResumeRequest(BaseModel):
    thread_id: str = Field(..., description="Thread ID to resume")
    value: Any = Field(None, description="Value to pass to the interrupted node")


# ---------------------------------------------------------------------------
# Global agent registry (initialized from domain_agents or programmatic registration)
# ---------------------------------------------------------------------------

_agent_registry: dict[str, Any] = {}
_thread_checkpoints: dict[str, dict] = {}


def register_agent(agent):
    """注册 Agent 到运行时。"""
    _agent_registry[agent.name] = agent


def get_registry() -> dict:
    """获取 agent 注册表。"""
    return _agent_registry


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------

@router.get("/agents", response_model=list[AgentCard])
async def list_agents():
    """列出所有注册的 Agent。"""
    agents = []
    for name, agent in _agent_registry.items():
        card = agent.to_agent_card() if hasattr(agent, "to_agent_card") else {
            "agent_id": name,
            "name": name,
            "description": getattr(agent, "description", ""),
            "model": getattr(agent, "model", ""),
            "tools": [],
            "handoffs": [],
            "capabilities": ["chat"],
        }
        agents.append(AgentCard(**card))
    return agents


@router.get("/agents/{agent_id}", response_model=AgentCard)
async def get_agent(agent_id: str):
    """获取指定 Agent 详情。"""
    agent = _agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    card = agent.to_agent_card() if hasattr(agent, "to_agent_card") else {
        "agent_id": agent_id,
        "name": agent_id,
        "description": getattr(agent, "description", ""),
        "model": getattr(agent, "model", ""),
        "tools": [],
        "handoffs": [],
        "capabilities": ["chat"],
    }
    return AgentCard(**card)


@router.post("/run", response_model=RunResponse)
async def run_agent(request: RunRequest):
    """同步执行 Agent。"""
    agent = _agent_registry.get(request.agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{request.agent_id}' not found")

    run_id = str(uuid.uuid4())
    thread_id = request.thread_id or str(uuid.uuid4())

    # 构建输入
    messages = list(request.messages)
    if request.user_input:
        messages.append({"role": "user", "content": request.user_input})

    try:
        # 构建并执行图
        graph = agent.to_graph()
        result = graph.invoke(
            {"messages": messages},
            config={"configurable": {"thread_id": thread_id}},
        )

        return RunResponse(
            run_id=run_id,
            agent_id=request.agent_id,
            status="completed",
            messages=result.get("messages", []),
            thread_id=thread_id,
        )

    except Exception as e:
        logger.error(f"Agent '{request.agent_id}' execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def stream_agent(request: RunRequest):
    """流式执行 Agent（SSE）。"""
    agent = _agent_registry.get(request.agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{request.agent_id}' not found")

    thread_id = request.thread_id or str(uuid.uuid4())

    messages = list(request.messages)
    if request.user_input:
        messages.append({"role": "user", "content": request.user_input})

    def generate():
        graph = agent.to_graph()
        for chunk in graph.stream(
            {"messages": messages},
            config={"configurable": {"thread_id": thread_id}},
        ):
            yield chunk.to_sse()
        # 结束标记
        yield f"data: {json.dumps({'type': 'done', 'thread_id': thread_id})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Thread-Id": thread_id,
        },
    )


@router.post("/agents/{agent_id}/run", response_model=RunResponse)
async def run_specific_agent(agent_id: str, request: RunRequest):
    """指定 Agent 执行。"""
    request.agent_id = agent_id
    return await run_agent(request)


@router.post("/resume")
async def resume_execution(request: ResumeRequest):
    """恢复中断的执行。"""
    checkpoint_data = _thread_checkpoints.get(request.thread_id)
    if not checkpoint_data:
        raise HTTPException(status_code=404, detail=f"Thread '{request.thread_id}' not found or not interrupted")

    agent_id = checkpoint_data.get("agent_id")
    agent = _agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    try:
        from ..runtime_plane.graph import Command
        graph = agent.to_graph()
        result = graph.invoke(
            Command(resume=request.value),
            config={"configurable": {"thread_id": request.thread_id}},
        )

        return RunResponse(
            run_id=str(uuid.uuid4()),
            agent_id=agent_id,
            status="completed",
            messages=result.get("messages", []),
            thread_id=request.thread_id,
        )

    except Exception as e:
        logger.error(f"Resume error for thread '{request.thread_id}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def runtime_health():
    """运行层健康检查。"""
    return {
        "status": "healthy",
        "registered_agents": len(_agent_registry),
        "agent_names": list(_agent_registry.keys()),
    }
