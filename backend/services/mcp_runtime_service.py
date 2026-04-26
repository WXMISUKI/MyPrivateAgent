"""Runtime MCP capability binding for the harness tool registry."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional, Set

try:
    from agent_framework.tools import ToolRenderMode, ToolSpec
    from harness.tool_registry import BaseTool, PermissionLevel, ToolRegistry
    from services.mcp_adapter_service import get_mcp_adapter_service
    from services.mcp_registry_service import get_mcp_registry_service
    from services.mcp_session_service import get_mcp_session_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.agent_framework.tools import ToolRenderMode, ToolSpec
    from backend.harness.tool_registry import BaseTool, PermissionLevel, ToolRegistry
    from backend.services.mcp_adapter_service import get_mcp_adapter_service
    from backend.services.mcp_registry_service import get_mcp_registry_service
    from backend.services.mcp_session_service import get_mcp_session_service


class McpRuntimeService:
    """Expose enabled MCP capabilities as runtime tools."""

    def __init__(self):
        self.registry_service = get_mcp_registry_service()
        self.adapter_service = get_mcp_adapter_service()
        self.session_service = get_mcp_session_service()
        self._registered_tool_names: Set[str] = set()

    def sync_registry_tools(self, tool_registry: ToolRegistry) -> None:
        capability_catalog = self.registry_service.build_capability_catalog()
        active_tool_names: Set[str] = set()

        for entry in capability_catalog.get("capabilities", []):
            capability = entry["capability"]
            tool_name = self._build_tool_name(capability)
            active_tool_names.add(tool_name)
            tool_registry.register(self._build_base_tool(tool_name, capability))
            tool_registry.register_tool_spec(self._build_tool_spec(tool_name, capability))
            tool_registry.register_tool_definition(self._build_tool_definition(tool_name, capability))

        for stale_name in self._registered_tool_names - active_tool_names:
            tool_registry.unregister(stale_name)

        self._registered_tool_names = active_tool_names

    def validate_required_capabilities(self, capabilities: list[str] | tuple[str, ...]) -> dict:
        return self.adapter_service.validate_capabilities(capabilities)

    async def execute_capability(self, capability: str, request: str, arguments: Optional[Dict[str, Any]] = None) -> str:
        try:
            return await self.session_service.execute_capability(
                capability=capability,
                request=request,
                arguments=arguments,
            )
        except ValueError:
            return await self.adapter_service.execute(
                capability=capability,
                request=request,
                arguments=arguments,
            )

    def _build_base_tool(self, tool_name: str, capability: str) -> BaseTool:
        async def _invoke(request: str, arguments: Optional[Dict[str, Any]] = None) -> str:
            return await self.execute_capability(capability, request=request, arguments=arguments)

        return BaseTool(
            name=tool_name,
            description=f"调用 MCP capability `{capability}` 的运行时工具。",
            func=_invoke,
            permission_level=PermissionLevel.ASK,
            parameters={
                "request": {
                    "type": "string",
                    "description": f"发送给 MCP capability `{capability}` 的请求内容。"
                },
                "arguments": {
                    "type": "object",
                    "description": "可选附加参数对象。",
                },
            },
        )

    def _build_tool_spec(self, tool_name: str, capability: str) -> ToolSpec:
        return ToolSpec(
            name=tool_name,
            description=f"MCP capability `{capability}` 的运行时入口。",
            permission_level="ask",
            deterministic=False,
            safe_to_rephrase=False,
            render_mode=ToolRenderMode.PLAIN_TEXT,
            supports_cache=False,
            passthrough_strategy="never",
            tags=("mcp", capability),
        )

    def _build_tool_definition(self, tool_name: str, capability: str) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": tool_name,
                "description": f"调用 MCP capability `{capability}`。仅在确实需要访问外部能力时使用。",
                "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "request": {
                            "type": "string",
                            "description": f"发送给 capability `{capability}` 的请求。"
                        },
                        "arguments": {
                            "type": "object",
                            "description": "可选附加参数对象。"
                        },
                    },
                    "required": ["request"],
                    "additionalProperties": False,
                },
            },
        }

    def _build_tool_name(self, capability: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "_", capability.lower()).strip("_")
        return f"mcp_{slug}"


_mcp_runtime_service: Optional[McpRuntimeService] = None


def get_mcp_runtime_service() -> McpRuntimeService:
    global _mcp_runtime_service
    if _mcp_runtime_service is None:
        _mcp_runtime_service = McpRuntimeService()
    return _mcp_runtime_service
