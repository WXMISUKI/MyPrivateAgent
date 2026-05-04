from __future__ import annotations

import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

try:
    from agent_server.dependencies import get_current_user, get_db
    from agent_server.http import success_response
    from models import User
    from schemas import (
        McpCapabilityCatalogResponse,
        McpProbeResponse,
        McpSessionHandshakeResponse,
        McpServerCreate,
        McpServerResponse,
        McpServerUpdate,
        McpToolCallRequest,
        McpToolCallResponse,
    )
    from services.mcp_adapter_service import get_mcp_adapter_service
    from services.mcp_registry_service import get_mcp_registry_service
    from services.mcp_session_service import get_mcp_session_service
    from services.run_trace_service import get_run_trace_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.agent_server.dependencies import get_current_user, get_db
    from backend.agent_server.http import success_response
    from backend.models import User
    from backend.schemas import (
        McpCapabilityCatalogResponse,
        McpProbeResponse,
        McpSessionHandshakeResponse,
        McpServerCreate,
        McpServerResponse,
        McpServerUpdate,
        McpToolCallRequest,
        McpToolCallResponse,
    )
    from backend.services.mcp_adapter_service import get_mcp_adapter_service
    from backend.services.mcp_registry_service import get_mcp_registry_service
    from backend.services.mcp_session_service import get_mcp_session_service
    from backend.services.run_trace_service import get_run_trace_service


router = APIRouter(prefix="/api/mcp", tags=["MCP"])
IS_VERCEL = os.getenv("VERCEL", "").strip() == "1"


def _record_mcp_timeline(
    *,
    db: Session,
    conversation_id: int | None,
    event_type: str,
    summary: str,
    detail: str = "",
    severity: str = "info",
    payload: dict | None = None,
) -> dict:
    trace_service = get_run_trace_service(db)
    snapshot_ref = trace_service.build_snapshot_ref(
        source="mcp",
        event_type=event_type,
        conversation_id=conversation_id,
    )
    payload = {
        **(payload or {}),
        "snapshot_ref": snapshot_ref,
    }
    trace_written = trace_service.append_latest_active_item_trace(
        user_id=None,
        conversation_id=conversation_id,
        source="mcp",
        event_type=event_type,
        summary=summary,
        detail=detail,
        severity=severity,
        payload=payload,
    )
    audit_written = trace_service.append_latest_active_item_audit(
        user_id=None,
        conversation_id=conversation_id,
        event_type=event_type,
        content=summary,
        payload=payload,
    )
    return {
        "trace_written": trace_written,
        "audit_written": audit_written,
        "conversation_id": conversation_id,
        "snapshot_ref": snapshot_ref,
    }


@router.get("/servers", response_model=list[McpServerResponse])
def list_mcp_servers(
    current_user: Annotated[User, Depends(get_current_user)],
):
    _ = current_user
    service = get_mcp_registry_service()
    return service.list_servers()


@router.post("/servers", response_model=McpServerResponse, status_code=status.HTTP_201_CREATED)
def create_mcp_server(
    payload: McpServerCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    conversation_id: int | None = None,
    db: Session = Depends(get_db),
):
    _ = current_user
    if IS_VERCEL and payload.transport == "stdio":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vercel 环境不支持 stdio 型 MCP，请使用 http 型远程 MCP。",
        )
    service = get_mcp_registry_service()
    try:
        result = service.upsert_server(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    _record_mcp_timeline(
        db=db,
        conversation_id=conversation_id,
        event_type="mcp_server_created",
        summary=f"MCP 服务 `{result.name}` 已创建",
        detail=f"transport={result.transport}",
        severity="success",
        payload={
            "server_name": result.name,
            "transport": result.transport,
            "capabilities": list(result.capabilities or []),
        },
    )
    return result


@router.patch("/servers/{server_name}", response_model=McpServerResponse)
def update_mcp_server(
    server_name: str,
    payload: McpServerUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    conversation_id: int | None = None,
    db: Session = Depends(get_db),
):
    _ = current_user
    service = get_mcp_registry_service()
    try:
        result = service.update_server(server_name, payload.model_dump(exclude_unset=True))
    except ValueError as exc:
        detail = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if "不存在" in detail else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=detail) from exc
    _record_mcp_timeline(
        db=db,
        conversation_id=conversation_id,
        event_type="mcp_server_updated",
        summary=f"MCP 服务 `{server_name}` 已更新",
        detail=f"transport={result.transport}",
        severity="info",
        payload={
            "server_name": result.name,
            "transport": result.transport,
            "capabilities": list(result.capabilities or []),
        },
    )
    return result


