"""Persistent MCP server registry for the reusable agent framework demo."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_MCP_REGISTRY_PATH = Path(__file__).resolve().parents[2] / "backend" / "data" / "mcp_servers.json"
VALID_MCP_TRANSPORTS = {"stdio", "http"}


class McpRegistryService:
    """Manage MCP server configuration records with lightweight JSON persistence."""

    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_path = Path(registry_path or DEFAULT_MCP_REGISTRY_PATH)

    def list_servers(self) -> List[dict]:
        return sorted(self._load_registry(), key=lambda item: item["name"])

    def get_server(self, name: str) -> Optional[dict]:
        normalized_name = self._normalize_name(name)
        for item in self._load_registry():
            if item["name"] == normalized_name:
                return item
        return None

    def upsert_server(self, payload: Dict[str, Any]) -> dict:
        normalized = self._normalize_server_payload(payload)
        registry = self._load_registry()

        updated = False
        for index, item in enumerate(registry):
            if item["name"] == normalized["name"]:
                registry[index] = normalized
                updated = True
                break

        if not updated:
            registry.append(normalized)

        self._write_registry(registry)
        return normalized

    def update_server(self, name: str, updates: Dict[str, Any]) -> dict:
        existing = self.get_server(name)
        if existing is None:
            raise ValueError("MCP server 不存在")

        merged = dict(existing)
        for key, value in updates.items():
            if value is not None:
                merged[key] = value

        # 保证更新时仍沿用原 name，避免通过 patch 改主键
        merged["name"] = existing["name"]
        return self.upsert_server(merged)

    def delete_server(self, name: str) -> bool:
        normalized_name = self._normalize_name(name)
        registry = self._load_registry()
        filtered = [item for item in registry if item["name"] != normalized_name]
        if len(filtered) == len(registry):
            return False
        self._write_registry(filtered)
        return True

    def set_enabled(self, name: str, enabled: bool) -> dict:
        return self.update_server(name, {"enabled": bool(enabled)})

    def build_capability_catalog(self) -> dict:
        servers = self.list_servers()
        capability_map: dict[str, list[str]] = defaultdict(list)

        for server in servers:
            for capability in server.get("capabilities", []):
                capability_map[capability].append(server["name"])

        return {
            "total_servers": len(servers),
            "enabled_servers": sum(1 for server in servers if server.get("enabled")),
            "capabilities": [
                {
                    "capability": capability,
                    "server_names": sorted(server_names),
                }
                for capability, server_names in sorted(capability_map.items())
            ],
        }

    def resolve_servers_for_capability(self, capability: str) -> List[dict]:
        normalized_capability = self._normalize_text(capability)
        return [
            server
            for server in self.list_servers()
            if server.get("enabled") and normalized_capability in server.get("capabilities", [])
        ]

    def _load_registry(self) -> List[dict]:
        if not self.registry_path.exists():
            return []

        data = json.loads(self.registry_path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("MCP registry 文件格式无效")
        return [self._normalize_server_payload(item) for item in data]

    def _write_registry(self, registry: List[dict]) -> None:
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.registry_path.write_text(
            json.dumps(registry, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _normalize_server_payload(self, payload: Dict[str, Any]) -> dict:
        name = self._normalize_name(payload.get("name"))
        display_name = self._normalize_text(payload.get("display_name"))
        transport = self._normalize_transport(payload.get("transport") or "stdio")
        command = self._optional_text(payload.get("command"))
        url = self._optional_text(payload.get("url"))

        if not display_name:
            raise ValueError("display_name 不能为空")

        if transport == "stdio" and not command:
            raise ValueError("stdio 类型的 MCP server 必须配置 command")
        if transport == "http" and not url:
            raise ValueError("http 类型的 MCP server 必须配置 url")

        return {
            "name": name,
            "display_name": display_name,
            "transport": transport,
            "command": command,
            "args": [str(item).strip() for item in (payload.get("args") or []) if str(item).strip()],
            "url": url,
            "enabled": bool(payload.get("enabled", True)),
            "description": self._optional_text(payload.get("description")),
            "capabilities": self._normalize_text_list(payload.get("capabilities")),
            "tags": self._normalize_text_list(payload.get("tags")),
            "metadata": dict(payload.get("metadata") or {}),
            "status": "enabled" if bool(payload.get("enabled", True)) else "disabled",
        }

    def _normalize_name(self, value: Any) -> str:
        normalized = self._normalize_text(value).lower().replace(" ", "-")
        if not normalized:
            raise ValueError("name 不能为空")
        return normalized

    def _normalize_transport(self, value: Any) -> str:
        normalized = self._normalize_text(value).lower()
        if normalized not in VALID_MCP_TRANSPORTS:
            raise ValueError("transport 无效")
        return normalized

    def _normalize_text(self, value: Any) -> str:
        return str(value or "").strip()

    def _optional_text(self, value: Any) -> Optional[str]:
        normalized = self._normalize_text(value)
        return normalized or None

    def _normalize_text_list(self, values: Any) -> List[str]:
        normalized_values = []
        for value in values or []:
            text = self._normalize_text(value)
            if text:
                normalized_values.append(text)
        return sorted(dict.fromkeys(normalized_values))


_mcp_registry_service: Optional[McpRegistryService] = None


def get_mcp_registry_service() -> McpRegistryService:
    global _mcp_registry_service
    if _mcp_registry_service is None:
        _mcp_registry_service = McpRegistryService()
    return _mcp_registry_service
