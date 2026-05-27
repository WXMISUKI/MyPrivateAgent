"""HTTP provider definitions for the standalone unifiedTTSandASR service."""

from __future__ import annotations

from typing import Any

from ..clients.http_client import CapabilityProviderError, HttpCapabilityClient
from ..contracts import CapabilityDefinition


def build_http_voice_capabilities(
    *,
    base_url: str,
    timeout_seconds: float = 5.0,
    client: HttpCapabilityClient | None = None,
) -> list[CapabilityDefinition]:
    http_client = client or HttpCapabilityClient(base_url=base_url, timeout_seconds=timeout_seconds)
    return [
        CapabilityDefinition(
            capability_id="voice.tts.edge",
            kind="tts",
            transport="http",
            provider="edge_tts",
            title="Edge TTS",
            description="Synthesize text through the external unifiedTTSandASR service.",
            endpoint="/api/capabilities/voice.tts.edge/invoke",
            input_schema={
                "type": "object",
                "required": ["text"],
                "properties": {
                    "text": {"type": "string"},
                    "voice": {"type": "string"},
                    "rate": {"type": "string"},
                    "volume": {"type": "string"},
                    "pitch": {"type": "string"},
                },
            },
            output_schema={
                "type": "object",
                "properties": {
                    "media_type": {"type": "string"},
                    "audio_base64": {"type": "string"},
                },
            },
            metadata=_metadata(base_url, "/api/capabilities/voice.tts.edge/health", "/api/capabilities/voice.tts.edge/invoke"),
            invoker=_invoke(http_client, "/api/capabilities/voice.tts.edge/invoke"),
            health_checker=_health(http_client, "/api/capabilities/voice.tts.edge/health"),
            heartbeat_checker=_provider_heartbeat(http_client),
        ),
        CapabilityDefinition(
            capability_id="voice.asr.vosk",
            kind="asr",
            transport="http",
            provider="vosk_server",
            title="Vosk ASR",
            description="Transcribe audio through the external unifiedTTSandASR service.",
            endpoint="/api/capabilities/voice.asr.vosk/invoke",
            input_schema={
                "type": "object",
                "required": ["audio_base64"],
                "properties": {
                    "audio_base64": {"type": "string"},
                    "media_type": {"type": "string"},
                    "language": {"type": "string"},
                },
            },
            output_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "language": {"type": "string"},
                    "partial": {"type": "boolean"},
                },
            },
            metadata=_metadata(
                base_url,
                "/api/capabilities/voice.asr.vosk/health",
                "/api/capabilities/voice.asr.vosk/invoke",
                stream_path="/api/voice/asr/ws",
            ),
            invoker=_invoke(http_client, "/api/capabilities/voice.asr.vosk/invoke"),
            health_checker=_health(http_client, "/api/capabilities/voice.asr.vosk/health"),
            heartbeat_checker=_provider_heartbeat(http_client),
        ),
    ]


def _metadata(base_url: str, health_path: str, invoke_path: str, *, stream_path: str | None = None) -> dict[str, Any]:
    metadata = {
        "provider_base_url": base_url.rstrip("/"),
        "provider_health_path": health_path,
        "provider_invoke_path": invoke_path,
        "provider_heartbeat_path": "/health",
        "external_provider": "unifiedTTSandASR",
    }
    if stream_path:
        metadata["provider_stream_path"] = stream_path
    return metadata


def _health(client: HttpCapabilityClient, path: str):
    def check() -> dict[str, Any]:
        try:
            return client.get_json(path)
        except CapabilityProviderError as exc:
            return {
                "status": "unreachable",
                "reason": exc.message,
                "error": exc.to_payload(),
            }

    return check


def _provider_heartbeat(client: HttpCapabilityClient):
    def check() -> dict[str, Any]:
        try:
            return client.get_json("/health")
        except CapabilityProviderError as exc:
            return {
                "status": "unreachable",
                "reason": exc.message,
                "error": exc.to_payload(),
            }

    return check


def _invoke(client: HttpCapabilityClient, path: str):
    def invoke(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            return client.post_json(path, payload)
        except CapabilityProviderError as exc:
            return {
                "ok": False,
                "error": exc.to_payload(),
            }

    return invoke
