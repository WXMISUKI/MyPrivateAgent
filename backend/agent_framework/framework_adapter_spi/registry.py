"""In-memory registry for external framework adapter declarations."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from .base import AgentFrameworkAdapter


class AgentFrameworkAdapterRegistry:
    """In-memory registry for external framework adapter declarations."""

    def __init__(self, adapters: Optional[Iterable[AgentFrameworkAdapter]] = None):
        self._adapters: Dict[str, AgentFrameworkAdapter] = {}
        for adapter in adapters or []:
            self.register(adapter)

    def register(self, adapter: AgentFrameworkAdapter) -> None:
        adapter_id = str(getattr(adapter, "adapter_id", "") or "").strip()
        if not adapter_id:
            raise ValueError("adapter_id is required")
        self._adapters[adapter_id] = adapter

    def list_adapters(self) -> List[AgentFrameworkAdapter]:
        return [self._adapters[key] for key in sorted(self._adapters)]

    def build_health_entries(self) -> List[Dict[str, Any]]:
        entries: List[Dict[str, Any]] = []
        for adapter in self.list_adapters():
            try:
                entries.append(adapter.health_check().to_dict())
            except Exception as exc:
                entries.append({
                    "adapter_id": getattr(adapter, "adapter_id", "unknown_adapter"),
                    "display_name": getattr(adapter, "framework_name", "Unknown Adapter"),
                    "framework_name": getattr(adapter, "framework_name", "unknown"),
                    "adapter_type": "agent_framework",
                    "status": "unavailable",
                    "detail": str(exc),
                    "supported_run_kinds": list(getattr(adapter, "supported_run_kinds", ()) or []),
                    "capability_requirements": list(getattr(adapter, "capability_requirements", ()) or []),
                    "package_installed": False,
                    "runtime_enabled": False,
                    "execution_mode": "error",
                    "required_env": [],
                    "execution_block_reason": str(exc),
                    "configuration_status": "error",
                    "missing_env": [],
                    "missing_packages": [],
                    "required_packages": [],
                })
        return entries

    def build_runtime_contract(self) -> Dict[str, Any]:
        adapters = []
        for adapter in self.list_adapters():
            health = adapter.health_check().to_dict()
            adapters.append({
                "adapter_id": health["adapter_id"],
                "framework_name": health["framework_name"],
                "status": health["status"],
                "supported_run_kinds": health["supported_run_kinds"],
                "capability_requirements": health["capability_requirements"],
            })
        return {
            "contract_version": "phase-b-framework-adapter-spi-v1",
            "adapter_count": len(adapters),
            "adapters": adapters,
        }
