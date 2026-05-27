# Change: unified-knowledge-capability-runtime

## Why

RAG and knowledge graph sources are already described in domain agent manifests, but they are not first-class runtime capabilities yet. MyPrivateAgent needs a provider-neutral Knowledge Capability layer so external RAG and graph services can be discovered, health-checked, invoked, and governed without embedding vector stores, graph databases, document parsing, or model-specific dependencies into the core backend.

## What Changes

- Add a Knowledge Capability contract for external RAG retrieval and knowledge graph query providers.
- Add read-only RAG source and knowledge graph registry surfaces derived from domain agent manifests.
- Register external knowledge provider capabilities through the existing capability runtime pattern.
- Document how to build a standalone `unifiedKnowledgeProvider` / `unifiedRAGProvider` project for MyPrivateAgent integration.
- Keep MCP and Skill responsibilities unchanged: MCP remains external tool/resource access, and Skill remains runtime strategy/prompt injection.

## 收口对象

- `capability_runtime` provider-neutral registration for `knowledge.rag.retrieve` and `knowledge.graph.query`.
- Runtime Surface read-only contracts for `rag_source_registry` and `knowledge_graph_registry`.
- Domain agent manifest knowledge declarations under `capabilities.rag_sources` and `capabilities.graph_sources`.
- External provider integration documentation under `docs/guides/`.

## 非目标

- Do not implement an in-process vector database, graph database, embedding model, reranker, OCR, or document parser inside MyPrivateAgent.
- Do not add chat auto-retrieval or graph reasoning into the default `/api/chat` execution path in this slice.
- Do not implement ingestion jobs, file upload pipelines, graph editors, ontology editors, or background indexing schedulers.
- Do not replace MCP with RAG or RAG with MCP; they remain separate capability families.

## Capabilities

### New Capabilities

- `unified-knowledge-capability-runtime`: Provider-neutral RAG and knowledge graph capability registration, source registry, health, invocation, and external provider documentation.

### Modified Capabilities

- `domain-agent-asset-registry`: Domain agent manifests can expose `capabilities.graph_sources` alongside existing `capabilities.rag_sources`.
- `unified-capability-runtime`: The capability registry can expose knowledge capabilities backed by an external HTTP provider.

## Impact

- Backend contracts: add read-only knowledge registries to Runtime Surface and external knowledge capability definitions.
- Frontend consumers: existing capability diagnostics can display knowledge provider status through `/api/capabilities`; Runtime Surface can later display source/graph registries.
- Docs: add an external RAG/Knowledge Provider development guide and align domain agent guidance with graph source declarations.
- Dependencies: no new core backend dependency on vector stores, graph databases, embedding libraries, or document loaders.

