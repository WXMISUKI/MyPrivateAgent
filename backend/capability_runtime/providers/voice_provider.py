"""Bridge existing voice runtime providers into the capability registry."""

from __future__ import annotations

import asyncio
import base64
from typing import Any

from ..contracts import CapabilityDefinition


def build_voice_capabilities() -> list[CapabilityDefinition]:
    return [
        CapabilityDefinition(
            capability_id="voice.tts.edge",
            kind="tts",
            transport="local",
            provider="edge_tts",
            title="Edge TTS",
            description="Synthesize short text into speech through the optional Edge-TTS provider.",
            endpoint="/api/voice/tts",
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
            metadata={"runtime": "voice_runtime", "result_encoding": "base64"},
            invoker=_invoke_tts,
        ),
        CapabilityDefinition(
            capability_id="voice.asr.vosk",
            kind="asr",
            transport="websocket",
            provider="vosk_server",
            title="Vosk ASR",
            description="Transcribe audio through the optional Vosk server provider.",
            endpoint="/api/voice/asr",
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
            metadata={"runtime": "voice_runtime", "input_encoding": "base64"},
            invoker=_invoke_asr,
        ),
    ]


def _get_voice_runtime_service():
    try:
        from voice_runtime.service import get_voice_runtime_service
    except ModuleNotFoundError:
        from backend.voice_runtime.service import get_voice_runtime_service
    return get_voice_runtime_service()


def _invoke_tts(payload: dict[str, Any]) -> dict[str, Any]:
    service = _get_voice_runtime_service()
    result = asyncio.run(service.synthesize_speech_async(payload))
    if not result.ok:
        return result.to_payload()
    return {
        "ok": True,
        "provider": result.provider,
        "media_type": result.media_type,
        "audio_base64": base64.b64encode(result.content or b"").decode("ascii"),
    }


def _invoke_asr(payload: dict[str, Any]) -> dict[str, Any]:
    audio_base64 = str(payload.get("audio_base64") or "")
    try:
        audio = base64.b64decode(audio_base64)
    except Exception:
        audio = b""
    service = _get_voice_runtime_service()
    result = asyncio.run(
        service.transcribe_audio_async(
            audio,
            media_type=str(payload.get("media_type") or "application/octet-stream"),
            language=payload.get("language"),
        )
    )
    return result.to_payload()
