"""In-memory capability registry for local and external providers."""

from __future__ import annotations

from .contracts import CapabilityDefinition
from .providers.document_vlm_http_provider import build_http_document_vlm_capabilities
from .providers.knowledge_http_provider import build_http_knowledge_capabilities
from .providers.paddleocr_layout_http_provider import build_http_layout_capabilities
from .providers.paddleocr_http_provider import build_http_paddleocr_capabilities
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
            ENABLE_KNOWLEDGE_CAPABILITY_PROVIDER,
            ENABLE_LAYOUT_CAPABILITY_PROVIDER,
            ENABLE_OCR_CAPABILITY_PROVIDER,
            ENABLE_VLM_CAPABILITY_PROVIDER,
            KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL,
            KNOWLEDGE_CAPABILITY_PROVIDER_TIMEOUT_SECONDS,
            LAYOUT_CAPABILITY_PROVIDER_BASE_URL,
            LAYOUT_CAPABILITY_PROVIDER_INVOKE_PATH,
            LAYOUT_CAPABILITY_PROVIDER_TIMEOUT_SECONDS,
            OCR_CAPABILITY_PROVIDER_BASE_URL,
            OCR_CAPABILITY_PROVIDER_TIMEOUT_SECONDS,
            VLM_CAPABILITY_PROVIDER_BASE_URL,
            VLM_CAPABILITY_PROVIDER_INVOKE_PATH,
            VLM_CAPABILITY_PROVIDER_TIMEOUT_SECONDS,
            VLM_CAPABILITY_PROVIDER_ASYNC_SUBMIT_PATH,
            VLM_CAPABILITY_PROVIDER_ASYNC_STATUS_PATH_TEMPLATE,
            VOICE_CAPABILITY_PROVIDER_BASE_URL,
            VOICE_CAPABILITY_PROVIDER_TIMEOUT_SECONDS,
        )
    except ModuleNotFoundError:
        from backend.config import (
            ENABLE_EXTERNAL_VOICE_CAPABILITY_PROVIDER,
            ENABLE_KNOWLEDGE_CAPABILITY_PROVIDER,
            ENABLE_LAYOUT_CAPABILITY_PROVIDER,
            ENABLE_OCR_CAPABILITY_PROVIDER,
            ENABLE_VLM_CAPABILITY_PROVIDER,
            KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL,
            KNOWLEDGE_CAPABILITY_PROVIDER_TIMEOUT_SECONDS,
            LAYOUT_CAPABILITY_PROVIDER_BASE_URL,
            LAYOUT_CAPABILITY_PROVIDER_INVOKE_PATH,
            LAYOUT_CAPABILITY_PROVIDER_TIMEOUT_SECONDS,
            OCR_CAPABILITY_PROVIDER_BASE_URL,
            OCR_CAPABILITY_PROVIDER_TIMEOUT_SECONDS,
            VLM_CAPABILITY_PROVIDER_BASE_URL,
            VLM_CAPABILITY_PROVIDER_INVOKE_PATH,
            VLM_CAPABILITY_PROVIDER_TIMEOUT_SECONDS,
            VLM_CAPABILITY_PROVIDER_ASYNC_SUBMIT_PATH,
            VLM_CAPABILITY_PROVIDER_ASYNC_STATUS_PATH_TEMPLATE,
            VOICE_CAPABILITY_PROVIDER_BASE_URL,
            VOICE_CAPABILITY_PROVIDER_TIMEOUT_SECONDS,
        )
    capabilities: list[CapabilityDefinition]
    if ENABLE_EXTERNAL_VOICE_CAPABILITY_PROVIDER and VOICE_CAPABILITY_PROVIDER_BASE_URL:
        capabilities = build_http_voice_capabilities(
            base_url=VOICE_CAPABILITY_PROVIDER_BASE_URL,
            timeout_seconds=VOICE_CAPABILITY_PROVIDER_TIMEOUT_SECONDS,
        )
    else:
        capabilities = build_voice_capabilities()
    if ENABLE_KNOWLEDGE_CAPABILITY_PROVIDER and KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL:
        capabilities.extend(
            build_http_knowledge_capabilities(
                base_url=KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL,
                timeout_seconds=KNOWLEDGE_CAPABILITY_PROVIDER_TIMEOUT_SECONDS,
            )
        )
    if ENABLE_OCR_CAPABILITY_PROVIDER and OCR_CAPABILITY_PROVIDER_BASE_URL:
        capabilities.extend(
            build_http_paddleocr_capabilities(
                base_url=OCR_CAPABILITY_PROVIDER_BASE_URL,
                timeout_seconds=OCR_CAPABILITY_PROVIDER_TIMEOUT_SECONDS,
            )
        )
    if ENABLE_LAYOUT_CAPABILITY_PROVIDER and LAYOUT_CAPABILITY_PROVIDER_BASE_URL:
        capabilities.extend(
            build_http_layout_capabilities(
                base_url=LAYOUT_CAPABILITY_PROVIDER_BASE_URL,
                timeout_seconds=LAYOUT_CAPABILITY_PROVIDER_TIMEOUT_SECONDS,
                invoke_path=LAYOUT_CAPABILITY_PROVIDER_INVOKE_PATH,
            )
        )
    if ENABLE_VLM_CAPABILITY_PROVIDER and VLM_CAPABILITY_PROVIDER_BASE_URL:
        capabilities.extend(
            build_http_document_vlm_capabilities(
                base_url=VLM_CAPABILITY_PROVIDER_BASE_URL,
                timeout_seconds=VLM_CAPABILITY_PROVIDER_TIMEOUT_SECONDS,
                invoke_path=VLM_CAPABILITY_PROVIDER_INVOKE_PATH,
                async_submit_path=VLM_CAPABILITY_PROVIDER_ASYNC_SUBMIT_PATH,
                async_status_path_template=VLM_CAPABILITY_PROVIDER_ASYNC_STATUS_PATH_TEMPLATE,
            )
        )
    return CapabilityRegistry(capabilities)
