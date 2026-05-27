# Change: capability-provider-diagnostics-panel

## Why
MyPrivateAgent can discover and invoke external ASR/TTS capabilities, but operators currently need to test them through raw API calls or the standalone `unifiedTTSandASR` debug page. The control plane should provide its own provider-neutral test endpoint and a lightweight frontend diagnostics panel.

## What Changes
- Add `POST /api/capabilities/{capability_id}/test` as the backend source of truth for active capability tests.
- Implement TTS default testing through capability invocation and result summarization.
- Implement ASR readiness testing when no audio payload is supplied, with optional real invoke when audio is provided.
- Add a Vue capability provider diagnostics panel that shows capability registry, heartbeat, test status, and TTS playback.
- Keep full WebSocket recording diagnostics in `unifiedTTSandASR/static/index.html` for this slice.

## 收口对象
- Capability runtime test service behavior.
- Capability router test endpoint.
- Settings UI diagnostics panel.
- Focused backend/frontend tests and docs.

## 非目标
- Do not implement browser PCM recording or ASR WebSocket streaming in MyPrivateAgent.
- Do not replace `unifiedTTSandASR`'s debug UI.
- Do not add persistent monitoring or historical health storage.
