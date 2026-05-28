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
- [ ] 3.4 Implement LlamaIndex-backed document RAG for the first knowledge base.
- [ ] 3.5 Implement Neo4j GraphRAG-backed graph query for the first graph namespace.
- [ ] 3.6 Add MyPrivateAgent source readiness visibility after the provider exposes stable catalog responses.

## 4. Verification and Archive

- [x] 4.1 Run `openspec validate plan-external-rag-graphrag-provider --strict`.
- [x] 4.2 Run a documentation review pass for contract drift against existing guides.
- [ ] 4.3 After implementation tasks are complete, archive the change with OpenSpec and confirm canonical specs/docs contain the final decisions.
