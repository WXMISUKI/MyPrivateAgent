# 外部 Knowledge Provider / RAG 项目开发规范

## 1. 定位

外部 Knowledge Provider 是 MyPrivateAgent 的知识能力服务，不是主后端的一部分。它负责 RAG、知识图谱、Embedding、向量库、图数据库、文档解析、OCR、重排和索引生命周期；MyPrivateAgent 只负责注册、调用、健康检查、权限治理、审计证据和垂域绑定。

推荐项目命名：

```text
unifiedKnowledgeProvider
unifiedRAGProvider
```

不建议为每个知识库或图谱单独创建一个服务。更好的方式是一个 provider 管理多个：

```text
knowledge_base
collection
document_source
graph_namespace
ontology
entity_type / relation_type
```

## 2. 推荐目录结构

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
    services/
      document_loader.py
      chunker.py
      embedding_service.py
      vector_store.py
      retriever.py
      reranker.py
      graph_store.py
      ontology_registry.py
    providers/
      embeddings/
      vectorstores/
      graphstores/
    data/
      sources/
      indexes/
    docs/
      myprivateagent-integration.md
      api-contract.md
    tests/
```

主项目不要求外部服务必须使用 FastAPI，但接口合同必须稳定，返回 JSON，并提供健康检查。

## 3. 最小 HTTP API

```http
GET  /health
GET  /api/capabilities
GET  /api/rag/sources
POST /api/rag/retrieve
GET  /api/graph/schemas
POST /api/graph/query
```

`/health` 用于 MyPrivateAgent 的 capability heartbeat。服务不可用、索引未就绪、图数据库不可达时，应返回机器可读状态，不要只返回自由文本。

示例：

```json
{
  "status": "ok",
  "service": "unifiedKnowledgeProvider",
  "rag": {"status": "ready"},
  "graph": {"status": "ready"}
}
```

## 4. RAG 检索合同

请求：

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

响应必须带引用证据：

```json
{
  "ok": true,
  "result": {
    "answer_context": "用于注入模型的检索上下文",
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

约束：

- `answer_context` 是给模型使用的短上下文，不应返回整篇文档。
- `documents[*].citation` 必须稳定，便于 trace、审计和用户侧引用。
- 检索失败应返回 `ok=false` 和 `error.code`，不要返回 200 + 空字符串伪成功。
- 高风险业务动作不能只依赖 RAG 结果直接执行，仍要经过 MyPrivateAgent 的 policy / approval。

## 5. 知识图谱查询合同

知识图谱和 RAG 并列，不应被简单塞进 RAG。RAG 解决文档片段检索，知识图谱解决实体、关系、路径、约束和可解释推理。

请求：

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

响应：

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

约束：

- `graph_id` 必须稳定。
- `entities / relations / paths` 应使用可序列化对象，不返回数据库游标或内部对象。
- `evidence` 应说明图谱结果来源，例如导入批次、源文档、业务系统记录或 ontology 版本。
- 图谱 schema、ontology、entity type、relation type 应由外部 provider 管理版本。

## 6. MyPrivateAgent 环境变量

在 MyPrivateAgent `.env` 中启用外部知识能力：

```env
ENABLE_KNOWLEDGE_CAPABILITY_PROVIDER=true
KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL=http://127.0.0.1:8020
KNOWLEDGE_CAPABILITY_PROVIDER_TIMEOUT_SECONDS=5
```

启用后，`GET /api/capabilities` 会出现：

```text
knowledge.rag.retrieve
knowledge.graph.query
```

调用入口：

```http
POST /api/capabilities/knowledge.rag.retrieve/invoke
POST /api/capabilities/knowledge.graph.query/invoke
GET  /api/capabilities/heartbeat
```

## 7. agent.yaml 绑定

垂域 agent 通过 `capabilities.rag_sources` 和 `capabilities.graph_sources` 声明可见知识能力：

```yaml
capabilities:
  rag_sources:
    - refund_policy_docs
    - logistics_faq
  graph_sources:
    - ecommerce_order_graph
```

MyPrivateAgent 会把这些声明暴露到 Runtime Surface：

```text
rag_source_registry
knowledge_graph_registry
```

v1 registry 是只读治理面，不会自动创建索引、上传文档、编辑 ontology，也不会自动把检索结果注入 `/api/chat`。

## 8. 开发验收清单

- [ ] `/health` 可用，并能区分 ready / degraded / unreachable。
- [ ] `/api/rag/retrieve` 对测试文档返回稳定 `documents[*].citation`。
- [ ] `/api/graph/query` 对测试图谱返回 `graph_id / entities / relations / paths / evidence`。
- [ ] provider 不依赖 MyPrivateAgent 也能独立启动和自测。
- [ ] 向量库、图数据库、Embedding key、文档存储等敏感配置不写死在代码里。
- [ ] 大文档、OCR、重排、增量索引在 provider 内部治理，不进入 MyPrivateAgent 主后端。