@router.delete("/servers/{server_name}")
def delete_mcp_server(
    server_name: str,
    current_user: Annotated[User, Depends(get_current_user)],
    conversation_id: int | None = None,
    db: Session = Depends(get_db),
):
    _ = current_user
    service = get_mcp_registry_service()
    if not service.delete_server(server_name):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP server 不存在")
    _record_mcp_timeline(
        db=db,
        conversation_id=conversation_id,
        event_type="mcp_server_deleted",
        summary=f"MCP 服务 `{server_name}` 已删除",
        severity="warning",
        payload={"server_name": server_name},
    )
    return success_response("MCP server 已删除", server_name=server_name)


@router.post("/servers/{server_name}/enable", response_model=McpServerResponse)
def enable_mcp_server(
    server_name: str,
    current_user: Annotated[User, Depends(get_current_user)],
    conversation_id: int | None = None,
    db: Session = Depends(get_db),
):
    _ = current_user
    service = get_mcp_registry_service()
    try:
        result = service.set_enabled(server_name, True)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    _record_mcp_timeline(
        db=db,
        conversation_id=conversation_id,
        event_type="mcp_server_enabled",
        summary=f"MCP 服务 `{server_name}` 已启用",
        severity="success",
        payload={"server_name": server_name},
    )
    return result


@router.post("/servers/{server_name}/disable", response_model=McpServerResponse)
def disable_mcp_server(
    server_name: str,
    current_user: Annotated[User, Depends(get_current_user)],
    conversation_id: int | None = None,
    db: Session = Depends(get_db),
):
    _ = current_user
    service = get_mcp_registry_service()
    try:
        result = service.set_enabled(server_name, False)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    _record_mcp_timeline(
        db=db,
        conversation_id=conversation_id,
        event_type="mcp_server_disabled",
        summary=f"MCP 服务 `{server_name}` 已停用",
        severity="warning",
        payload={"server_name": server_name},
    )
    return result


@router.get("/catalog", response_model=McpCapabilityCatalogResponse)
def get_mcp_capability_catalog(
    current_user: Annotated[User, Depends(get_current_user)],
):
    _ = current_user
    service = get_mcp_registry_service()
    return service.build_capability_catalog()


@router.post("/servers/{server_name}/probe", response_model=McpProbeResponse)
def probe_mcp_server(
    server_name: str,
    current_user: Annotated[User, Depends(get_current_user)],
    conversation_id: int | None = None,
    db: Session = Depends(get_db),
):
    _ = current_user
    service = get_mcp_adapter_service()
    try:
        result = service.probe_server(server_name)
    except ValueError as exc:
        detail = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if "不存在" in detail else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=detail) from exc
    _record_mcp_timeline(
        db=db,
        conversation_id=conversation_id,
        event_type="mcp_server_probed",
        summary=f"MCP 服务 `{server_name}` 已完成 Probe",
        detail=f"status={getattr(result, 'status', None) or getattr(result, 'server_status', None) or 'ok'}",
        severity="info",
        payload={"server_name": server_name},
    )
    return result


@router.post("/servers/{server_name}/handshake", response_model=McpSessionHandshakeResponse)
async def handshake_mcp_server(
    server_name: str,
    current_user: Annotated[User, Depends(get_current_user)],
    conversation_id: int | None = None,
    db: Session = Depends(get_db),
):
    _ = current_user
    service = get_mcp_session_service()
    try:
        result = await service.handshake_server(server_name)
    except ValueError as exc:
        detail = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if "不存在" in detail else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=detail) from exc
    _record_mcp_timeline(
        db=db,
        conversation_id=conversation_id,
        event_type="mcp_server_handshake_completed",
        summary=f"MCP 服务 `{server_name}` 已完成 Handshake",
        detail=f"tools={len(getattr(result, 'tools', []) or [])}",
        severity="success",
        payload={"server_name": server_name},
    )
    return result


@router.post("/servers/{server_name}/tools/{tool_name}/call", response_model=McpToolCallResponse)
async def call_mcp_tool(
    server_name: str,
    tool_name: str,
    payload: McpToolCallRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    conversation_id: int | None = None,
    db: Session = Depends(get_db),
):
    _ = current_user
    service = get_mcp_session_service()
    try:
        result = await service.call_tool(
            server_name=server_name,
            tool_name=tool_name,
            arguments=payload.arguments,
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if "不存在" in detail or "不支持工具" in detail else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=detail) from exc
    _record_mcp_timeline(
        db=db,
        conversation_id=conversation_id,
        event_type="mcp_tool_call_completed",
        summary=f"MCP 工具 `{server_name}.{tool_name}` 调用已完成",
        detail="工具调用已返回结果。",
        severity="success",
        payload={
            "server_name": server_name,
            "tool_name": tool_name,
            "arguments": payload.arguments,
        },
    )
    return result
