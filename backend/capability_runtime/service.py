"""Service facade for capability discovery, health, and invocation."""

from __future__ import annotations

from typing import Any

from .contracts import CONTRACT_VERSION, CapabilityDefinition
from .registry import CapabilityRegistry, get_default_capability_registry


class CapabilityRuntimeService:
    def __init__(self, registry: CapabilityRegistry | None = None):
        self.registry = registry or get_default_capability_registry()

    def list_capabilities(self) -> dict[str, Any]:
        return {
            "contract_version": CONTRACT_VERSION,
            "capabilities": [
                self._capability_contract(capability)
                for capability in self.registry.list()
            ],
        }

    def get_capability(self, capability_id: str) -> dict[str, Any]:
        return self._capability_contract(self.registry.get(capability_id))

    def get_capability_health(self, capability_id: str) -> dict[str, Any]:
        capability = self.registry.get(capability_id)
        contract = self._capability_contract(capability)
        return {
            "capability_id": capability.capability_id,
            "kind": capability.kind,
            "provider": capability.provider,
            "transport": capability.transport,
            "status": contract.get("status") or "unknown",
            "reason": contract.get("reason") or "",
        }

    def invoke(self, capability_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        capability = self.registry.get(capability_id)
        if capability.invoker is None:
            return {
                "ok": False,
                "capability_id": capability.capability_id,
                "provider": capability.provider,
                "error": {
                    "code": "CAPABILITY_INVOKER_UNAVAILABLE",
                    "message": "Capability does not expose a local invoker.",
                },
            }
        result = capability.invoker(payload)
        if result.get("ok"):
            return {
                "ok": True,
                "capability_id": capability.capability_id,
                "provider": result.get("provider") or capability.provider,
                "result": {
                    key: value
                    for key, value in result.items()
                    if key not in {"ok", "provider"}
                },
            }
        return {
            "ok": False,
            "capability_id": capability.capability_id,
            "provider": capability.provider,
            "error": result.get("error") or {
                "code": "CAPABILITY_INVOCATION_FAILED",
                "message": "Capability invocation failed.",
            },
        }

    def _capability_contract(self, capability: CapabilityDefinition) -> dict[str, Any]:
        status, reason = self._resolve_status(capability)
        return capability.to_contract(status=status, reason=reason)

    def _resolve_status(self, capability: CapabilityDefinition) -> tuple[str, str]:
        if capability.metadata.get("runtime") != "voice_runtime":
            return "unknown", ""
        try:
            from voice_runtime.service import get_voice_runtime_service
        except ModuleNotFoundError:
            from backend.voice_runtime.service import get_voice_runtime_service
        voice_capabilities = get_voice_runtime_service().get_capabilities()
        key = "tts" if capability.kind == "tts" else "asr"
        provider_status = voice_capabilities.get(key) or {}
        return str(provider_status.get("status") or "unknown"), str(provider_status.get("reason") or "")


def get_capability_runtime_service() -> CapabilityRuntimeService:
    return CapabilityRuntimeService()
