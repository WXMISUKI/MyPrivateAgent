"""
Agent Runtime API - 运行层 API 端点

提供智能体运行时的 REST API：
- POST /api/agent-runtime/run              同步执行
- POST /api/agent-runtime/stream           流式执行（SSE）
- POST /api/agent-runtime/upload-and-run   上传文件并执行
- POST /api/agent-runtime/resume           恢复中断的执行
- GET  /api/agent-runtime/agents           列出所有注册的 agent
- GET  /api/agent-runtime/agents/{id}      获取 agent 详情
- POST /api/agent-runtime/agents/{id}/run  指定 agent 执行
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-runtime", tags=["agent-runtime"])

# 上传文件存储目录
UPLOAD_DIR = Path(".myagent/agent-runtime-uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


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
# Global agent registry
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
# Intent recognition
# ---------------------------------------------------------------------------

def recognize_intent(user_input: str) -> str | None:
    """意图识别：根据用户输入匹配 Agent。"""
    try:
        from ..domain_agents.hazardous_project_recognition.bootstrap import match_intent
        agent_id = match_intent(user_input)
        if agent_id:
            return agent_id
    except ImportError:
        pass

    # 通用意图匹配：检查 agent metadata 中的 intent_keywords
    text = user_input.lower()
    for name, agent in _agent_registry.items():
        keywords = getattr(agent, "metadata", {}).get("intent_keywords", [])
        for kw in keywords:
            if kw.lower() in text:
                return name

    return None


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
    # 意图识别：如果没有指定 agent_id，尝试自动识别
    agent_id = request.agent_id
    if not agent_id or agent_id == "auto":
        recognized = recognize_intent(request.user_input)
        if recognized:
            agent_id = recognized
        else:
            raise HTTPException(status_code=400, detail="无法识别意图，请指定 agent_id")

    agent = _agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    run_id = str(uuid.uuid4())
    thread_id = request.thread_id or str(uuid.uuid4())

    # 构建输入
    messages = list(request.messages)
    if request.user_input:
        messages.append({"role": "user", "content": request.user_input})

    try:
        graph = agent.to_graph().compile()
        result = graph.invoke(
            {"messages": messages},
            config={"configurable": {"thread_id": thread_id}},
        )

        return RunResponse(
            run_id=run_id,
            agent_id=agent_id,
            status="completed",
            messages=result.get("messages", []),
            thread_id=thread_id,
        )

    except Exception as e:
        logger.error(f"Agent '{agent_id}' execution error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def stream_agent(request: RunRequest):
    """流式执行 Agent（SSE）。"""
    agent_id = request.agent_id
    if not agent_id or agent_id == "auto":
        recognized = recognize_intent(request.user_input)
        if recognized:
            agent_id = recognized
        else:
            raise HTTPException(status_code=400, detail="无法识别意图，请指定 agent_id")

    agent = _agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    thread_id = request.thread_id or str(uuid.uuid4())
    messages = list(request.messages)
    if request.user_input:
        messages.append({"role": "user", "content": request.user_input})

    def generate():
        graph = agent.to_graph().compile()
        for chunk in graph.stream(
            {"messages": messages},
            config={"configurable": {"thread_id": thread_id}},
        ):
            yield chunk.to_sse()
        yield f"data: {json.dumps({'type': 'done', 'thread_id': thread_id})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.post("/upload-and-run")
async def upload_and_run(
    file: UploadFile = File(..., description="上传的文件"),
    agent_id: str = Form("auto", description="Agent ID，auto 表示自动识别"),
    user_input: str = Form("", description="用户输入"),
):
    """上传文件并执行 Agent。

    支持的文件格式：.doc, .docx, .xlsx, .xls, .csv
    """
    # 保存上传文件
    file_id = str(uuid.uuid4())[:8]
    safe_name = f"{file_id}_{file.filename}"
    file_path = UPLOAD_DIR / safe_name

    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {e}")

    # 意图识别
    if agent_id == "auto":
        # 从用户输入或文件名推断意图
        search_text = f"{user_input} {file.filename}"
        recognized = recognize_intent(search_text)
        if recognized:
            agent_id = recognized
        else:
            # 默认使用危大工程识别（因为上传了文件）
            agent_id = "hazardous_project_recognition"

    agent = _agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    run_id = str(uuid.uuid4())
    thread_id = str(uuid.uuid4())

    # 提取文档内容
    try:
        from ..domain_agents.hazardous_project_recognition.tools.document_extractor import extract_document_content
        doc_result = extract_document_content(str(file_path))
    except Exception as e:
        doc_result = {"status": "error", "error": str(e)}

    # 构建输入消息（包含提取的文档内容）
    prompt = user_input or f"请识别文件 {file.filename} 中的危大工程清单，按步骤分析并输出结果。"
    if doc_result.get("status") == "success":
        # 优先使用表格数据（结构化更好）
        tables_text = ""
        for t in doc_result.get("tables", []):
            headers = t.get("headers", [])
            rows = t.get("rows", [])
            if headers:
                tables_text += " | ".join(headers) + "\n"
            for row in rows:
                tables_text += " | ".join(row) + "\n"
        # 如果没有表格，用全文
        if not tables_text.strip():
            tables_text = doc_result.get("text_content", "")
        content = f"{prompt}\n\n文件名：{file.filename}\n\n{tables_text}"
        messages = [{"role": "user", "content": content}]
    else:
        messages = [{"role": "user", "content": f"{prompt}\n\n文件提取失败：{doc_result.get('error', '未知错误')}"}]

    try:
        graph = agent.to_graph().compile()
        result = graph.invoke(
            {"messages": messages},
            config={"configurable": {"thread_id": thread_id}},
        )

        return RunResponse(
            run_id=run_id,
            agent_id=agent_id,
            status="completed",
            messages=result.get("messages", []),
            thread_id=thread_id,
            metadata={
                "uploaded_file": file.filename,
                "file_path": str(file_path),
                "file_size": file.size,
            },
        )

    except Exception as e:
        logger.error(f"Upload-and-run error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=404, detail=f"Thread '{request.thread_id}' not found")

    agent_id = checkpoint_data.get("agent_id")
    agent = _agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    try:
        from ..runtime_plane.graph import Command
        graph = agent.to_graph().compile()
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
        logger.error(f"Resume error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intents")
async def list_intents():
    """列出所有已注册的意图关键词映射。"""
    intents = {}
    for name, agent in _agent_registry.items():
        keywords = getattr(agent, "metadata", {}).get("intent_keywords", [])
        if keywords:
            intents[name] = keywords
    return {"intents": intents}


@router.get("/health")
async def runtime_health():
    """运行层健康检查。"""
    return {
        "status": "healthy",
        "registered_agents": len(_agent_registry),
        "agent_names": list(_agent_registry.keys()),
    }
