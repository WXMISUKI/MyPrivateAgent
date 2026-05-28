# Change: external-voice-provider-boundary-cleanup

## Why

Voice ASR/TTS execution has already moved toward the standalone `unifiedTTSandASR` provider through `capability_runtime`, but the core repository still describes `backend/voice_runtime/` as if it were the recommended voice runtime. This blurs the boundary between the Agent Runtime Control Plane and optional local provider code.

## What Changes

- Clarify that `unifiedTTSandASR` is the recommended external voice provider for production and normal development.
- Reclassify `backend/voice_runtime/` and `/api/voice/*` as legacy local fallback / compatibility surfaces.
- Update local voice provider contracts, error messages, and docs so they do not instruct developers to install voice dependencies into the main backend as the normal path.
- Keep compatibility APIs and tests intact; do not delete `backend/voice_runtime/` in this slice.

## 收口对象

- `backend/capability_runtime/providers/voice_provider.py`
- `backend/voice_runtime/service.py`
- `backend/routers/voice.py`
- `docs/guides/capability_runtime_registry.md`
- `docs/guides/voice_runtime_module.md`
- `docs/README.md`
- `openspec/specs/unified-capability-runtime/spec.md`
- `openspec/specs/unified-voice-runtime/spec.md`

## 非目标

- Do not delete `/api/voice/*` compatibility endpoints.
- Do not remove existing tests that prove legacy local fallback stays fail-open/disabled.
- Do not add voice dependencies to the main backend.
- Do not change `/api/chat` or the main microphone capability stream behavior.

## Impact

- Runtime behavior remains compatible.
- Documentation and capability metadata now align with the external-provider-first architecture.
- Future work can later remove or further quarantine legacy local voice code through a separate breaking-change proposal.
