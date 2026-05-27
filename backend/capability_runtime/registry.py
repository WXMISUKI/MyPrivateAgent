"""In-memory capability registry for local and external providers."""

from __future__ import annotations

from .contracts import CapabilityDefinition
from .providers.voice_provider import build_voice_capabilities
from .providers.voice_http_provider import build_http_voice_capabilities


class CapabilityRegistry:
    def __init__(self, capabilities: list[CapabilityDefinition] | None = None):
        self._capabilities = {
            capability.capability_id: capability
            for capability in (capabilities if capabilities is not None else build_voice_capabilities())
        }

    def list(self) -> tuple[CapabilityDefinition, ...]:
        return tuple(self._capabilities.values())

    def get(self, capability_id: str) -> CapabilityDefinition:
        capability = self._capabilities.get(capability_id)
        if capability is None:
            raise LookupError(f"Capability not found: {capability_id}")
        return capability


def get_default_capability_registry() -> CapabilityRegistry:
    try:
        from config import (
            ENABLE_EXTERNAL_VOICE_CAPABILITY_PROVIDER,
            VOICE_CAPABILITY_PROVIDER_BASE_URL,
            VOICE_CAPABILITY_PROVIDER_TIMEOUT_SECONDS,
        )
    except ModuleNotFoundError:
        from backend.config import (
            ENABLE_EXTERNAL_VOICE_CAPABILITY_PROVIDER,
            VOICE_CAPABILITY_PROVIDER_BASE_URL,
            VOICE_CAPABILITY_PROVIDER_TIMEOUT_SECONDS,
        )
    if ENABLE_EXTERNAL_VOICE_CAPABILITY_PROVIDER and VOICE_CAPABILITY_PROVIDER_BASE_URL:
        return CapabilityRegistry(
            build_http_voice_capabilities(
                base_url=VOICE_CAPABILITY_PROVIDER_BASE_URL,
                timeout_seconds=VOICE_CAPABILITY_PROVIDER_TIMEOUT_SECONDS,
            )
        )
    return CapabilityRegistry()
