## Why

MyPrivateAgent has already moved heavy ASR/TTS capability into external providers, and RAG / knowledge graph should follow the same control-plane/data-plane split. The next step is to define how domain agents bind knowledge sources, how an external provider should be built, and how LlamaIndex and Neo4j GraphRAG are used as implementation references without becoming the project positioning.

收口对象：主项目的垂域 Agent 知识绑定、外部 RAG / GraphRAG Provider 开发文档、以及后续实现和归档节奏。

非目标：本变更不把向量库、图数据库、Embedding、OCR、文档解析、rerank、索引调度或 Neo4j/LlamaIndex 依赖引入 MyPrivateAgent 主后端；不立即修改默认 `/api/chat` 自动检索行为；不建设知识库上传 UI 或图谱编辑器。

## What Changes

- Add a planning contract for domain-agent knowledge binding and retrieval policy.
- Add a provider implementation design that recommends LlamaIndex for mainstream document RAG orchestration and Neo4j GraphRAG for graph-backed entity/relation/path retrieval.
- Document the external provider project layout, API contracts, source catalog, lifecycle boundaries, and validation checklist.
- Define the implementation sequence: spec, implementation, verification, archive, then git submission.
- Keep MyPrivateAgent as the runtime control plane: it owns agent manifests, governance visibility, capability invocation envelopes, policy, audit, and trace evidence.
- Keep the external provider as the knowledge data plane: it owns ingestion, parsing, chunking, embedding, vector storage, graph storage, ontology, retrieval, rerank, and index lifecycle.

## Capabilities

### New Capabilities

- `external-rag-graphrag-provider-plan`: Planning contract for the independent RAG / GraphRAG provider, framework choices, source catalog, API expectations, and implementation cadence.

### Modified Capabilities

- `domain-agent-asset-registry`: Domain agent manifests gain documented knowledge binding and retrieval policy expectations.
- `unified-knowledge-capability-runtime`: The existing provider-neutral knowledge runtime gains documented implementation guidance for LlamaIndex-backed RAG and Neo4j-backed GraphRAG provider projects.

## Impact

- Docs:
  - `docs/guides/external_rag_provider_development.md`
  - new external provider design guide under `docs/guides/`
  - `docs/guides/domain_agent_development_guide.md`
- OpenSpec:
  - new change under `openspec/changes/plan-external-rag-graphrag-provider/`
  - delta specs for `domain-agent-asset-registry` and `unified-knowledge-capability-runtime`
- Runtime contracts:
  - no immediate contract-breaking change
  - future implementation may extend `agent.yaml` parsing with `retrieval` policy fields
- Frontend:
  - no immediate UI change
  - future governance UI may display provider source readiness and retrieval policy
- External dependencies:
  - main backend does not add LlamaIndex, Neo4j, vector DB, or graph DB dependencies
  - the external provider project may use LlamaIndex, Neo4j GraphRAG, Neo4j driver, vector stores, rerankers, and document parsers

External references:

- Borrow from LlamaIndex: ingestion pipeline, document/node abstraction, vector index / retriever / query engine composition, and agent tools as a RAG orchestration reference.
- Do not borrow from LlamaIndex: making MyPrivateAgent a LlamaIndex app or replacing runtime governance with LlamaIndex agent loops.
- Borrow from Neo4j GraphRAG: graph-backed retrievers, vector/fulltext/hybrid retrieval, Cypher-backed graph traversal, and graph evidence.
- Do not borrow from Neo4j GraphRAG: exposing graph DB internals directly to MyPrivateAgent or forcing every RAG source into a graph model.
