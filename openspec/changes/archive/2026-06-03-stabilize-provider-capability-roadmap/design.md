## Context

The project already has strong runtime control-plane contracts and has moved heavy capabilities toward external providers. Document capability contracts are now canonical, and the remaining active provider work is `plan-external-rag-graphrag-provider`.

The next risk is planning drift: P0/P1/P2 work spans several independent concerns, and implementing them in one change would mix provider data-plane readiness, agent behavior policy, prompt governance, memory lifecycle, and evaluation infrastructure.

## Design

### 1. Use one stable roadmap spec

Add `provider-capability-roadmap` as a canonical OpenSpec capability. It is a planning guardrail, not a runtime API contract. It records the order and boundaries of future changes.

### 2. Keep external provider development decoupled

External RAG / GraphRAG remains a data-plane project. MyPrivateAgent should only move beyond contract/readiness once the external provider exposes stable readiness evidence:

- `/health`
- `/api/capabilities`
- `/api/catalog` or source catalog equivalent
- `/api/rag/sources`
- `/api/rag/retrieve`
- `/api/graph/schemas`
- structured `/api/graph/query` behavior, either implemented or `GRAPH_NOT_IMPLEMENTED`

### 3. Split future work by concern

Future changes should be separate:

- `plan-external-rag-graphrag-provider`: finish active provider line.
- `add-agent-grounding-policy-contract`: agent grounding policy and source ACL semantics.
- `add-promptops-versioned-prompt-contract`: prompt version/template/eval/rollout governance.
- `add-agent-memoryops-lifecycle-contract`: memory lifecycle and injection evidence.
- `add-multiturn-agent-evaluation-gate`: scenario-based regression for prompt/RAG/context.
- Future P2 changes for multimodal taxonomy, workflow/chatflow, enterprise connectors, and provider ops.

### 4. Keep implementation out of this change

This change only stabilizes direction. It should be archived after validation so the canonical spec can guide later work.

## Alternatives Considered

- One large OpenSpec change for all P0/P1/P2 work: rejected because verification would be too broad and implementation would mix unrelated contracts.
- Put the roadmap only in markdown: rejected because the user explicitly wants stable spec-backed direction.
- Modify default chat retrieval now: rejected because external provider readiness is not yet final and grounding policy has not been specified.

## Risks

- Roadmap spec may be treated as implementation complete. Mitigation: state clearly that it only authorizes future focused changes.
- External provider may evolve contract fields. Mitigation: keep MyPrivateAgent integration gated by provider catalog/readiness smoke before runtime promotion.
