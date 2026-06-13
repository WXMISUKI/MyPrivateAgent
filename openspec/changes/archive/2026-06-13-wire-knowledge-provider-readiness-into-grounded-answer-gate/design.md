## Context

The grounded-answer promotion gate already aggregates provider, grounding, PromptOps, MemoryOps, and deterministic eval evidence. Provider evidence was previously interpreted through broad status fields. Knowledge Provider capability health now exposes a more precise `governance_readiness` block that distinguishes explicit RAG readiness from GraphRAG and default chat grounding gates.

## Goals / Non-Goals

**Goals:**

- Prefer `provider_evidence.governance_readiness` when evaluating provider readiness.
- Preserve legacy provider evidence compatibility for existing trial payloads.
- Allow document RAG promotion when `rag_retrieve.status=ready` and other evidence is ready.
- Block graph grounded-answer promotion when `graph_query.status=gated`.
- Keep degraded/unreachable provider readiness as review/blocked with machine-readable reasons.

**Non-Goals:**

- No provider HTTP calls.
- No answer generation or composition behavior change.
- No default `/api/chat` retrieval injection.
- No GraphRAG execution.
- No source binding automation.

## Decisions

1. Add a small provider evidence normalizer inside the promotion service.
   - Rationale: the promotion service owns the gate semantics and already consumes provider evidence.
   - Alternative considered: normalize in routers or trial services. Rejected because that would scatter promotion semantics.

2. Treat `governance_readiness.rag_retrieve.status=ready` as provider ready for document RAG.
   - Rationale: this is the new caller-owned readiness contract.
   - Alternative considered: require `overall_status=ready` only. Rejected because a degraded source catalog can still require review, while RAG status is the direct document RAG usability signal.

3. Preserve GraphRAG as a separate blocker.
   - Rationale: provider RAG readiness does not prove graph execution readiness.

4. Keep legacy evidence accepted.
   - Rationale: existing tests and local trial payloads may still provide `status=ready` or similar fields.

## Risks / Trade-offs

- [Risk] A degraded catalog with RAG ready could be over-promoted. -> Mitigation: return review when source catalog status is degraded unless existing policy explicitly treats the provided evidence as safe.
- [Risk] Graph requests could be accidentally allowed through document RAG readiness. -> Mitigation: add focused graph-gated test.
- [Risk] Existing trial payloads may not contain `governance_readiness`. -> Mitigation: keep legacy status fallback.
