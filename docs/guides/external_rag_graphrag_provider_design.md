# External RAG / GraphRAG Provider Design

## 1. Positioning

The external knowledge provider is the knowledge data plane for MyPrivateAgent. MyPrivateAgent remains the runtime control plane.

```text
MyPrivateAgent
  owns agent identity, roles, prompts, capability binding, invocation envelope,
  policy, approval, trace, audit, and Runtime Surface governance.

unifiedKnowledgeProvider
  owns document ingestion, parsing, chunking, embedding, vector stores,
  reranking, graph stores, ontology, graph traversal, and index lifecycle.
```

This provider should usually be one independent service that manages many knowledge bases and graph namespaces. Do not create one provider service per vertical agent unless operations, compliance, or tenant isolation truly require it.

## 2. Framework Recommendation

### 2.1 Document RAG: LlamaIndex

Use LlamaIndex inside the provider for mainstream document RAG:

- data connectors and ingestion pipelines
- document / node parsing
- metadata extraction
- vector indexes and retrievers
- query engines
- reranker and postprocessor composition
- RAG evaluation utilities

MyPrivateAgent should not import LlamaIndex. The provider hides LlamaIndex internals behind the stable HTTP contract.

Good first use cases:

- internal enterprise FAQ
- policy and regulation Q&A
- product manuals
- customer service knowledge bases
- document-grounded assistant responses with citations

### 2.2 Knowledge Graph / GraphRAG: Neo4j GraphRAG

Use Neo4j GraphRAG when the question is relationship-heavy:

- entity lookup
- relation lookup
- path and multi-hop reasoning
- graph-constrained retrieval
- vector + fulltext + graph traversal hybrid retrieval
- explainable evidence from graph records or source documents

MyPrivateAgent should not import Neo4j or graph retriever classes. It calls `knowledge.graph.query` and receives provider-neutral `entities`, `relations`, `paths`, and `evidence`.

Good first use cases:

- customer-product-contract-risk relations
- order-logistics-refund relations
- person-location-case-event relations
- organization-system-permission dependency graphs

## 3. Recommended Project Layout

```text
unifiedKnowledgeProvider/
  app/
    main.py
    config.py
    routers/
      health.py
      capabilities.py
      rag.py
      graph.py
      sources.py
    models/
      contracts.py
      catalog.py
    services/
      source_catalog.py
      document_loader.py
      chunker.py
      embedding_service.py
      vector_store.py
      llamaindex_rag_service.py
      reranker.py
      graph_store.py
      neo4j_graphrag_service.py
      ontology_registry.py
    providers/
      embeddings/
      vectorstores/
      graphstores/
    data/
      sources/
      indexes/
    docs/
      api-contract.md
      myprivateagent-integration.md
    tests/
```

## 4. Source Catalog

The provider should maintain a source catalog. MyPrivateAgent declares what an agent is allowed to use; the provider reports whether those sources exist and are ready.

Example:

```yaml
knowledge_bases:
  - id: finance_product_docs
    type: rag
    status: ready
    owner: finance
    version: 2026-05-28
    embedding_model: text-embedding-3-large
    vector_store: qdrant
    freshness: daily

graphs:
  - id: customer_product_relation_graph
    type: graph
    status: ready
    owner: finance
    ontology_version: 2026-05
    graph_store: neo4j
```

`/api/capabilities` or a dedicated catalog endpoint should expose machine-readable readiness. Missing or degraded sources should not be hidden as free text.

## 5. HTTP API

Minimum API:

```http
GET  /health
GET  /api/capabilities
GET  /api/rag/sources
POST /api/rag/retrieve
GET  /api/graph/schemas
POST /api/graph/query
```

Optional lifecycle API for provider operators:

```http
POST /api/ingestion/jobs
GET  /api/ingestion/jobs/{job_id}
POST /api/indexes/{source_id}/rebuild
GET  /api/indexes/{source_id}/status
```

Do not expose lifecycle mutation endpoints through MyPrivateAgent until a separate governance design exists.

## 6. RAG Request and Response

Request:

```json
{
  "query": "客户三天未发货能否退款？",
  "knowledge_base_ids": ["refund_policy_docs"],
  "top_k": 5,
  "filters": {
    "agent_id": "ecommerce_support",
    "role": "after_sales_specialist"
  }
}
```

Response:

```json
{
  "ok": true,
  "result": {
    "answer_context": "用于注入模型的短上下文。",
    "documents": [
      {
        "source_id": "refund_policy_docs",
        "document_id": "refund_policy_2026",
        "title": "售后退款规则",
        "snippet": "超时未发货场景下...",
        "score": 0.86,
        "citation": "refund_policy_2026#section-3"
      }
    ]
  }
}
```

Rules:

- `answer_context` must be compact.
- `documents[*].citation` must be stable.
- Empty retrieval is valid, but it must be explicit.
- Provider failures must use structured `error.code` and `error.message`.

## 7. Graph Request and Response

Request:

```json
{
  "graph_id": "ecommerce_order_graph",
  "query": "订单 order-1 的售后关系",
  "entity_ids": ["order-1"],
  "relation_types": ["has_refund", "shipped_by"],
  "filters": {
    "agent_id": "ecommerce_support"
  }
}
```

Response:

```json
{
  "ok": true,
  "result": {
    "graph_id": "ecommerce_order_graph",
    "entities": [],
    "relations": [],
    "paths": [],
    "evidence": []
  }
}
```

Rules:

- Graph output must remain serializable JSON.
- Evidence should point to source documents, import batches, business system records, or ontology versions.
- Do not return database cursors, driver objects, or raw internal classes.

## 8. Domain Agent Binding

MyPrivateAgent domain agents bind to source ids, not provider internals.

```yaml
id: finance_customer_service
roles:
  - id: loan_consultant
    default: true

capabilities:
  rag_sources:
    - finance_product_docs
    - compliance_faq
  graph_sources:
    - customer_product_relation_graph

retrieval:
  mode: agentic
  default_top_k: 5
  require_citations: true
  graph_usage: relationship_questions_only
  fallback_policy: refuse_or_clarify_when_no_evidence
```

Prompts should describe how the agent uses evidence. The provider should not decide final persona, refusal style, approval policy, or business risk rules.

## 9. Implementation Cadence

Use the same cadence as other runtime capability work:

```text
1. Specification
   OpenSpec proposal, design, spec deltas, and tasks.

2. Implementation
   Provider scaffold, source catalog, health, RAG endpoint, graph endpoint,
   then MyPrivateAgent readiness visibility.

3. Verification
   Provider contract tests, smoke retrieval, graph query smoke, and
   MyPrivateAgent capability heartbeat.

4. Archive
   Merge decisions into canonical specs/docs and archive the OpenSpec change.
```

## 10. First Slice Recommendation

Build the first slice as a document-only RAG provider:

1. FastAPI provider skeleton.
2. `/health` and `/api/capabilities`.
3. static source catalog.
4. one small local document set.
5. LlamaIndex vector retrieval.
6. stable citations.
7. MyPrivateAgent invokes `knowledge.rag.retrieve`.

Then add graph:

1. Neo4j connection and test graph namespace.
2. `/api/graph/schemas`.
3. `/api/graph/query`.
4. graph evidence normalization.
5. hybrid query only after plain graph query is stable.
