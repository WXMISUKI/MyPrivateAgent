# 外部 Knowledge Provider / RAG 项目开发规范

## 1. 定位

外部 Knowledge Provider 是 MyPrivateAgent 的知识能力服务，不是主后端的一部分。它负责 RAG、知识图谱、Embedding、向量库、图数据库、文档解析、OCR、重排和索引生命周期；MyPrivateAgent 只负责注册、调用、健康检查、权限治理、审计证据和垂域绑定。

更完整的 RAG / GraphRAG provider 设计见 [external_rag_graphrag_provider_design.md](./external_rag_graphrag_provider_design.md)。当前推荐：文档型 RAG 的 provider 内部优先参考 LlamaIndex；实体、关系、路径、多跳查询和图增强检索优先参考 Neo4j GraphRAG。二者都只能作为外部 provider 的内部实现依赖，不进入 MyPrivateAgent 主后端。

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
      source_catalog.py
      document_loader.py
      chunker.py
      embedding_service.py
      vector_store.py
      llamaindex_rag_service.py
      retriever.py
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
      myprivateagent-integration.md
      api-contract.md
    tests/
```

主项目不要求外部服务必须使用 FastAPI，但接口合同必须稳定，返回 JSON，并提供健康检查。

实现建议：

- LlamaIndex 负责 provider 内部的文档加载、node parsing、索引、retriever、query engine、rerank/postprocessor 编排。
- Neo4j GraphRAG 负责 provider 内部的图谱检索、hybrid/vector/fulltext retrieval、Cypher traversal 和图证据规整。
- provider 对 MyPrivateAgent 只暴露本文定义的 HTTP JSON 合同，不暴露 LlamaIndex、Neo4j driver、GraphRAG retriever 等内部对象。

## 3. 最小 HTTP API

```http
GET  /health
GET  /api/capabilities
GET  /api/rag/sources
POST /api/rag/retrieve
GET  /api/graph/schemas
POST /api/graph/query
```

推荐额外提供 provider 侧 source catalog：

```http
GET /api/catalog
```

catalog 用于报告 `knowledge_base_id`、`graph_id`、状态、版本、索引新鲜度和 degraded 原因。MyPrivateAgent 的 `agent.yaml` 只声明允许绑定哪些 source，provider catalog 负责说明这些 source 是否真实存在且 ready。

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

MyPrivateAgent 仓库侧文档 RAG 试接结果可通过以下命令导出：

```powershell
python scripts/export_unified_knowledge_provider_trial_outcome.py `
  --provider-base-url http://127.0.0.1:8020 `
  --provider-readiness-path D:\AI\AIcode\unifiedKnowledgeRAG\docs\integration\myprivateagent-document-rag-trial-readiness\phase24-document-rag-trial-readiness.json
```

`--provider-readiness-path` 是可选输入，用于把 provider 侧 Phase 24 `decision=go` 的文档 RAG readiness closure 记录到 MyPrivateAgent 侧 trial outcome。它不能替代真实 HTTP 检查；provider 仍需单独启动并通过 health、manifest、preflight、source binding preview 和 RAG retrieve 检查。

当 provider 已经注册并通过 live HTTP 验收某个本地业务语料后，可以在 MyPrivateAgent 侧跑一个更聚焦的 caller-side corpus trial：

```powershell
python scripts/export_local_knowledge_provider_corpus_trial.py `
  --provider-base-url http://127.0.0.1:8020 `
  --source-id company_profile_2025_trial
