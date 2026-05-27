# Design: Unified Voice Runtime

## Architecture
The voice runtime is a backend module under `backend/voice_runtime/`.

It owns:
- Provider-neutral contracts.
- Capability discovery.
- Lazy optional dependency checks.
- Provider adapters.

The FastAPI router is always importable and can be registered by the server, but runtime execution remains gated by `ENABLE_VOICE_RUNTIME`.

## Provider Strategy
### ASR
Primary v1 provider: `vosk_server`.

The service assumes Vosk can be operated as a separate process/service. This keeps model files, native dependencies, and runtime lifecycle outside the core backend package. The API contract reserves both synchronous file transcription and WebSocket streaming.

### TTS
Primary v1 provider: `edge_tts`.

The provider is lazy-imported. If `edge-tts` is not installed or the runtime is disabled, endpoints return a structured unavailable error instead of crashing import-time startup.

## Configuration
New environment variables:
- `ENABLE_VOICE_RUNTIME=false`
- `VOICE_ASR_PROVIDER=vosk_server`
- `VOICE_TTS_PROVIDER=edge_tts`
- `VOSK_MODE=server`
- `VOSK_SERVER_URL=ws://127.0.0.1:2700`
- `VOSK_LANGUAGE=zh-cn`
- `VOSK_SAMPLE_RATE=16000`
- `EDGE_TTS_DEFAULT_VOICE=zh-CN-XiaoxiaoNeural`
- `EDGE_TTS_RATE=+0%`
- `EDGE_TTS_VOLUME=+0%`
- `EDGE_TTS_PITCH=+0Hz`

## Error Model
Voice endpoints return structured errors:
- `VOICE_RUNTIME_DISABLED`
- `VOICE_PROVIDER_UNAVAILABLE`
- `VOICE_PROVIDER_ERROR`
- `VOICE_UNSUPPORTED_MEDIA_TYPE`

## Packaging Boundary
Default backend dependencies stay unchanged. Optional voice dependencies live in `backend/voice_runtime/requirements-voice.txt`.

This lets deployments choose:
- Core runtime only.
- Core runtime + Edge-TTS.
- Core runtime + external Vosk server.
- Core runtime + both providers.

## Streaming Contract
`WS /api/voice/asr/ws` accepts binary PCM chunks and forwards them to the configured Vosk WebSocket server. A text frame with `__end__` sends the Vosk EOF marker. Returned Vosk `partial` or `text` payloads are wrapped in the local `voice-runtime-v1` JSON envelope.

## Follow-up Slices
- Add visible frontend TTS playback controls.
- Add a full browser-to-backend streaming ASR UX using `MediaRecorder`/PCM conversion.
- Add provider health telemetry to Runtime Surface.
