## Context

MyPrivateAgent already treats `unifiedKnowledgeRAG` as an external Knowledge Provider through provider-neutral capability contracts. The provider can expose compact `governance_readiness`, and the grounded-answer promotion gate already consumes that evidence to distinguish explicit document RAG readiness, degraded source catalog, unreachable provider, and GraphRAG gated boundaries.

The explicit grounded-answer trial surface is the next caller-owned readiness layer. It should preserve provider readiness evidence in its bounded trial report, but it must remain upstream of package dry-run, composition trial, answer generation, provider invocation, and default chat behavior.

## Goals / Non-Goals

**Goals:**

- Let grounded-answer trial reports include compact caller-supplied provider governance readiness evidence.
- Keep trial status aligned with promotion gate outcomes for ready, review, blocked, and graph-gated cases.
- Preserve provider blockers and warnings in machine-readable form for downstream dry-run/composition layers.
- Add focused test coverage around the trial surface boundary.

**Non-Goals:**

- No provider HTTP call from the trial surface.
- No default `/api/chat` retrieval injection.
- No model call or final answer generation.
- No source binding, audit, memory, trace, or approval mutation.
- No GraphRAG execution promotion.
- No retrieval strategy work inside `unifiedKnowledgeRAG`.

## Decisions

1. Use caller-supplied evidence as the only provider input.

   Rationale: the trial surface is a deterministic readiness layer. Calling the provider here would mix live IO into a side-effect-free report and blur the boundary with the live provider trial.

2. Preserve compact readiness under the trial report instead of copying provider raw payloads.

   Rationale: downstream package dry-run and composition trial need status, reasons, blockers, and warnings, not raw documents or provider internals. This keeps the report safe for governance surfaces and artifacts.

3. Reuse promotion gate semantics as the source of truth for trial status.

   Rationale: the promotion gate already owns provider-readiness decisions. The trial surface should report those decisions rather than invent a second status mapping.

4. Keep GraphRAG blocked when `graph_query.status = gated`.

   Rationale: document RAG readiness is not GraphRAG execution readiness. The trial surface should make this explicit before any answer package can be built.

## Risks / Trade-offs

- Provider readiness evidence may be absent in older callers -> keep existing trial behavior compatible and only include provider readiness when supplied.
- Compact readiness could be mistaken for default chat promotion -> include explicit promotion-boundary fields and doc updates.
- Trial report may grow slightly -> limit additions to status, reasons, blockers, warnings, and readiness summary only.
