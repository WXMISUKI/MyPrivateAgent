## Why

`unifiedKnowledgeRAG` Phase 18 now reports the minimal MyPrivateAgent access gate as ready. MyPrivateAgent should stop waiting for more provider-side evidence and run a repository-side trial that proves the caller can discover, preflight, retrieve evidence, and inspect source binding review through the provider HTTP contract.

## What Changes

- Add a read-only MyPrivateAgent repo-side trial outcome exporter for the unified knowledge provider.
- The trial checks the minimal integration path:
  - `GET /health`
  - `GET /api/provider/manifest`
  - `GET /api/provider/preflight`
  - `POST /api/rag/retrieve`
  - `GET /api/provider/source-bindings`
- The exporter writes a compact JSON/Markdown outcome with `trial_passed`, `trial_review`, or `trial_blocked`.
- The trial supports a local provider URL and optional provider API key without storing secret values.
- The trial remains outside default chat behavior and does not create source-to-agent binding.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `unified-knowledge-capability-runtime`: Add repo-side trial outcome requirements for the unified knowledge provider integration.

## Impact

- Affected code:
  - new trial service under `backend/capability_runtime/`
  - new export script under `scripts/`
- Affected tests:
  - focused backend tests with mocked provider responses
- Affected docs:
  - generated trial outcome under `docs/integration/unified-knowledge-provider-trial/`
- No default runtime behavior changes.
