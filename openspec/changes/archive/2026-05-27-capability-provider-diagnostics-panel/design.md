# Design: Capability Provider Diagnostics Panel

## Backend
`CapabilityRuntimeService.test_capability(capability_id, payload)` handles active test semantics:

- TTS default: merge caller payload with a fixed short Chinese test sentence, call `invoke`, verify `result.audio_base64` and `result.media_type`, and return a compact summary.
- ASR without `audio_base64`: call `get_capability_health` and return `mode=health_only`.
- ASR with `audio_base64`: call `invoke` and summarize transcript fields.
- Unknown capability remains `CAPABILITY_NOT_FOUND`.
- Provider failures return structured errors without raising server startup errors.

## API
`POST /api/capabilities/{capability_id}/test`

Request:
```json
{
  "payload": {},
  "mode": "default"
}
```

Response:
```json
{
  "ok": true,
  "capability_id": "voice.tts.edge",
  "status": "ok",
  "latency_ms": 120,
  "result_summary": {
    "media_type": "audio/mpeg",
    "audio_base64_length": 1024
  }
}
```

## Frontend
Add `CapabilityProviderDiagnosticsPanel.vue` and mount it in Settings > Model and Provider.

The panel uses:
- `capabilityApi.list()`
- `capabilityApi.heartbeat()`
- `capabilityApi.test(capabilityId, payload)`

For TTS success, it creates an audio data URL from `result_summary.audio_base64` when present. For ASR, it supports optional PCM file upload converted to base64 before testing.

## Failure Handling
Failures render inline in the panel and keep the rest of the settings page usable.
