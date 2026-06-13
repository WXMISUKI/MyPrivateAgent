## Context

The external `unifiedKnowledgeRAG` provider can already serve explicit local RAG calls through `knowledge.rag.retrieve`. MyPrivateAgent already registers the provider through the unified capability runtime and surfaces health/catalog information through capability heartbeat. The missing piece is a compact, caller-owned readiness read model that explains whether the provider is usable for explicit RAG and why GraphRAG/default chat grounding remain gated.

## Goals / Non-Goals

**Goals:**

- Add a read-only `governance_readiness` block to Knowledge Provider health/heartbeat payloads.
- Reuse existing provider health, catalog summary, and capability runtime surfaces.
- Distinguish explicit RAG readiness from GraphRAG promotion and default chat grounding.
- Keep failures structured and fail-open for the main app.
- Cover ready, unreachable, degraded, and unconfigured/disabled states with focused tests.

**Non-Goals:**

- Do not change `unifiedKnowledgeRAG`.
- Do not enable default `/api/chat` retrieval injection.
- Do not execute or promote GraphRAG.
- Do not create source-to-agent bindings.
- Do not change answer composition, prompt, memory, approval, audit, or trace behavior.

## Decisions

1. Put the read model under Knowledge Provider health/heartbeat payloads.
   - Rationale: capability heartbeat already aggregates provider and per-capability health. Adding a compact readiness block there avoids another endpoint and keeps diagnostics provider-neutral.
   - Alternative considered: add a new Runtime Surface top-level card immediately. Rejected for this slice because the runtime surface can consume heartbeat/readiness later without expanding UI now.

2. Treat `rag_retrieve` and `graph_query` separately.
   - Rationale: RAG retrieve is locally usable; GraphRAG remains separately gated. A single provider status would hide this boundary.
   - Alternative considered: derive readiness from provider `status=ready` only. Rejected because provider ready does not mean GraphRAG or chat grounding is promoted.

3. Keep source catalog posture as evidence, not authorization.
   - Rationale: source catalog readiness helps governance diagnose missing/degraded sources but must not create source bindings or default injection behavior.
   - Alternative considered: use source catalog readiness to auto-promote domain agent grounding. Rejected because grounding promotion requires separate policy/eval gates.

4. Use compact fields only.
   - Rationale: readiness should not copy full provider documents, retrieval results, API keys, or raw large payloads.

## Risks / Trade-offs

- [Risk] Consumers may interpret `ready` as default chat grounding approval. -> Mitigation: readiness includes explicit `default_chat_grounding = gated` and `graph_query = gated` semantics.
- [Risk] Provider catalog is unavailable while health is ready. -> Mitigation: report degraded readiness and preserve main app health.
- [Risk] Readiness becomes another source of truth separate from capability health. -> Mitigation: derive it from the same health/catalog payload in the Knowledge HTTP provider adapter.
