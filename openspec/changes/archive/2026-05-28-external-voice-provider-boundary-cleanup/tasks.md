## 1. Specs

- [x] 1.1 Add spec deltas clarifying external voice provider first and legacy local fallback boundaries.

## 2. Runtime Metadata Cleanup

- [x] 2.1 Update local voice capability provider metadata/docstrings to mark `backend/voice_runtime/` as legacy local fallback.
- [x] 2.2 Update local voice runtime service/router messages to point normal development to `unifiedTTSandASR` and capability runtime.

## 3. Documentation Cleanup

- [x] 3.1 Update capability runtime docs to say external `unifiedTTSandASR` is recommended and `/api/voice/*` is compatibility.
- [x] 3.2 Update voice runtime docs and docs index to mark the module as legacy local fallback.

## 4. Validation

- [x] 4.1 Run focused backend tests for capability runtime and legacy voice router.
- [x] 4.2 Run `cmd /c openspec validate external-voice-provider-boundary-cleanup --strict` and `cmd /c openspec validate --specs --strict`.
