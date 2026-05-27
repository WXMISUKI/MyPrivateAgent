"""Voice runtime capability and execution service."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec
from typing import Any

from .contracts import CONTRACT_VERSION, VoiceAudioResult, VoiceRuntimeError, VoiceTranscriptResult


@dataclass(frozen=True)
class VoiceRuntimeSettings:
    enabled: bool = False
    asr_provider: str = "vosk_server"
    tts_provider: str = "edge_tts"
    vosk_mode: str = "server"
    vosk_server_url: str = "ws://127.0.0.1:2700"
    vosk_language: str = "zh-cn"
    vosk_sample_rate: int = 16000
    edge_tts_default_voice: str = "zh-CN-XiaoxiaoNeural"
    edge_tts_rate: str = "+0%"
    edge_tts_volume: str = "+0%"
    edge_tts_pitch: str = "+0Hz"

    @classmethod
    def from_config(cls) -> "VoiceRuntimeSettings":
        try:
            from config import (
                EDGE_TTS_DEFAULT_VOICE,
                EDGE_TTS_PITCH,
                EDGE_TTS_RATE,
                EDGE_TTS_VOLUME,
                ENABLE_VOICE_RUNTIME,
                VOICE_ASR_PROVIDER,
                VOICE_TTS_PROVIDER,
                VOSK_LANGUAGE,
                VOSK_MODE,
                VOSK_SAMPLE_RATE,
                VOSK_SERVER_URL,
            )
        except ModuleNotFoundError:
            from backend.config import (
                EDGE_TTS_DEFAULT_VOICE,
                EDGE_TTS_PITCH,
                EDGE_TTS_RATE,
                EDGE_TTS_VOLUME,
                ENABLE_VOICE_RUNTIME,
                VOICE_ASR_PROVIDER,
                VOICE_TTS_PROVIDER,
                VOSK_LANGUAGE,
                VOSK_MODE,
                VOSK_SAMPLE_RATE,
                VOSK_SERVER_URL,
            )
        return cls(
            enabled=bool(ENABLE_VOICE_RUNTIME),
            asr_provider=VOICE_ASR_PROVIDER,
            tts_provider=VOICE_TTS_PROVIDER,
            vosk_mode=VOSK_MODE,
            vosk_server_url=VOSK_SERVER_URL,
            vosk_language=VOSK_LANGUAGE,
            vosk_sample_rate=VOSK_SAMPLE_RATE,
            edge_tts_default_voice=EDGE_TTS_DEFAULT_VOICE,
            edge_tts_rate=EDGE_TTS_RATE,
            edge_tts_volume=EDGE_TTS_VOLUME,
            edge_tts_pitch=EDGE_TTS_PITCH,
        )


class VoiceRuntimeService:
    """Facade for optional voice providers."""

    def __init__(self, settings: VoiceRuntimeSettings | None = None):
        self.settings = settings or VoiceRuntimeSettings.from_config()

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "contract_version": CONTRACT_VERSION,
            "enabled": self.settings.enabled,
            "asr": self._build_asr_capability(),
            "tts": self._build_tts_capability(),
            "endpoints": {
                "capabilities": "/api/voice/capabilities",
                "asr": "/api/voice/asr",
                "asr_stream": "/api/voice/asr/ws",
                "tts": "/api/voice/tts",
            },
        }

    def transcribe_audio(
        self,
        audio: bytes,
        *,
        media_type: str = "application/octet-stream",
        language: str | None = None,
    ) -> dict[str, Any]:
        result = self._transcribe_audio_result(
            audio,
            media_type=media_type,
            language=language,
        )
        return result.to_payload()

    async def transcribe_audio_async(
        self,
        audio: bytes,
        *,
        media_type: str = "application/octet-stream",
        language: str | None = None,
    ) -> VoiceTranscriptResult:
        preliminary = self._transcribe_audio_result(
            audio,
            media_type=media_type,
            language=language,
            execute_provider=False,
        )
        if not preliminary.ok:
            return preliminary
        try:
            from .providers.vosk_server_provider import VoskServerProvider

            provider = VoskServerProvider(self.settings)
            return await provider.transcribe(audio, language=language)
        except Exception as exc:
            return self._provider_unavailable_transcript(
                "VOICE_PROVIDER_ERROR",
                f"Vosk ASR transcription failed: {exc}",
                language=language,
            )

    async def synthesize_speech_async(self, payload: dict[str, Any]) -> VoiceAudioResult:
        disabled_error = self._disabled_error(self.settings.tts_provider)
        if disabled_error:
            return VoiceAudioResult(
                content=None,
                media_type="application/json",
                provider=self.settings.tts_provider,
                error=disabled_error,
            )
        if self.settings.tts_provider != "edge_tts":
            return self._provider_unavailable_audio(
                "VOICE_PROVIDER_UNAVAILABLE",
                f"Unsupported TTS provider: {self.settings.tts_provider}",
            )
        if find_spec("edge_tts") is None:
            return self._provider_unavailable_audio(
                "VOICE_PROVIDER_UNAVAILABLE",
                "edge-tts is not installed. Install backend/voice_runtime/requirements-voice.txt to enable TTS.",
            )
        try:
            from .providers.edge_tts_provider import EdgeTtsProvider

            provider = EdgeTtsProvider(self.settings)
            return await provider.synthesize(payload)
        except Exception as exc:
            return self._provider_unavailable_audio(
                "VOICE_PROVIDER_ERROR",
                f"Edge-TTS synthesis failed: {exc}",
            )

    def synthesize_speech(self, payload: dict[str, Any]) -> dict[str, Any]:
        disabled_error = self._disabled_error(self.settings.tts_provider)
        if disabled_error:
            return VoiceAudioResult(
                content=None,
                media_type="application/json",
                provider=self.settings.tts_provider,
                error=disabled_error,
            ).to_payload()
        if self.settings.tts_provider != "edge_tts" or find_spec("edge_tts") is None:
            return self._provider_unavailable_audio(
                "VOICE_PROVIDER_UNAVAILABLE",
                "Configured TTS provider is not available.",
            ).to_payload()
        return {
            "ok": False,
            "error": VoiceRuntimeError(
                code="VOICE_PROVIDER_UNAVAILABLE",
                message="Use synthesize_speech_async for enabled TTS execution.",
                provider=self.settings.tts_provider,
            ).to_payload(),
        }

    def _transcribe_audio_result(
        self,
        audio: bytes,
        *,
        media_type: str,
        language: str | None,
        execute_provider: bool = True,
    ) -> VoiceTranscriptResult:
        disabled_error = self._disabled_error(self.settings.asr_provider)
        if disabled_error:
            return VoiceTranscriptResult(
                text="",
                provider=self.settings.asr_provider,
                language=language or self.settings.vosk_language,
                error=disabled_error,
            )
        if self.settings.asr_provider != "vosk_server":
            return self._provider_unavailable_transcript(
                "VOICE_PROVIDER_UNAVAILABLE",
                f"Unsupported ASR provider: {self.settings.asr_provider}",
                language=language,
            )
        if not self.settings.vosk_server_url.strip():
            return self._provider_unavailable_transcript(
                "VOICE_PROVIDER_UNAVAILABLE",
                "VOSK_SERVER_URL is required for vosk_server ASR.",
                language=language,
            )
        if find_spec("websockets") is None:
            return self._provider_unavailable_transcript(
                "VOICE_PROVIDER_UNAVAILABLE",
                "websockets is not installed. Install backend/voice_runtime/requirements-voice.txt to enable Vosk ASR.",
                language=language,
            )
        if not audio:
            return self._provider_unavailable_transcript(
                "VOICE_UNSUPPORTED_MEDIA_TYPE",
                "Audio payload is empty.",
                language=language,
            )
        if execute_provider:
            return self._provider_unavailable_transcript(
                "VOICE_PROVIDER_UNAVAILABLE",
                "Use transcribe_audio_async for enabled Vosk ASR execution.",
                language=language,
            )
        return VoiceTranscriptResult(
            text="",
            provider=self.settings.asr_provider,
            language=language or self.settings.vosk_language,
        )

    def _build_asr_capability(self) -> dict[str, Any]:
        if not self.settings.enabled:
            return {
                "provider": self.settings.asr_provider,
                "mode": self.settings.vosk_mode,
                "language": self.settings.vosk_language,
                "status": "disabled",
                "realtime_supported": self.settings.asr_provider == "vosk_server",
                "reason": "ENABLE_VOICE_RUNTIME=false",
            }
        if self.settings.asr_provider != "vosk_server":
            return {
                "provider": self.settings.asr_provider,
                "mode": "unsupported",
                "language": self.settings.vosk_language,
                "status": "unsupported",
                "realtime_supported": False,
                "reason": "Only vosk_server is supported in v1.",
            }
        if not self.settings.vosk_server_url.strip():
            return {
                "provider": "vosk_server",
                "mode": self.settings.vosk_mode,
                "language": self.settings.vosk_language,
                "status": "unconfigured",
                "realtime_supported": True,
                "reason": "VOSK_SERVER_URL is required.",
            }
        if find_spec("websockets") is None:
            return {
                "provider": "vosk_server",
                "mode": self.settings.vosk_mode,
                "language": self.settings.vosk_language,
                "status": "missing_dependency",
                "realtime_supported": True,
                "reason": "Python package 'websockets' is not installed.",
            }
        return {
            "provider": "vosk_server",
            "mode": self.settings.vosk_mode,
            "language": self.settings.vosk_language,
            "status": "ready",
            "realtime_supported": True,
            "server_url": self.settings.vosk_server_url,
            "sample_rate": self.settings.vosk_sample_rate,
        }

    def _build_tts_capability(self) -> dict[str, Any]:
        if not self.settings.enabled:
            return {
                "provider": self.settings.tts_provider,
                "status": "disabled",
                "default_voice": self.settings.edge_tts_default_voice,
                "reason": "ENABLE_VOICE_RUNTIME=false",
            }
        if self.settings.tts_provider != "edge_tts":
            return {
                "provider": self.settings.tts_provider,
                "status": "unsupported",
                "default_voice": self.settings.edge_tts_default_voice,
                "reason": "Only edge_tts is supported in v1.",
            }
        if find_spec("edge_tts") is None:
            return {
                "provider": "edge_tts",
                "status": "missing_dependency",
                "default_voice": self.settings.edge_tts_default_voice,
                "reason": "Python package 'edge-tts' is not installed.",
            }
        return {
            "provider": "edge_tts",
            "status": "ready",
            "default_voice": self.settings.edge_tts_default_voice,
            "rate": self.settings.edge_tts_rate,
            "volume": self.settings.edge_tts_volume,
            "pitch": self.settings.edge_tts_pitch,
        }

    def _disabled_error(self, provider: str) -> VoiceRuntimeError | None:
        if self.settings.enabled:
            return None
        return VoiceRuntimeError(
            code="VOICE_RUNTIME_DISABLED",
            message="Voice runtime is disabled. Set ENABLE_VOICE_RUNTIME=true to enable it.",
            provider=provider,
        )

    def _provider_unavailable_audio(self, code: str, message: str) -> VoiceAudioResult:
        return VoiceAudioResult(
            content=None,
            media_type="application/json",
            provider=self.settings.tts_provider,
            error=VoiceRuntimeError(code=code, message=message, provider=self.settings.tts_provider),
        )

    def _provider_unavailable_transcript(
        self,
        code: str,
        message: str,
        *,
        language: str | None,
    ) -> VoiceTranscriptResult:
        return VoiceTranscriptResult(
            text="",
            provider=self.settings.asr_provider,
            language=language or self.settings.vosk_language,
            error=VoiceRuntimeError(code=code, message=message, provider=self.settings.asr_provider),
        )


def get_voice_runtime_service() -> VoiceRuntimeService:
    return VoiceRuntimeService()
