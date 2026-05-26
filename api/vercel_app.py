from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse


AUTH_MODE = os.getenv("AUTH_MODE", "demo_guest").strip() or "demo_guest"
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "doubao").strip() or "doubao"
ARK_API_KEY = os.getenv("ARK_API_KEY", "").strip()
ARK_BASE_URL = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3").rstrip("/")
ARK_MODEL = os.getenv("ARK_MODEL", "").strip() or DEFAULT_MODEL
EFFECTIVE_MODEL = ARK_MODEL or DEFAULT_MODEL


app = FastAPI(title="MyPrivateAgent Vercel Runtime", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _guest_user() -> dict[str, Any]:
    return {
        "id": "vercel-demo-user",
        "username": "guest",
        "display_name": "Guest",
        "role": "demo_guest",
    }


def _token_for_guest() -> str:
    return "vercel-demo-token"


def _sse(event: dict[str, Any]) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


def _extract_bearer(authorization: str | None) -> str:
    value = str(authorization or "").strip()
    if value.lower().startswith("bearer "):
        return value[7:].strip()
    return value


def _require_user(authorization: str | None) -> dict[str, Any]:
    token = _extract_bearer(authorization)
    if token != _token_for_guest():
        raise HTTPException(status_code=401, detail="Unauthorized")
    return _guest_user()


def _resolve_provider_model(model_name: str | None = None) -> str:
    requested = str(model_name or "").strip()
    if not requested or requested == DEFAULT_MODEL:
        return EFFECTIVE_MODEL
    return requested


def _chat_completion(message: str, model_name: str | None = None) -> str:
    if not ARK_API_KEY:
        return (
            "当前 Vercel 一体化部署运行在轻量 Serverless 模式。"
            "我已经收到你的问题："
            f"{message}"
        )

    payload = {
        "model": _resolve_provider_model(model_name),
        "messages": [
            {
                "role": "system",
                "content": "你是 MyPrivateAgent 的线上演示助手，请用中文、简洁、可靠地回答用户。",
            },
            {"role": "user", "content": message},
        ],
        "temperature": 0.3,
    }
    request = urllib.request.Request(
        f"{ARK_BASE_URL}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {ARK_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return f"模型调用失败，当前返回轻量兜底回复。错误：{exc}"

    choices = body.get("choices") or []
    if not choices:
        return "模型没有返回有效内容。"
    content = (choices[0].get("message") or {}).get("content")
    return str(content or "").strip() or "模型返回为空。"


@app.get("/api/health")
@app.get("/api/health/live")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "runtime": "vercel_serverless",
        "mode": "lightweight",
    }


@app.get("/api/runtime-profile")
def runtime_profile() -> dict[str, Any]:
    return {
        "agent_mode": "vercel_demo",
        "auth_mode": AUTH_MODE,
        "default_model": EFFECTIVE_MODEL,
        "runtime": "vercel_serverless",
        "storage": {"mode": "memory_only", "persistent": False},
        "capabilities": {
            "chat": True,
            "streaming": True,
            "skills": False,
            "mcp": False,
            "local_files": False,
        },
        "failover_thresholds": {"medium": 0.2, "high": 0.5},
    }


@app.get("/api/runtime-profile/{_:path}")
def runtime_profile_detail() -> dict[str, Any]:
    return {"items": [], "events": [], "summary": {}, "runtime": "vercel_serverless"}


@app.patch("/api/runtime-profile")
@app.patch("/api/runtime-profile/embedded-runtime-bootstrap")
def update_runtime_profile(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"ok": True, "applied": payload or {}, "runtime": "vercel_serverless"}


@app.post("/api/auth/guest")
def auth_guest() -> dict[str, Any]:
    return {"access_token": _token_for_guest(), "token_type": "bearer", "user": _guest_user()}


@app.get("/api/auth/me")
@app.get("/api/auth/verify")
def auth_me(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    return _require_user(authorization)


@app.post("/api/auth/login")
def auth_login() -> dict[str, Any]:
    return {"access_token": _token_for_guest(), "token_type": "bearer", "user": _guest_user()}


@app.post("/api/auth/logout")
def auth_logout() -> dict[str, Any]:
    return {"ok": True}


@app.get("/api/models")
def models() -> list[dict[str, Any]]:
    return [
        {
            "name": EFFECTIVE_MODEL,
            "display_name": DEFAULT_MODEL if DEFAULT_MODEL != EFFECTIVE_MODEL else EFFECTIVE_MODEL,
            "provider": "ark" if ARK_API_KEY else "vercel-demo",
            "is_default": True,
            "available": True,
        }
    ]


@app.get("/api/providers")
def providers() -> list[dict[str, Any]]:
    return [
        {
            "name": "ark" if ARK_API_KEY else "vercel-demo",
            "display_name": "Ark" if ARK_API_KEY else "Vercel Demo",
            "enabled": True,
            "configured": bool(ARK_API_KEY),
            "default_model": DEFAULT_MODEL,
        }
    ]


@app.get("/api/commands")
def commands() -> list[dict[str, Any]]:
    return []


@app.get("/api/conversations")
def conversations() -> list[dict[str, Any]]:
    return []


@app.post("/api/conversations")
def create_conversation(payload: dict[str, Any]) -> dict[str, Any]:
    now = int(time.time() * 1000)
    return {"id": f"vercel_{now}", "title": payload.get("title") or "New chat", "messages": []}


@app.post("/api/chat")
async def chat(request: Request, authorization: str | None = Header(default=None)) -> StreamingResponse:
    _require_user(authorization)
    payload = await request.json()
    message = str(payload.get("message") or "").strip()
    model_name = payload.get("model_name") or DEFAULT_MODEL
    conversation_id = payload.get("conversation_id") or f"vercel_{int(time.time() * 1000)}"

    def generate():
        yield _sse({"type": "conversation_id", "conversation_id": conversation_id})
        yield _sse({"type": "status", "status_kind": "execution_progress", "phase": "vercel", "content": "Vercel 轻量运行时已接收请求"})
        answer = _chat_completion(message, str(model_name))
        yield _sse({"type": "content", "content": answer})
        yield _sse({"type": "done", "content": answer, "message_id": int(time.time() * 1000)})

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/chat/abort")
def abort_chat() -> dict[str, Any]:
    return {"ok": True}


@app.post("/api/chat/regenerate")
def regenerate_chat() -> dict[str, Any]:
    return {"content": "当前 Vercel 轻量模式暂不支持重新生成。"}


@app.get("/api/{_:path}")
def fallback_api() -> JSONResponse:
    return JSONResponse({"items": [], "message": "Vercel lightweight runtime"}, status_code=200)
