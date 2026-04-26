from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

try:
    from agent_server.dependencies import get_current_user
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
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.agent_server.dependencies import get_current_user
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


router = APIRouter(prefix="/api/mcp", tags=["MCP"])


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
):
    _ = current_user
    service = get_mcp_registry_service()
    try:
        return service.upsert_server(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/servers/{server_name}", response_model=McpServerResponse)
def update_mcp_server(
    server_name: str,
    payload: McpServerUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
):
    _ = current_user
    service = get_mcp_registry_service()
    try:
        return service.update_server(server_name, payload.model_dump(exclude_unset=True))
    except ValueError as exc:
        detail = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if "不存在" in detail else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.delete("/servers/{server_name}")
def delete_mcp_server(
    server_name: str,
    current_user: Annotated[User, Depends(get_current_user)],
):
    _ = current_user
    service = get_mcp_registry_service()
    if not service.delete_server(server_name):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP server 不存在")
    return success_response("MCP server 已删除", server_name=server_name)


@router.post("/servers/{server_name}/enable", response_model=McpServerResponse)
def enable_mcp_server(
    server_name: str,
    current_user: Annotated[User, Depends(get_current_user)],
):
    _ = current_user
    service = get_mcp_registry_service()
    try:
        return service.set_enabled(server_name, True)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/servers/{server_name}/disable", response_model=McpServerResponse)
def disable_mcp_server(
    server_name: str,
    current_user: Annotated[User, Depends(get_current_user)],
):
    _ = current_user
    service = get_mcp_registry_service()
    try:
        return service.set_enabled(server_name, False)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


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
):
    _ = current_user
    service = get_mcp_adapter_service()
    try:
        return service.probe_server(server_name)
    except ValueError as exc:
        detail = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if "不存在" in detail else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.post("/servers/{server_name}/handshake", response_model=McpSessionHandshakeResponse)
async def handshake_mcp_server(
    server_name: str,
    current_user: Annotated[User, Depends(get_current_user)],
):
    _ = current_user
    service = get_mcp_session_service()
    try:
        return await service.handshake_server(server_name)
    except ValueError as exc:
        detail = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if "不存在" in detail else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.post("/servers/{server_name}/tools/{tool_name}/call", response_model=McpToolCallResponse)
async def call_mcp_tool(
    server_name: str,
    tool_name: str,
    payload: McpToolCallRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    _ = current_user
    service = get_mcp_session_service()
    try:
        return await service.call_tool(
            server_name=server_name,
            tool_name=tool_name,
            arguments=payload.arguments,
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if "不存在" in detail or "不支持工具" in detail else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=detail) from exc
