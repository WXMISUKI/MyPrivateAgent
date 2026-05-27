# Change: external-voice-capability-http-provider

## Why
The ASR/TTS provider has been moved into `D:\AI\AIcode\unifiedTTSandASR`. MyPrivateAgent should stop treating voice as an in-process local provider when an external voice service is configured. It also needs a live discovery/heartbeat surface so operators and frontends can see which capabilities are currently callable.

## What Changes
- Add an HTTP capability client for external provider services that expose `/api/capabilities/*`.
- Add environment-backed registration for the external voice capability provider.
- Let `voice.tts.edge` and `voice.asr.vosk` be registered as HTTP capabilities when the external provider is enabled.
- Add a provider heartbeat endpoint for live provider/service/capability status checks.
- Keep existing local voice provider fallback and existing `/api/voice/*` compatibility endpoints unchanged.

## 收口对象
- `backend/capability_runtime/clients/http_client.py`
- HTTP voice provider registration under `backend/capability_runtime/providers/`
- `backend/capability_runtime/service.py` live health and heartbeat aggregation
- `backend/routers/capabilities.py` heartbeat endpoint
- docs for configuring `unifiedTTSandASR`

## 非目标
- Do not remove local `voice_runtime`.
- Do not implement long-running job/artifact storage.
- Do not proxy WebSocket ASR through MyPrivateAgent in this slice.
- Do not add OCR/video providers yet.
