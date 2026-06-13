## Why

`unifiedKnowledgeRAG` has closed its local provider-use loop and is running at `http://127.0.0.1:8020`. MyPrivateAgent now needs to close the caller-side loop: enable, discover, explicitly invoke, and export provider-compatible evidence without changing default chat grounding.

This change turns the existing Phase 26 runbook into a verified MyPrivateAgent closure slice, so the team can stop re-checking provider readiness and move forward from a clear caller-owned evidence artifact.

## What Changes

- Add a caller-side closure contract for MyPrivateAgent using `unifiedKnowledgeRAG` as an external knowledge capability provider.
- Document the minimal enablement settings for local caller verification:
  - `ENABLE_KNOWLEDGE_CAPABILITY_PROVIDER=true`
  - `KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL=http://127.0.0.1:8020`
- Refresh the explicit company-profile caller smoke and provider-compatible trial outcome artifacts.
- Add or update a concise MyPrivateAgent runbook that links provider startup, MyPrivateAgent env settings, caller smoke, provider feedback payload, and boundary interpretation.
- Keep the closure explicit and side-effect-free:
  - no default `/api/chat` retrieval injection
  - no source-to-agent binding automation
  - no GraphRAG execution
  - no provider runtime promotion
  - no final answer policy change

## Capabilities

### New Capabilities
- `knowledge-provider-caller-loop-closure`: Defines the MyPrivateAgent-side enablement, explicit smoke, evidence artifacts, and boundaries for consuming `unifiedKnowledgeRAG`.

### Modified Capabilities
- `unified-knowledge-capability-runtime`: Clarifies that Phase 26 caller closure includes MyPrivateAgent-side local provider enablement/runbook and refreshed caller evidence, not another provider-readiness chain.

## Impact

- Affected docs:
  - `docs/integration/phase26-caller-provider-live-trial-closure/*`
  - new or updated MyPrivateAgent local provider use runbook under `docs/integration/`
- Affected evidence artifacts:
  - `docs/integration/company-profile-explicit-api-local-smoke/*`
  - `docs/integration/unified-knowledge-provider-trial/*`
- Affected config documentation:
  - local env examples or runbook references for `ENABLE_KNOWLEDGE_CAPABILITY_PROVIDER` and `KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL`
- Affected code paths:
  - existing `backend/capability_runtime` registry/provider adapter may be verified, but no runtime behavior change is intended unless documentation or focused tests reveal a gap.
- No frontend, default chat flow, GraphRAG execution, source binding automation, or provider implementation changes are intended.
