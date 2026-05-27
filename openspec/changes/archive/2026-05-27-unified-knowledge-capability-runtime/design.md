## Context

MyPrivateAgent already has MCP Runtime, Skill Runtime, Domain Agent Registry, and provider-neutral capability runtime surfaces. Domain agent manifests can declare `rag_sources`, but those declarations are currently only asset metadata. There is no first-class RAG source registry, knowledge graph registry, or external knowledge provider capability.

RAG and graph workloads typically require dependencies that should not be part of the core control plane: vector stores, embedding models, document loaders, rerankers, graph databases, entity extraction, and index lifecycle management. This change keeps those execution concerns in a standalone provider and lets MyPrivateAgent own discovery, governance, invocation envelope, and evidence.

## Goals / Non-Goals

**Goals:**

- Define RAG and knowledge graph as provider-neutral Knowledge Capabilities.
- Register `knowledge.rag.retrieve` and `knowledge.graph.query` through the existing capability runtime when an external knowledge provider is configured.
- Expose read-only `rag_source_registry` and `knowledge_graph_registry` contracts from domain agent manifests.
- Document how to build an external `unifiedKnowledgeProvider` / `unifiedRAGProvider` project.

**Non-Goals:**

- No vector database, graph database, embedding model, reranker, OCR, ingestion job, or indexing scheduler inside MyPrivateAgent.
- No default `/api/chat` auto-retrieval or graph reasoning in this slice.
- No graph editor, ontology editor, document upload console, or business-specific source management UI.
- No replacement of MCP or Skill semantics.

## Decisions

1. **Use one external Knowledge Provider for many sources.**
   - Decision: A single external provider manages multiple knowledge bases, collections, graph namespaces, and ontologies.
   - Rationale: Per-source projects fragment operations, health, credentials, and governance. A single provider can still isolate data through source ids, graph ids, filters, and permissions.

2. **Keep RAG and Graph as separate capability families.**
   - Decision: Use `knowledge.rag.*` for semantic document retrieval and `knowledge.graph.*` for entity/relation/path queries.
   - Rationale: RAG citations and graph path evidence have different schemas and governance needs. Combining them too early hides ontology and relationship constraints.

3. **Reuse capability runtime instead of adding a separate execution plane.**
   - Decision: External knowledge invocation uses `/api/capabilities/{capability_id}/invoke` and heartbeat uses existing capability heartbeat semantics.
   - Rationale: Voice provider work already established the provider-neutral pattern and fail-open health behavior.

4. **Make registries read-only in v1.**
   - Decision: MyPrivateAgent reads knowledge declarations from domain agent manifests and exposes registry contracts. It does not create indexes or mutate provider state.
   - Rationale: This keeps the first slice deterministic, testable, and safe while the external provider is being developed.

## Risks / Trade-offs

- [Risk] Registry declarations can drift from the external provider. -> Mitigation: provider heartbeat and future active tests report unreachable or missing source conditions without blocking startup.
- [Risk] Knowledge results may be over-trusted by agents. -> Mitigation: RAG responses MUST include citations, graph responses MUST include entity/relation/path evidence, and high-risk actions still go through policy/approval.
- [Risk] Operators may confuse MCP resources with RAG sources. -> Mitigation: docs and contracts keep MCP, Skill, RAG, and Graph responsibilities separate.
- [Risk] v1 does not improve answer quality automatically. -> Mitigation: this slice establishes the contract and provider integration; chat retrieval injection can be added in a later change.

