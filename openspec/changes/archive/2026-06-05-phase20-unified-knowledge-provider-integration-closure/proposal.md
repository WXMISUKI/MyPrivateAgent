## Why

Phase 19 proved the caller-side unified knowledge provider trial can pass against the lightweight provider contract. The remaining risk is process drift: continuing to add readiness evidence instead of closing the provider readiness chain and moving the next behavior-control work to grounding policy.

This change closes the provider integration readiness evidence line with a small, explicit go/review/blocked decision. It keeps MyPrivateAgent as the caller/control plane, keeps unifiedKnowledgeRAG as the provider/data plane, and prevents default chat retrieval injection from being enabled before grounding policy and evaluation gates exist.

## What Changes

- Add a Phase 20 closure decision artifact for the unified knowledge provider integration.
- Summarize Phase 19 trial outcome, provider readiness checks, remaining graph boundary, and next-line ownership.
- Update provider roadmap semantics to state that readiness evidence should close once caller-side trial passes, instead of continuing as an open-ended handoff-evidence stream.
- Keep `plan-external-rag-graphrag-provider` task decisions honest: completed caller-side trial tasks can close; default chat injection remains delegated to `add-agent-grounding-policy-contract`.

## Impact

- Backend:
  - Adds a small read-only closure decision builder.
  - Does not change default `/api/chat` retrieval behavior.
- Scripts:
  - Adds a local exporter for the Phase 20 closure artifact.
- Docs:
  - Adds a closure decision markdown/json artifact under `docs/integration/unified-knowledge-provider-trial/`.
- OpenSpec:
  - Adds closure requirements for `unified-knowledge-capability-runtime`.
  - Updates provider roadmap semantics around evidence/readiness stop conditions.
- Non-goals:
  - No vector store, graph database, LlamaIndex, Neo4j, embedding, rerank, parser, or GraphRAG runtime dependency is added to MyPrivateAgent.
  - No source-to-agent binding, approval, audit policy, or default answer composition is created here.
  - No default chat retrieval injection is enabled in this phase.
