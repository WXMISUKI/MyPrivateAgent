"""Minimal MCP session handshake and tool-call service."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from datetime import datetime
from typing import Any, Dict, Optional

try:
    from services.mcp_adapter_service import get_mcp_adapter_service
    from services.mcp_registry_service import get_mcp_registry_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.mcp_adapter_service import get_mcp_adapter_service
    from backend.services.mcp_registry_service import get_mcp_registry_service


DEFAULT_CLIENT_INFO = {
    "name": "my-private-agent",
    "title": "MyPrivateAgent",
    "version": "0.1.0",
}


@dataclass(frozen=True)
class McpSessionAuditRecord:
    server_name: str
    transport: str
    phase: str
    request_method: str
    ok: bool
    detail: str = ""
    response_excerpt: str = ""


@dataclass
class McpSessionCacheEntry:
    server_name: str
    handshake: Dict[str, Any]
    updated_at: datetime


class McpSessionService:
    """Provide a minimal MCP initialize/list-tools/tool-call session path."""

    def __init__(self):
        self.registry_service = get_mcp_registry_service()
        self.adapter_service = get_mcp_adapter_service()
        self._session_cache: Dict[str, McpSessionCacheEntry] = {}

    async def handshake_server(self, server_name: str, *, force_refresh: bool = False) -> Dict[str, Any]:
        if not force_refresh:
            cached = self._session_cache.get(server_name)
            if cached is not None:
                return dict(cached.handshake)

        server = self.registry_service.get_server(server_name)
        if server is None:
            raise ValueError("MCP server 不存在")

        initialize_payload = {
            "protocolVersion": str((server.get("metadata") or {}).get("protocol_version") or "2024-11-05"),
            "capabilities": {},
            "clientInfo": dict(DEFAULT_CLIENT_INFO),
        }

        initialize_response = await self.adapter_service.send_session_request(
            server_name=server_name,
            method="initialize",
            params=initialize_payload,
            request_id=1,
        )

        init_result = initialize_response.get("result") if isinstance(initialize_response, dict) else None
        if not isinstance(init_result, dict):
            raise ValueError("MCP initialize 响应无效")

        tools_response = await self.adapter_service.send_session_request(
            server_name=server_name,
            method="tools/list",
            params={},
            request_id=2,
        )
        tools_result = tools_response.get("result") if isinstance(tools_response, dict) else None
        tools = []
        if isinstance(tools_result, dict):
            candidate_tools = tools_result.get("tools")
            if isinstance(candidate_tools, list):
                tools = [
                    {
                        "name": str(item.get("name") or "").strip(),
                        "description": str(item.get("description") or "").strip(),
                    }
                    for item in candidate_tools
                    if isinstance(item, dict) and str(item.get("name") or "").strip()
                ]

        handshake = {
            "server_name": server["name"],
            "transport": server["transport"],
            "status": "ready",
            "protocol_version": str(init_result.get("protocolVersion") or initialize_payload["protocolVersion"]),
            "server_info": dict(init_result.get("serverInfo") or {}),
            "capabilities": dict(init_result.get("capabilities") or {}),
            "tools": tools,
            "audit": [
                self._serialize_audit(
                    McpSessionAuditRecord(
                        server_name=server["name"],
                        transport=server["transport"],
                        phase="initialize",
                        request_method="initialize",
                        ok=True,
                        response_excerpt=self._excerpt(initialize_response),
                    )
                ),
                self._serialize_audit(
                    McpSessionAuditRecord(
                        server_name=server["name"],
                        transport=server["transport"],
                        phase="tools_list",
                        request_method="tools/list",
                        ok=True,
                        response_excerpt=self._excerpt(tools_response),
                    )
                ),
            ],
        }
        self._session_cache[server["name"]] = McpSessionCacheEntry(
            server_name=server["name"],
            handshake=dict(handshake),
            updated_at=datetime.now(),
        )
        return dict(handshake)

    async def call_tool(
        self,
        *,
        server_name: str,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        handshake = await self.handshake_server(server_name)
        available_tools = {item["name"] for item in handshake.get("tools", []) if item.get("name")}
        if tool_name not in available_tools:
            raise ValueError(f"MCP server `{server_name}` 不支持工具 `{tool_name}`")

        response = await self.adapter_service.send_session_request(
            server_name=server_name,
            method="tools/call",
            params={
                "name": tool_name,
                "arguments": dict(arguments or {}),
            },
            request_id=3,
        )
        result = response.get("result") if isinstance(response, dict) else None
        if not isinstance(result, dict):
            raise ValueError("MCP tools/call 响应无效")

        return {
            "server_name": server_name,
            "tool_name": tool_name,
            "status": "ok",
            "structured_content": dict(result.get("structuredContent") or {}),
            "content": self._normalize_tool_result_content(result.get("content")),
            "is_error": bool(result.get("isError", False)),
            "raw_result": result,
            "audit": self._serialize_audit(
                McpSessionAuditRecord(
                    server_name=server_name,
                    transport=handshake.get("transport", ""),
                    phase="tools_call",
                    request_method="tools/call",
                    ok=not bool(result.get("isError", False)),
                    response_excerpt=self._excerpt(response),
                )
            ),
        }

    async def execute_capability(
        self,
        *,
        capability: str,
        request: str,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> str:
        providers = self.registry_service.resolve_servers_for_capability(capability)
        if not providers:
            raise ValueError(f"MCP capability `{capability}` 当前没有可用的启用服务。")

        last_error = None
        for provider in providers:
            try:
                handshake = await self.handshake_server(provider["name"])
                tool_name = self._resolve_tool_name(
                    server=provider,
                    capability=capability,
                    tools=handshake.get("tools", []),
                )
                if not tool_name:
                    last_error = ValueError(f"MCP server `{provider['name']}` 未声明 capability `{capability}` 对应工具")
                    continue

                tool_arguments = dict(arguments or {})
                if request and "request" not in tool_arguments:
                    tool_arguments["request"] = request
                tool_result = await self.call_tool(
                    server_name=provider["name"],
                    tool_name=tool_name,
                    arguments=tool_arguments,
                )
                text_parts = tool_result.get("content") or []
                if text_parts:
                    return "\n".join(text_parts)
                structured = tool_result.get("structured_content") or {}
                if structured:
                    return json.dumps(structured, ensure_ascii=False)
                raw_result = tool_result.get("raw_result") or {}
                return json.dumps(raw_result, ensure_ascii=False)
            except ValueError as exc:
                last_error = exc
                continue

        if last_error is not None:
            raise last_error
        raise ValueError(f"MCP capability `{capability}` 调用失败。")

    def clear_session_cache(self, server_name: Optional[str] = None) -> None:
        if server_name is None:
            self._session_cache.clear()
            return
        self._session_cache.pop(server_name, None)

    def _excerpt(self, payload: Any) -> str:
        text = str(payload or "").strip()
        if len(text) <= 240:
            return text
        return text[:237].rstrip() + "..."

    def _normalize_tool_result_content(self, payload: Any) -> list[str]:
        if not isinstance(payload, list):
            return []

        normalized: list[str] = []
        for item in payload:
            if isinstance(item, dict):
                item_type = str(item.get("type") or "").strip().lower()
                if item_type == "text" and item.get("text") not in (None, ""):
                    normalized.append(str(item.get("text")))
                elif item:
                    normalized.append(json.dumps(item, ensure_ascii=False))
            elif item not in (None, ""):
                normalized.append(str(item))
        return normalized

    def _resolve_tool_name(self, *, server: Dict[str, Any], capability: str, tools: list[Dict[str, Any]]) -> Optional[str]:
        metadata = dict(server.get("metadata") or {})
        capability_tools = dict(metadata.get("capability_tools") or {})
        mapped = str(capability_tools.get(capability) or "").strip()
        available_tool_names = [
            str(item.get("name") or "").strip()
            for item in tools
            if isinstance(item, dict) and str(item.get("name") or "").strip()
        ]
        if mapped and mapped in available_tool_names:
            return mapped

        capability_slug = self._slug(capability)
        for tool_name in available_tool_names:
            if self._slug(tool_name) in {capability_slug, capability_slug.replace("_", ""), capability_slug.split("_")[-1]}:
                return tool_name

        if len(available_tool_names) == 1:
            return available_tool_names[0]
        return None

    def _slug(self, text: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", str(text or "").strip().lower()).strip("_")

    def _serialize_audit(self, record: McpSessionAuditRecord) -> Dict[str, Any]:
        return {
            "server_name": record.server_name,
            "transport": record.transport,
            "phase": record.phase,
            "request_method": record.request_method,
            "ok": record.ok,
            "detail": record.detail,
            "response_excerpt": record.response_excerpt,
        }


_mcp_session_service: Optional[McpSessionService] = None


def get_mcp_session_service() -> McpSessionService:
    global _mcp_session_service
    if _mcp_session_service is None:
        _mcp_session_service = McpSessionService()
    return _mcp_session_service
