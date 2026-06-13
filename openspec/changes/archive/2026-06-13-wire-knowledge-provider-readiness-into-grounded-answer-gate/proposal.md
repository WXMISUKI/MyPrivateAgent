## Why

Knowledge Provider RAG is closed for explicit local use, and MyPrivateAgent now exposes caller-owned `governance_readiness` in capability health/heartbeat. The grounded-answer promotion gate should consume that readiness directly so domain-agent trial promotion is based on the same provider control-plane evidence rather than loose provider status fields.

## What Changes

- Wire Knowledge Provider `governance_readiness` into the grounded-answer promotion gate's provider evidence evaluation.
- Treat `rag_retrieve.status=ready` as the explicit document RAG readiness signal.
- Preserve `graph_query.status=gated` as a blocker for graph grounded-answer requests.
- Preserve `default_chat_grounding.status=gated` as a non-blocking boundary for repo-side trial, not a promotion to default chat.
- Keep the promotion gate side-effect-free.
- Non-goals:
  - Do not call `unifiedKnowledgeRAG`.
  - Do not generate answers.
  - Do not enable default `/api/chat` retrieval injection.
  - Do not execute GraphRAG.
  - Do not create source-to-agent bindings.
  - Do not change PromptOps, MemoryOps, audit, approval, memory, or answer composition behavior.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `domain-agent-grounded-answer-promotion-gate`: provider evidence evaluation now recognizes Knowledge Provider `governance_readiness`.

## Impact

- Affected backend:
  - `backend/services/domain_agent_grounded_answer_promotion_service.py` or equivalent promotion gate service
  - existing grounded-answer promotion tests
- Affected docs/specs:
  - `openspec/specs/domain-agent-grounded-answer-promotion-gate/spec.md`
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`
- Verification:
  - Focused promotion gate tests.
  - `openspec validate --all --strict`.
