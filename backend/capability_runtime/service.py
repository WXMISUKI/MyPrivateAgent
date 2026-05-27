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
        health = {
            "capability_id": capability.capability_id,
            "kind": capability.kind,
            "provider": capability.provider,
            "transport": capability.transport,
            "status": contract.get("status") or "unknown",
            "reason": contract.get("reason") or "",
        }
        if contract.get("error"):
            health["error"] = contract["error"]
        return health

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
            if "result" in result and "capability_id" in result:
                return result
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
        health = self._resolve_health(capability)
        contract = capability.to_contract(
            status=str(health.get("status") or "unknown"),
            reason=str(health.get("reason") or ""),
        )
        if health.get("error"):
            contract["error"] = health["error"]
        return contract

    def _resolve_status(self, capability: CapabilityDefinition) -> tuple[str, str]:
        health = self._resolve_health(capability)
        return str(health.get("status") or "unknown"), str(health.get("reason") or "")

    def _resolve_health(self, capability: CapabilityDefinition) -> dict[str, Any]:
        if capability.health_checker is not None:
            health = capability.health_checker()
            if isinstance(health, dict):
                return health
        if capability.metadata.get("runtime") != "voice_runtime":
            return {"status": "unknown", "reason": ""}
        try:
            from voice_runtime.service import get_voice_runtime_service
        except ModuleNotFoundError:
            from backend.voice_runtime.service import get_voice_runtime_service
        voice_capabilities = get_voice_runtime_service().get_capabilities()
        key = "tts" if capability.kind == "tts" else "asr"
        provider_status = voice_capabilities.get(key) or {}
        return {
            "status": str(provider_status.get("status") or "unknown"),
            "reason": str(provider_status.get("reason") or ""),
        }

    def get_provider_heartbeat(self) -> dict[str, Any]:
        providers: dict[str, dict[str, Any]] = {}
        for capability in self.registry.list():
            base_url = str(capability.metadata.get("provider_base_url") or "").strip()
            provider_key = base_url or "local"
            provider = providers.setdefault(
                provider_key,
                {
                    "provider_id": capability.metadata.get("external_provider") or capability.provider,
                    "base_url": base_url,
                    "transport": capability.transport,
                    "status": "unknown",
                    "reason": "",
                    "capabilities": [],
                },
            )
            provider["capabilities"].append(self.get_capability_health(capability.capability_id))
            if base_url and provider["status"] == "unknown":
                provider.update(self._probe_provider_heartbeat(capability))
        return {
            "contract_version": CONTRACT_VERSION,
            "providers": list(providers.values()),
        }

    def _probe_provider_heartbeat(self, capability: CapabilityDefinition) -> dict[str, Any]:
        from .clients.http_client import CapabilityProviderError, HttpCapabilityClient

        base_url = str(capability.metadata.get("provider_base_url") or "").strip()
        heartbeat_path = str(capability.metadata.get("provider_heartbeat_path") or "/health")
        if not base_url:
            return {"status": "unknown", "reason": "No provider base URL configured."}
        if capability.heartbeat_checker is not None:
            data = capability.heartbeat_checker()
            if data.get("error"):
                return data
            return {
                "status": str(data.get("status") or "unknown"),
                "reason": str(data.get("message") or data.get("reason") or ""),
                "raw": data,
            }
        try:
            data = HttpCapabilityClient(base_url=base_url).get_json(heartbeat_path)
        except CapabilityProviderError as exc:
            return {
                "status": "unreachable",
                "reason": exc.message,
                "error": exc.to_payload(),
            }
        return {
            "status": str(data.get("status") or "unknown"),
            "reason": str(data.get("message") or ""),
            "raw": data,
        }


def get_capability_runtime_service() -> CapabilityRuntimeService:
    return CapabilityRuntimeService()
