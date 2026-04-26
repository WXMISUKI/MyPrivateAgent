"""Minimal MCP adapter and probe service."""

from __future__ import annotations

import asyncio
import json
import shutil
from copy import deepcopy
from asyncio.subprocess import PIPE
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

try:
    from services.mcp_registry_service import get_mcp_registry_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.mcp_registry_service import get_mcp_registry_service


class McpAdapterService:
    """Provide minimal handshake/probe semantics for configured MCP servers."""

    def __init__(self):
        self.registry_service = get_mcp_registry_service()

    def probe_server(self, server_name: str) -> dict:
        server = self.registry_service.get_server(server_name)
        if server is None:
            raise ValueError("MCP server 不存在")

        transport = server.get("transport")
        if transport == "stdio":
            return self._probe_stdio(server)
        if transport == "http":
            return self._probe_http(server)
        raise ValueError("MCP server transport 无效")

    def validate_capabilities(self, capabilities: list[str] | tuple[str, ...]) -> dict:
        missing_capabilities: list[str] = []
        unavailable_capabilities: list[str] = []
        resolved_capabilities: list[dict[str, Any]] = []

        for capability in self._normalize_capability_list(capabilities):
            providers = self.registry_service.resolve_servers_for_capability(capability)
            if not providers:
                missing_capabilities.append(capability)
                continue

            resolved_provider = None
            resolved_probe = None
            for provider in providers:
                probe = self.probe_server(provider["name"])
                if probe.get("status") == "ready":
                    resolved_provider = provider
                    resolved_probe = probe
                    break

            if resolved_provider is None:
                unavailable_capabilities.append(capability)
                continue

            resolved_capabilities.append({
                "capability": capability,
                "provider_name": resolved_provider["name"],
                "transport": resolved_provider["transport"],
                "probe_status": resolved_probe["status"],
            })

        return {
            "ready": not missing_capabilities and not unavailable_capabilities,
            "missing_capabilities": missing_capabilities,
            "unavailable_capabilities": unavailable_capabilities,
            "resolved_capabilities": resolved_capabilities,
        }

    async def execute(self, *, capability: str, request: str, arguments: Optional[Dict[str, Any]] = None) -> str:
        resolution = self.validate_capabilities([capability])
        if resolution["missing_capabilities"]:
            return f"MCP capability `{capability}` 当前没有可用的启用服务。"
        if resolution["unavailable_capabilities"]:
            return f"MCP capability `{capability}` 已配置服务，但当前 provider 不可用。"

        providers = self.registry_service.resolve_servers_for_capability(capability)
        primary = providers[0]
        payload = {
            "capability": capability,
            "request": str(request or "").strip(),
            "arguments": dict(arguments or {}),
        }

        if primary["transport"] == "stdio":
            return await self._execute_stdio(primary, payload)
        if primary["transport"] == "http":
            return await self._execute_http(primary, payload)
        raise ValueError("MCP server transport 无效")

    async def send_session_request(
        self,
        *,
        server_name: str,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        request_id: Optional[Any] = 1,
    ) -> Dict[str, Any]:
        server = self.registry_service.get_server(server_name)
        if server is None:
            raise ValueError("MCP server 不存在")

        probe = self.probe_server(server_name)
        if probe.get("status") != "ready":
            raise ValueError(f"MCP server 当前不可用: {probe.get('detail') or probe.get('status')}")

        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": str(method or "").strip(),
            "params": deepcopy(params or {}),
        }
        return await self._dispatch_json_payload(server, payload)

    def _probe_stdio(self, server: Dict[str, Any]) -> dict:
        command = str(server.get("command") or "").strip()
        resolved_command = shutil.which(command) if command else None
        status = "ready" if resolved_command else "missing_command"
        return {
            "server_name": server["name"],
            "transport": "stdio",
            "status": status,
            "command": command,
            "resolved_command": resolved_command,
            "args": list(server.get("args") or []),
            "detail": "已完成本地命令探测" if resolved_command else "未找到可执行命令",
        }

    def _probe_http(self, server: Dict[str, Any]) -> dict:
        url = str(server.get("url") or "").strip()
        parsed = urlparse(url)
        valid = parsed.scheme in {"http", "https"} and bool(parsed.netloc)
        return {
            "server_name": server["name"],
            "transport": "http",
            "status": "ready" if valid else "invalid_url",
            "url": url,
            "detail": "URL 格式可用，待接入真实握手" if valid else "URL 格式无效",
        }

    async def _execute_stdio(self, server: Dict[str, Any], payload: Dict[str, Any]) -> str:
        try:
            response_text = await self._dispatch_stdio_payload(server, payload)
        except ValueError as exc:
            return str(exc)

        return self._extract_response_text(
            response_text,
            server_name=server["name"],
            transport="stdio",
            payload=payload,
        )

    async def _execute_http(self, server: Dict[str, Any], payload: Dict[str, Any]) -> str:
        try:
            response_text = await self._dispatch_http_payload(server, payload)
        except ValueError as exc:
            return str(exc)

        return self._extract_response_text(
            response_text,
            server_name=server["name"],
            transport="http",
            payload=payload,
        )

    async def _dispatch_json_payload(self, server: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        if server["transport"] == "stdio":
            response_text = await self._dispatch_stdio_payload(server, payload)
        elif server["transport"] == "http":
            response_text = await self._dispatch_http_payload(server, payload)
        else:
            raise ValueError("MCP server transport 无效")

        try:
            data = json.loads(str(response_text or "").strip() or "{}")
        except json.JSONDecodeError as exc:
            raise ValueError(f"MCP server `{server['name']}` 返回了无效 JSON 响应") from exc

        if not isinstance(data, dict):
            raise ValueError(f"MCP server `{server['name']}` 返回了非对象 JSON 响应")
        return data

    async def _dispatch_stdio_payload(self, server: Dict[str, Any], payload: Dict[str, Any]) -> str:
        command = str(server.get("command") or "").strip()
        args = [str(item) for item in (server.get("args") or [])]
        timeout_seconds = self._resolve_timeout_seconds(server)

        try:
            process = await asyncio.create_subprocess_exec(
                command,
                *args,
                stdin=PIPE,
                stdout=PIPE,
                stderr=PIPE,
            )
        except FileNotFoundError as exc:
            raise ValueError(f"MCP stdio 服务 `{server['name']}` 启动失败：未找到命令 `{command}`。") from exc
        except Exception as exc:
            raise ValueError(f"MCP stdio 服务 `{server['name']}` 启动失败：{exc}") from exc

        input_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=input_bytes),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            process.kill()
            await process.communicate()
            raise ValueError(f"MCP stdio 服务 `{server['name']}` 调用超时（{timeout_seconds}s）。") from exc

        if process.returncode not in {0, None}:
            detail = stderr.decode("utf-8", errors="ignore").strip() or stdout.decode("utf-8", errors="ignore").strip()
            raise ValueError(
                f"MCP stdio 服务 `{server['name']}` 调用失败（exit_code={process.returncode}）：{detail or '无输出'}"
            )

        return stdout.decode("utf-8", errors="ignore")

    async def _dispatch_http_payload(self, server: Dict[str, Any], payload: Dict[str, Any]) -> str:
        url = str(server.get("url") or "").strip()
        timeout_seconds = self._resolve_timeout_seconds(server)
        metadata = dict(server.get("metadata") or {})
        headers = {"Content-Type": "application/json; charset=utf-8"}
        headers.update({str(key): str(value) for key, value in dict(metadata.get("headers") or {}).items()})

        request = Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            return await asyncio.to_thread(
                self._perform_http_request,
                request,
                timeout_seconds,
            )
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore").strip()
            raise ValueError(f"MCP http 服务 `{server['name']}` 调用失败（status={exc.code}）：{body or exc.reason}") from exc
        except URLError as exc:
            raise ValueError(f"MCP http 服务 `{server['name']}` 调用失败：{exc.reason}") from exc
        except Exception as exc:
            raise ValueError(f"MCP http 服务 `{server['name']}` 调用失败：{exc}") from exc

    def _perform_http_request(self, request: Request, timeout_seconds: int) -> str:
        with urlopen(request, timeout=timeout_seconds) as response:
            return response.read().decode("utf-8", errors="ignore")

    def _extract_response_text(
        self,
        response_text: str,
        *,
        server_name: str,
        transport: str,
        payload: Dict[str, Any],
    ) -> str:
        stripped = str(response_text or "").strip()
        if not stripped:
            return f"MCP {transport} 服务 `{server_name}` 已完成调用，但未返回内容。"

        try:
            data = json.loads(stripped)
        except json.JSONDecodeError:
            return stripped

        if isinstance(data, dict):
            for key in ("content", "result", "message", "output"):
                value = data.get(key)
                if value not in (None, ""):
                    return str(value)
            return json.dumps(data, ensure_ascii=False)
        if isinstance(data, list):
            return json.dumps(data, ensure_ascii=False)
        return str(data)

    def _resolve_timeout_seconds(self, server: Dict[str, Any]) -> int:
        metadata = dict(server.get("metadata") or {})
        timeout_value = metadata.get("timeout_seconds", 15)
        try:
            timeout_seconds = int(timeout_value)
        except (TypeError, ValueError):
            timeout_seconds = 15
        return max(1, timeout_seconds)

    def _normalize_capability_list(self, values: list[str] | tuple[str, ...]) -> list[str]:
        normalized: list[str] = []
        for value in values or []:
            text = str(value or "").strip()
            if text:
                normalized.append(text)
        return sorted(dict.fromkeys(normalized))


_mcp_adapter_service: Optional[McpAdapterService] = None


def get_mcp_adapter_service() -> McpAdapterService:
    global _mcp_adapter_service
    if _mcp_adapter_service is None:
        _mcp_adapter_service = McpAdapterService()
    return _mcp_adapter_service
