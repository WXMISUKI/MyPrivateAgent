## Context

MyPrivateAgent already has a provider-neutral capability runtime and an external knowledge provider contract. `backend/domain_agents/*/agent.yaml` can declare `rag_sources` and `graph_sources`, and Runtime Surface exposes read-only registries for those declarations. The current missing piece is a concrete implementation plan for the external RAG / GraphRAG provider and the domain-agent policy that decides how those knowledge sources are bound.

Current source-of-truth documents:

- `docs/guides/domain_agent_development_guide.md`
- `docs/guides/external_rag_provider_development.md`
- `openspec/specs/domain-agent-asset-registry/spec.md`
- `openspec/specs/unified-knowledge-capability-runtime/spec.md`

Framework positioning:

- LlamaIndex is a strong fit for mainstream RAG provider internals because its framework documentation organizes ingestion, indexing, querying, retrievers, vector stores, agents, tools, and evaluation as separate components.
- Neo4j GraphRAG is a strong fit for knowledge graph retrieval because it centers graph retrievers, Neo4j-backed vector/fulltext/hybrid retrieval, Cypher traversal, and graph-grounded result evidence.
- Neither framework should replace MyPrivateAgent runtime, policy, approval, query control, runtime surface, or audit contracts.

## Goals / Non-Goals

**Goals:**

- Define a staged implementation plan for domain-agent knowledge binding and external provider development.
- Document when to use LlamaIndex-backed RAG, when to use Neo4j GraphRAG, and when to combine both.
- Keep heavy dependencies outside MyPrivateAgent.
- Keep all retrieval and graph results auditable with citations or graph evidence.
- Create an implementation checklist that can be applied and archived through OpenSpec.

**Non-Goals:**

- No default chat auto-retrieval in this planning slice.
- No vector store, graph database, embedding model, reranker, or parser dependencies in the main backend.
- No knowledge upload console, graph editor, ontology editor, or document management UI in MyPrivateAgent.
- No per-domain provider project proliferation; prefer one external provider managing many knowledge bases and graph namespaces.

## Decisions

1. **Use one external provider as the knowledge data plane.**
   - Decision: Build an independent `unifiedKnowledgeProvider` / `unifiedRAGProvider` that manages multiple `knowledge_base`, `collection`, `document_source`, `graph_namespace`, and `ontology` records.
   - Alternative considered: Create one provider per vertical domain.
   - Rationale: One provider centralizes health, credentials, indexing operations, observability, and source catalog governance while still allowing source-level isolation.

2. **Use LlamaIndex for document RAG internals.**
   - Decision: Use LlamaIndex inside the external provider for ingestion, node parsing, indexing, retrievers, query engines, vector store adapters, and optional evaluation utilities.
   - Alternative considered: Hand-roll loading/chunking/retrieval from scratch.
   - Rationale: LlamaIndex provides mature abstractions for RAG pipelines and many integrations. The provider can expose stable MyPrivateAgent HTTP contracts while hiding LlamaIndex internals.

3. **Use Neo4j GraphRAG for graph-heavy retrieval.**
   - Decision: Use Neo4j GraphRAG when the question requires entity/relation/path evidence, graph traversal, hybrid graph-vector retrieval, or Cypher-backed constraints.
   - Alternative considered: Treat graph queries as ordinary vector RAG.
   - Rationale: Knowledge graphs carry relationship semantics that should be returned as `entities`, `relations`, `paths`, and `evidence`, not flattened into snippets only.

4. **Keep domain-agent prompts separate from knowledge data.**
   - Decision: Domain agents own role positioning, behavior boundaries, retrieval behavior, and fallback policy under `backend/domain_agents/<agent_id>/`; the provider owns data and retrieval.
   - Alternative considered: Let provider decide business persona and final answer behavior.
   - Rationale: Business role, refusal policy, approvals, and audit belong to MyPrivateAgent governance. The provider should return evidence, not impersonate the final agent.

5. **Represent retrieval policy explicitly.**
   - Decision: Future `agent.yaml` can document `retrieval` fields such as mode, top_k, citation requirement, graph usage, fallback policy, and allowed filters.
   - Alternative considered: Encode retrieval behavior only in prompt text.
   - Rationale: Structured policy can be validated, shown in Runtime Surface, and tested without scraping prompt content.

6. **Use staged adoption.**
   - Decision:
     1. Spec and docs.
     2. External provider scaffold.
     3. Provider source catalog and health.
     4. RAG retrieve endpoint.
     5. Graph query endpoint.
     6. MyPrivateAgent registry readiness check.
     7. Optional chat retrieval injection in a later OpenSpec change.
   - Rationale: This keeps the first deliverables verifiable and avoids mixing provider buildout with chat behavior changes.

## Risks / Trade-offs

- [Risk] `agent.yaml` declarations drift from provider sources. -> Mitigation: provider `/api/capabilities` and source catalog checks report missing or degraded sources.
- [Risk] Agents over-trust retrieved content. -> Mitigation: require citations for RAG, graph evidence for graph queries, and policy approval for high-risk actions.
- [Risk] Graph modeling becomes expensive too early. -> Mitigation: start with RAG for document-heavy domains; use GraphRAG only where entity relationships and multi-hop reasoning are explicit product needs.
- [Risk] Provider internals leak into MyPrivateAgent. -> Mitigation: keep HTTP JSON contracts stable and provider-neutral; do not expose LlamaIndex or Neo4j internal classes to the main backend.
- [Risk] One provider becomes operationally large. -> Mitigation: isolate by source ids, graph ids, tenants, ACL filters, and index lifecycle jobs; split later only if operational boundaries demand it.

## Migration Plan

1. Land this planning change with docs and specs only.
2. Implement a new external provider repository or sibling project, not inside the main backend runtime.
3. Wire `.env` to `KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL` when the provider is ready.
4. Keep `/api/chat` behavior unchanged until a later OpenSpec change explicitly adds retrieval injection.
5. Archive this change once docs, provider scaffold expectations, and source binding contracts are merged into canonical specs/docs.

Rollback strategy: remove the provider URL from `.env`; MyPrivateAgent starts without knowledge capabilities, preserving the current fail-open runtime behavior.

## Open Questions

- Which first domain should validate the provider: ecommerce support, internal enterprise assistant, or public-security document assistant?
- Should the first external provider live in this repository as a sibling folder for convenience, or in a separate repository from day one?
- Which vector store should be used for the first slice: local Chroma/Qdrant for development, Postgres pgvector, Elasticsearch, or another enterprise store?
- Should graph ingestion be manual schema-first at first, or should entity extraction from documents be automated later?
