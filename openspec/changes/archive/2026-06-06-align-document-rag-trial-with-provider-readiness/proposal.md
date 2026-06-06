## Why

`unifiedKnowledgeRAG` now publishes a Phase 24 document RAG trial readiness closure with `decision=go`. MyPrivateAgent already has a repo-side unified knowledge provider trial outcome, but the trial artifact does not explicitly record the provider-side document RAG closure that justified starting the trial.

This change aligns the caller-side trial with the current provider-side readiness posture so reviewers can see both sides in one place:

- provider-side Phase 24 document RAG readiness closure
- MyPrivateAgent repo-side HTTP trial checks
- caller-owned go/review/blocked outcome

## What Changes

- Add optional provider readiness input to the repo-side unified knowledge provider trial outcome.
- Validate and summarize the Phase 24 document RAG readiness closure when a readiness artifact path is provided.
- Keep the existing live HTTP trial checks unchanged:
  - `GET /health`
  - `GET /api/provider/manifest`
  - `GET /api/provider/preflight`
  - `GET /api/provider/source-bindings`
  - `POST /api/rag/retrieve`
- Expose the readiness linkage in JSON/Markdown trial artifacts without storing secrets.
- Update focused tests and docs around the trial outcome.

## Capabilities

### Modified Capabilities

- `unified-knowledge-capability-runtime`: clarify that repo-side document RAG trial outcome can consume provider-side Phase 24 readiness closure evidence as read-only context.

## Impact

- Affected code:
  - `backend/capability_runtime/knowledge_provider_trial.py`
  - `scripts/export_unified_knowledge_provider_trial_outcome.py`
- Affected tests:
  - `tests/agent_framework/test_knowledge_provider_trial.py`
- Affected docs:
  - generated trial outcome under `docs/integration/unified-knowledge-provider-trial/`
- No default chat behavior changes.
- No source-to-agent binding, approval, audit, retrieval backend promotion, or GraphRAG execution.
