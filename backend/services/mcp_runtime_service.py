"""Runtime MCP capability binding for the harness tool registry."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

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


class McpRuntimeAudit:
    """Small in-memory audit buffer for MCP runtime boundary events."""

    def __init__(self, max_records: int = 100):
        self.max_records = max(1, int(max_records or 100))
        self._records: List[Dict[str, Any]] = []

    def record(self, event_type: str, **payload: Any) -> Dict[str, Any]:
        record = {
            "event_type": str(event_type or "").strip(),
            "timestamp": datetime.now().isoformat(),
            **dict(payload or {}),
        }
        self._records.append(record)
        self._records = self._records[-self.max_records:]
        return dict(record)

    def list_records(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        records = self._records[-limit:] if limit else self._records
        return [dict(item) for item in records]

    def build_health(self) -> Dict[str, Any]:
        return {
            "component_id": "mcp_audit",
            "display_name": "MCP Audit",
            "status": "healthy",
            "detail": f"{len(self._records)} runtime audit records buffered",
        }


class McpRuntimeRegistry:
    """Registry boundary for MCP server and capability catalog access."""

    def __init__(self, registry_service: Any):
        self.registry_service = registry_service
        self.last_error = ""

    def build_capability_catalog(self) -> Dict[str, Any]:
        self.last_error = ""
        try:
            return dict(self.registry_service.build_capability_catalog() or {})
        except Exception as exc:
            self.last_error = str(exc)
            return {"total_servers": 0, "enabled_servers": 0, "capabilities": []}

    def resolve_servers_for_capability(self, capability: str) -> List[Dict[str, Any]]:
        return list(self.registry_service.resolve_servers_for_capability(capability) or [])

    def build_health(self, catalog: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        catalog = catalog or self.build_capability_catalog()
        return {
            "component_id": "mcp_registry",
            "display_name": "MCP Registry",
            "status": "unavailable" if self.last_error else "healthy",
            "detail": self.last_error or f"{len(catalog.get('capabilities') or [])} capabilities registered",
        }


class McpSessionManager:
    """Session boundary for initialize/tools-list/tools-call execution."""

    def __init__(self, session_service: Any):
        self.session_service = session_service
        self.last_error = ""

    async def execute_capability(self, *, capability: str, request: str, arguments: Optional[Dict[str, Any]] = None) -> str:
        self.last_error = ""
        try:
            return await self.session_service.execute_capability(
                capability=capability,
                request=request,
                arguments=arguments,
            )
        except Exception as exc:
            self.last_error = str(exc)
            raise

    def build_health(self) -> Dict[str, Any]:
        return {
            "component_id": "mcp_session_manager",
            "display_name": "MCP Session Manager",
            "status": "degraded" if self.last_error else "healthy",
            "detail": self.last_error or "session boundary ready",
        }


class McpCapabilityRouter:
    """Capability validation and fallback boundary."""

    def __init__(self, adapter_service: Any, audit: McpRuntimeAudit):
        self.adapter_service = adapter_service
        self.audit = audit
        self.last_error = ""

    def validate_required_capabilities(self, capabilities: list[str] | tuple[str, ...]) -> dict:
        normalized = self._normalize_capability_list(capabilities)
        self.last_error = ""
        try:
            return self.adapter_service.validate_capabilities(normalized)
        except Exception as exc:
            self.last_error = str(exc)
            self.audit.record(
                "capability_validation_failed",
                component="mcp_capability_router",
                capabilities=normalized,
                error=self.last_error,
            )
            return {
                "ready": False,
                "missing_capabilities": [],
                "unavailable_capabilities": normalized,
                "resolved_capabilities": [],
                "diagnostics": {
                    "component": "mcp_capability_router",
                    "error": self.last_error,
                },
            }

    async def execute_fallback(self, *, capability: str, request: str, arguments: Optional[Dict[str, Any]] = None) -> str:
        return await self.adapter_service.execute(
            capability=capability,
            request=request,
            arguments=arguments,
        )

    def build_health(self) -> Dict[str, Any]:
        return {
            "component_id": "mcp_capability_router",
            "display_name": "MCP Capability Router",
            "status": "degraded" if self.last_error else "healthy",
            "detail": self.last_error or "capability router ready",
        }

    def _normalize_capability_list(self, values: list[str] | tuple[str, ...]) -> list[str]:
        normalized: list[str] = []
        for value in values or []:
            text = str(value or "").strip()
            if text:
                normalized.append(text)
        return sorted(dict.fromkeys(normalized))


class McpRuntimeService:
    """Expose enabled MCP capabilities as runtime tools."""

    def __init__(self):
        self.registry_service = get_mcp_registry_service()
        self.adapter_service = get_mcp_adapter_service()
        self.session_service = get_mcp_session_service()
        self.audit = McpRuntimeAudit()
        self.runtime_registry = McpRuntimeRegistry(self.registry_service)
        self.session_manager = McpSessionManager(self.session_service)
        self.capability_router = McpCapabilityRouter(self.adapter_service, self.audit)
        self._registered_tool_names: Set[str] = set()

    def sync_registry_tools(self, tool_registry: ToolRegistry) -> None:
        self._refresh_components()
        capability_catalog = self.runtime_registry.build_capability_catalog()
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
        self.audit.record(
            "registry_tools_synced",
            capability_count=len(active_tool_names),
            tool_names=sorted(active_tool_names),
        )

    def validate_required_capabilities(self, capabilities: list[str] | tuple[str, ...]) -> dict:
        self._refresh_components()
        state = self.capability_router.validate_required_capabilities(capabilities)
        if state.get("ready"):
            self.audit.record(
                "capability_validation_succeeded",
                capabilities=list(capabilities or []),
                resolved_capabilities=list(state.get("resolved_capabilities") or []),
            )
        return state

    async def execute_capability(self, capability: str, request: str, arguments: Optional[Dict[str, Any]] = None) -> str:
        self._refresh_components()
        try:
            result = await self.session_manager.execute_capability(
                capability=capability,
                request=request,
                arguments=arguments,
            )
            self.audit.record("session_execute_succeeded", capability=capability)
            return result
        except ValueError as exc:
            self.audit.record("session_execute_failed", capability=capability, error=str(exc))
            result = await self.capability_router.execute_fallback(
                capability=capability,
                request=request,
                arguments=arguments,
            )
            self.audit.record("adapter_fallback_succeeded", capability=capability)
            return result

    def build_runtime_contract(self) -> Dict[str, Any]:
        self._refresh_components()
        catalog = self.runtime_registry.build_capability_catalog()
        capabilities = [
            {
                "capability": str(item.get("capability") or "").strip(),
                "server_names": list(item.get("server_names") or []),
            }
            for item in (catalog.get("capabilities") or [])
            if isinstance(item, dict) and str(item.get("capability") or "").strip()
        ]
        components = [
            self.runtime_registry.build_health(catalog),
            self.session_manager.build_health(),
            self.capability_router.build_health(),
            self.audit.build_health(),
        ]
        unhealthy = [item for item in components if item.get("status") in {"unavailable", "unhealthy"}]
        degraded = [item for item in components if item.get("status") == "degraded"]
        return {
            "contract_version": "phase-b-mcp-runtime-v1",
            "overall_status": "unavailable" if unhealthy else ("degraded" if degraded else "healthy"),
            "total_servers": int(catalog.get("total_servers") or 0),
            "enabled_servers": int(catalog.get("enabled_servers") or 0),
            "capability_count": len(capabilities),
            "capabilities": sorted(capabilities, key=lambda item: item["capability"]),
            "components": components,
            "recent_audit": self.audit.list_records(limit=20),
        }

    def _refresh_components(self) -> None:
        self.runtime_registry.registry_service = self.registry_service
        self.session_manager.session_service = self.session_service
        self.capability_router.adapter_service = self.adapter_service

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
