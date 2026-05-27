# Design: Unified Capability Runtime Registry

## Architecture
The new `capability_runtime` layer sits above provider-specific modules.

```text
Frontend / Agent / Domain Agent
          |
          v
  /api/capabilities/*
          |
          v
 CapabilityRuntimeService
          |
          v
 CapabilityRegistry
   | local       | http         | mcp
   v             v              v
 voice_runtime  external svc    MCP server
```

## Capability Contract
Each capability has:
- `capability_id`: stable id, for example `voice.tts.edge`.
- `kind`: `asr`, `tts`, `ocr`, `multimodal`, `video`, or future kind.
- `transport`: `local`, `http`, `websocket`, or `mcp`.
- `provider`: provider id such as `edge_tts` or `vosk_server`.
- `status`: `disabled`, `ready`, `missing_dependency`, `unconfigured`, `unsupported`, or `error`.
- `input_schema` and `output_schema`: lightweight JSON-schema-like metadata.
- `endpoint`: optional provider-specific or external endpoint.

## v1 Providers
This slice registers existing voice runtime capabilities:
- `voice.tts.edge`: local bridge to `VoiceRuntimeService.synthesize_speech_async`.
- `voice.asr.vosk`: local bridge to `VoiceRuntimeService.transcribe_audio_async`.

Provider-specific `/api/voice/*` endpoints stay available for compatibility. New consumers should prefer `/api/capabilities/*`.

## Invocation
`POST /api/capabilities/{capability_id}/invoke` is for short synchronous operations. It returns:

```json
{
  "ok": true,
  "capability_id": "voice.tts.edge",
  "provider": "edge_tts",
  "result": { "...": "..." }
}
```

Binary results are represented as base64 in v1 to keep the contract simple. Long-running jobs and artifact URLs are explicitly left for the next slice.

## Future External Services
External services should be registered through the same contract with `transport=http` or `transport=mcp`. The main runtime owns auth, policy, audit, and invocation envelope; the external service owns model dependencies, Python version, GPU/CUDA, FFmpeg, and model files.
