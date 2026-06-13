## Why

The RAG provider and caller loop has reached its current closure line, so the next highest-value work is to return to the Agent Runtime Control Plane core. The current `main_chat` query observation path is usable, but the query/run read-model boundary still needs one focused hardening pass so Runtime Surface and Governance Timeline keep consuming the same contract semantics.

## What Changes

- Harden the existing `main_chat` query/run read model boundary without changing default chat, RAG, provider, or execution behavior.
- Align `main_chat_query_detail`, `main_chat_query_history`, and shared frontend interpretation around the same `query_id` lifecycle semantics.
- Reduce reliance on ad hoc frontend timeline derivation where the backend read model already exposes stable fields.
- Update architecture and roadmap docs to record the phase completion line and stop conditions.
- Non-goals:
  - Do not expand `unifiedKnowledgeRAG` provider behavior.
  - Do not enable default `/api/chat` retrieval injection.
  - Do not promote new channels to full query history or workspace.
  - Do not redesign Governance Timeline or Runtime Surface UI.
  - Do not introduce GraphRAG, rerank, hybrid retrieval, query rewrite, or source binding automation.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `query-run-read-model`: harden the existing `main_chat` query detail/history read-model requirements and shared interpretation requirements.

## Impact

- Affected backend contracts:
  - `main_chat_query_detail`
  - `main_chat_query_history`
  - `main_chat_trace_overview.recent_queries`
- Affected frontend consumers:
  - `frontend-vue/src/services/governanceViewInterpretation.js`
  - `RuntimeSurfacePanel`
  - `GovernanceTimelinePanel` and related `Main Chat Query Workspace` components
- Affected docs/specs:
  - `openspec/specs/query-run-read-model/spec.md`
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`
- Verification:
  - Focused frontend/backend tests for query read model and shared interpretation.
  - `openspec validate --all --strict`.
