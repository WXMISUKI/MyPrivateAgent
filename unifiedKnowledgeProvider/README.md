# unifiedKnowledgeProvider

Independent Knowledge Provider for MyPrivateAgent.

This service is the knowledge data plane. MyPrivateAgent stays the runtime control plane and calls this service through provider-neutral HTTP contracts.

## Current Slice

This scaffold intentionally starts small:

- `GET /health`
- `GET /api/capabilities`
- `GET /api/catalog`
- `GET /api/rag/sources`
- `POST /api/rag/retrieve`
- `GET /api/graph/schemas`
- `POST /api/graph/query`

The current implementation uses an in-memory demo catalog so contracts can be validated before adding heavy dependencies. The intended production internals are:

- LlamaIndex for document RAG ingestion, indexing, retrieval, and reranking.
- Neo4j GraphRAG for graph-backed entity, relation, path, and hybrid retrieval.

## Run

```powershell
cd unifiedKnowledgeProvider
python -m uvicorn app.main:app --reload --port 8020
```

Configure MyPrivateAgent:

```env
ENABLE_KNOWLEDGE_CAPABILITY_PROVIDER=true
KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL=http://127.0.0.1:8020
KNOWLEDGE_CAPABILITY_PROVIDER_TIMEOUT_SECONDS=5
```

