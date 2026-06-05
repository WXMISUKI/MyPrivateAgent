## 1. Specification

- [x] 1.1 Validate the OpenSpec change and confirm the proposal, design, specs, and tasks are internally consistent.
- [x] 1.2 Confirm `external-rag-graphrag-provider-plan` captures the new planning capability.
- [x] 1.3 Confirm delta specs only extend `domain-agent-asset-registry` and `unified-knowledge-capability-runtime` without changing current runtime behavior.

## 2. Documentation

- [x] 2.1 Add an external RAG / GraphRAG provider design guide under `docs/guides/`.
- [x] 2.2 Update `docs/guides/external_rag_provider_development.md` with LlamaIndex and Neo4j GraphRAG implementation guidance.
- [x] 2.3 Update `docs/guides/domain_agent_development_guide.md` with a sample retrieval policy section.
- [x] 2.4 Document the spec -> implementation -> archive cadence for this provider work.

## 3. Future Implementation Plan

- [x] 3.1 Scaffold a standalone `unifiedKnowledgeProvider` project in a later implementation change.
- [x] 3.2 Implement `/health`, `/api/capabilities`, `/api/rag/sources`, `/api/rag/retrieve`, `/api/graph/schemas`, and `/api/graph/query` in the provider.
- [x] 3.3 Implement a provider-managed source catalog with readiness and version metadata.
- [x] 3.4 External provider readiness gate: confirm the external RAG / GraphRAG project exposes stable `/health`, `/api/capabilities`, `/api/catalog` or equivalent source catalog, `/api/rag/sources`, `/api/rag/retrieve`, `/api/graph/schemas`, and structured `/api/graph/query` behavior.
- [x] 3.5 Implement LlamaIndex-backed document RAG for the first knowledge base in the external provider project, not in the MyPrivateAgent main backend.
- [x] 3.6 Keep GraphRAG at schema/discovery or structured `GRAPH_NOT_IMPLEMENTED` until the external provider has a verifiable Neo4j GraphRAG namespace.
- [x] 3.7 Add MyPrivateAgent source readiness visibility after the provider exposes stable catalog responses.
- [x] 3.8 Add a caller-side local integration smoke that consumes provider health/catalog/RAG retrieval without changing default `/api/chat` behavior.
- [x] 3.9 Leave default chat retrieval injection to a later grounding policy OpenSpec change.

## 4. Verification and Archive

- [x] 4.1 Run `openspec validate plan-external-rag-graphrag-provider --strict`.
- [x] 4.2 Run a documentation review pass for contract drift against existing guides.
- [x] 4.3 Run provider-side focused verification when the external project is ready.
- [x] 4.4 Run MyPrivateAgent caller-side readiness smoke after provider readiness is available.
- [x] 4.5 After implementation tasks are complete, archive the change with OpenSpec and confirm canonical specs/docs contain the final decisions.

## Phase 20 Closure Note

- Phase 20 closure decision is `go` for the minimal MyPrivateAgent caller-side provider access path.
- Readiness evidence expansion should stop for the minimal access path; the next behavior-control line is `add-agent-grounding-policy-contract`.
- This change remains open for broader provider-side proof items that Phase 20 does not claim: full readiness gate coverage, first LlamaIndex-backed document RAG confirmation, and provider-side focused verification.
