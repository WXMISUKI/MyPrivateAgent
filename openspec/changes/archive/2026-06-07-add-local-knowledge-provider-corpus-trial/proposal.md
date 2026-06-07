## Why

`unifiedKnowledgeRAG` now reports the approved `company_profile_2025_trial` corpus as usable through live HTTP. MyPrivateAgent needs caller-owned proof that it can run a focused local corpus trial against that source before moving the knowledge path into broader domain-agent or chat workflows.

## What Changes

- Add a read-only local knowledge provider corpus trial exporter in MyPrivateAgent.
- The trial calls the already-running provider over HTTP and validates:
  - `GET /api/rag/sources`
  - `GET /api/rag/sources/{source_id}/documents`
  - `POST /api/rag/retrieve`
  - `POST /api/rag/answer`
- Default source is `company_profile_2025_trial`.
- Default cases include company-profile answerable questions and one unrelated negative-control query.
- Export JSON and Markdown trial artifacts under `docs/integration/local-knowledge-provider-corpus-trial/`.
- Keep the trial explicit and opt-in: no default chat retrieval injection, source-to-agent binding, audit policy mutation, provider startup, backend promotion, OCR, or GraphRAG execution.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `unified-knowledge-capability-runtime`: Add a caller-side local corpus trial requirement for a provider-visible source.

## Impact

- Affected code:
  - new trial service under `backend/capability_runtime/`
  - new export script under `scripts/`
- Affected tests:
  - focused backend tests using mocked HTTP transport
- Affected docs:
  - generated trial artifact under `docs/integration/local-knowledge-provider-corpus-trial/`
  - external provider guide and architecture notes
- No default runtime behavior changes.