```

该命令会调用 provider 的 `/api/rag/sources`、`/api/rag/sources/{source_id}/documents`、`/api/rag/retrieve` 和 `/api/rag/answer`，验证 answerable 问题、citation allowlist 和负控问题。输出位于：

```text
docs/integration/local-knowledge-provider-corpus-trial/local-knowledge-provider-corpus-trial.json
docs/integration/local-knowledge-provider-corpus-trial/local-knowledge-provider-corpus-trial.md
```

`decision=go` 只表示 MyPrivateAgent 已能通过本地 HTTP 合同使用该 source；它不创建 source-to-agent binding，不启用默认 `/api/chat` retrieval injection，不写审计或记忆，也不执行 GraphRAG。

当 provider 已经通过仓库侧 trial outcome 后，可以继续运行垂域 agent 显式 live trial，验证真实 document RAG evidence 是否能进入 MyPrivateAgent 的 grounded-answer 控制面链路：

```powershell
python backend/scripts/domain_agent_live_grounded_answer_trial.py `
  --agent-id ecommerce_support `
  --domain refund.policy `
  --query "退款政策是什么？" `
  --provider-base-url http://127.0.0.1:8020
```

这个 live trial 只使用 provider 的 document RAG retrieve 合同和 agent manifest 中声明的 `rag_sources`。它不启用默认 chat 检索注入，不创建绑定，不执行 GraphRAG，不写审计或记忆。

针对当前本地公司简介语料，推荐先跑最小公司简介垂域 agent 试验：

```powershell
python backend/scripts/domain_agent_live_grounded_answer_trial.py `
  --agent-id company_profile `
  --domain company.profile `
  --query "公司主营业务是什么？" `
  --provider-base-url http://127.0.0.1:8020 `
  --output-dir docs/integration/company-profile-domain-agent-live-trial
```

`company_profile` agent 只声明 `company_profile_2025_trial`，因此该命令用于验证“真实 agent manifest -> provider retrieve -> grounded-answer trial”的显式闭环。它仍然不启用默认 `/api/chat` retrieval injection，也不创建 source-to-agent binding。

## 7. agent.yaml 绑定

垂域 agent 通过 `capabilities.rag_sources` 和 `capabilities.graph_sources` 声明可见知识能力：

```yaml
capabilities:
  rag_sources:
    - refund_policy_docs
    - logistics_faq
  graph_sources:
    - ecommerce_order_graph
retrieval:
  mode: agentic
  default_top_k: 5
  require_citations: true
  graph_usage: relationship_questions_only
  fallback_policy: refuse_or_clarify_when_no_evidence
```

MyPrivateAgent 会把这些声明暴露到 Runtime Surface：

```text
rag_source_registry
knowledge_graph_registry
```

v1 registry 是只读治理面，不会自动创建索引、上传文档、编辑 ontology，也不会自动把检索结果注入 `/api/chat`。

`retrieval` 是垂域 Agent 的行为策略，不是 provider 数据配置。它用于描述该 Agent 何时检索、默认 top_k、是否强制引用、没有证据时如何处理，以及图谱只在什么问题类型下使用。provider 只负责按请求返回证据，不负责决定最终角色话术、拒答策略或审批策略。

## 8. 规格、实现、归档节奏

RAG / GraphRAG 能力按以下节奏推进：

```text
1. 规格
   OpenSpec proposal / design / specs / tasks 明确边界。

2. 实现
   先实现外部 provider 的 health、catalog、RAG retrieve；
   再实现 graph schemas、graph query；
   最后再考虑 MyPrivateAgent chat 自动注入。

3. 验证
   用 provider contract test、RAG smoke、graph smoke、
   MyPrivateAgent capability heartbeat 做最小验证。

4. 归档
   实现稳定后归档 OpenSpec change，
   把最终合同合入 canonical specs/docs。
```

## 9. 开发验收清单

- [ ] `/health` 可用，并能区分 ready / degraded / unreachable。
- [ ] `/api/rag/retrieve` 对测试文档返回稳定 `documents[*].citation`。
- [ ] `/api/graph/query` 对测试图谱返回 `graph_id / entities / relations / paths / evidence`。
- [ ] provider 不依赖 MyPrivateAgent 也能独立启动和自测。
- [ ] 向量库、图数据库、Embedding key、文档存储等敏感配置不写死在代码里。
- [ ] 大文档、OCR、重排、增量索引在 provider 内部治理，不进入 MyPrivateAgent 主后端。
