# Change: unified-voice-runtime-vosk-edge

## Summary
Add a unified, optional Voice Runtime module that exposes ASR and TTS capabilities without forcing Vosk, Edge-TTS, model downloads, or WebSocket dependencies into the default runtime package.

## 收口对象
- Backend voice capability contract and stable API surface.
- Optional provider adapters for Vosk real-time ASR and Edge-TTS speech synthesis.
- Frontend API wrapper for future chat input/output voice UX.
- Operator documentation for enabling the module only when needed.

## Motivation
The project is an Agent Runtime Control Plane. Voice should follow the same control-plane pattern as model, tool, MCP, skill, and domain-agent capabilities: expose a stable contract, keep providers pluggable, and make heavy/runtime-specific dependencies optional.

Vosk is suitable for low-latency local ASR, especially when deployed as a separate service. Edge-TTS is suitable for low-cost speech synthesis. Neither should become a hard dependency for the core chat runtime.

## Non-goals
- Do not replace the existing browser Web Speech input shipped in `voice-input-web-speech`.
- Do not bundle Vosk model files into the repository.
- Do not require `vosk`, `edge-tts`, or `websockets` in the default `backend/requirements.txt`.
- Do not change `/api/chat` request or response shape in this slice.
- Do not add assistant auto-play UI in this slice.

## Impacted Contracts
- Backend API:
  - `GET /api/voice/capabilities`
  - `POST /api/voice/asr`
  - `POST /api/voice/tts`
  - `WS /api/voice/asr/ws`
- Frontend consumer:
  - `frontend-vue/src/api/index.js` gets a `voiceApi` wrapper.
- Docs:
  - Add voice runtime module guide.

## External References
- Vosk is used as the ASR provider shape, preferably through a separately managed server or optional Python dependency.
- Edge-TTS is used as the TTS provider shape through an optional Python dependency.
- These references inform adapter boundaries only; the project contract remains local.
