# Provider Capability Gap Assessment - 2026-06-03

> 本文用于评估 MyPrivateAgent 在 provider 能力、上下文、提示词、多模态、RAG/GraphRAG 和企业级 Agent 平台能力上的当前成熟度。它不替代 `next_phase_hardening.md`，而是为后续 OpenSpec 切片排序提供依据。

## 1. 外部成熟平台共性

参考 OpenAI Agents SDK、Microsoft Copilot Studio、Amazon Bedrock Agents、Google Vertex AI / Agent Search、LangGraph、Dify、n8n、CrewAI 的公开文档后，成熟 Agent 平台通常具备以下能力面：

- 模型与工具编排：工具、Action Group、OpenAPI/Lambda/API action、MCP 或插件注册。
- 知识与 grounding：企业知识源、Web search、RAG、引用、权限过滤、禁止未 grounded 回答的策略。
- 多 Agent / handoff：子 agent、角色路由、handoff、workflow/chatflow。
- 记忆与状态：短期会话记忆、长期记忆、checkpoint、thread、resume、time-travel/debug。
- PromptOps：提示词模板、变量、版本、灰度、测试、审批、回滚。
- Guardrails：输入护栏、输出护栏、工具护栏、安全策略、PII/敏感数据处理。
- 可观测与评估：trace/span、工具调用记录、多轮测试、数据集评估、回归基线、线上监控。
- 多模态与文档：ASR/TTS、OCR、layout、VLM、文件解析、artifact、异步 job。
- 运营治理：provider 健康、凭据、租户/权限、配额、成本、SLA、失败重试。

## 2. 当前项目判断

### 2.1 已经比较扎实的部分

- Control-plane 定位清晰：主项目负责 Runtime Core、Capability Runtime、Policy/Approval、Trace/Audit、Runtime Surface；重模型和重数据面外置 provider。
- Capability Runtime 已有统一注册、health、heartbeat、invoke、test、stream 边界。
- ASR/TTS 已明确推荐外部 `unifiedTTSandASR`，legacy local voice 被降级为 disabled-by-default fallback。
- 文档能力已经完成规格收口：`document.ocr.extract`、`document.layout.parse`、`document.vlm.parse`、`document.vlm.parse.async`、document artifact、document ingestion workflow 都已进入 canonical `unified-capability-runtime` spec。
- Query/Run Read Model 成熟度较高：`main_chat` query detail/history/workspace 已有 dedicated read model 边界，且有 channel promotion gate 防止过早扩散。
- Runtime governance 明显强于一般轻量框架：approval、runtime contract gate、snapshot、quality gate、trace/audit、child-executor gate 等已有大量规格和测试沉淀。
- 多轮对话已经有基础：数据库消息历史进入模型输入，`ChatContextPackingService` 做 token budget packing，`ChatContextCompactService` 支持持久化 `/compact` 摘要。

### 2.2 可用但仍偏薄的部分

- RAG/GraphRAG：MyPrivateAgent 侧 provider-neutral contract 已成立，`unifiedKnowledgeProvider` 有接口 scaffold；但当前 provider 仍是静态 demo catalog，不是生产级 LlamaIndex/Neo4j GraphRAG 数据面。
- Prompt 管理：`/prompts` CRUD 已存在，但还不是企业级 PromptOps。缺少版本、变量 schema、绑定场景、审批、评测、灰度、回滚、prompt injection 测试。
- Memory：`AgentMemoryService` 当前更像分层指令/记忆文件加载器；长期语义记忆、用户偏好记忆、事实冲突处理、TTL、隐私删除、检索证据仍未形成正式 MemoryOps。
- 多模态模型：文档 VLM 已接入 contract，但图像理解、视频理解、音频理解、图像生成、视频生成还没有统一 capability family。
- Workflow/Agent 编排：已有 subagent、scheduler、external adapter、child-executor 规格；但还不是面向业务用户的 workflow/chatflow/action designer，也没有通用任务队列和长任务编排面。
- 评估体系：quality gate 很强，但偏 runtime contract；缺少 prompt/RAG/多轮对话/工具选择的场景化 eval dataset 与回归报告。
- Provider 运维：已有 heartbeat/readiness，但凭据、租户隔离、限流、成本预算、provider fallback、SLA 指标还没有统一 provider ops contract。

## 3. 关键差距矩阵

| 能力域 | 当前状态 | 差距 | 建议优先级 |
|---|---|---|---|
| RAG 数据面 | contract/scaffold ready | 缺真实 ingestion、embedding、vector store、rerank、citation eval | P0 |
| GraphRAG 数据面 | contract/scaffold ready | 缺 Neo4j schema、entity/relation/path 查询、图证据质量门禁 | P0 |
| Grounding 策略 | citation contract exists | 缺按 agent/场景控制 `must_use_knowledge`、`allow_ungrounded`、fallback/refuse 策略 | P0 |
| PromptOps | basic CRUD | 缺 version/template variables/eval/approval/rollout/rollback | P1 |
| MemoryOps | layered instruction loader + chat compact | 缺 long-term semantic memory、hot session state、memory lifecycle、冲突/过期治理 | P1 |
| Multi-turn eval | query history/read model exists | 缺多轮场景测试与 CI 回归 | P1 |
| Provider Ops | heartbeat/test exists | 缺 credential/profile、tenant、quota、cost、fallback、SLA contract | P1 |
| Multimodal expansion | document OCR/Layout/VLM ready | 缺 image/video/audio family 的统一 taxonomy | P2 |
| Workflow builder | runtime primitives exist | 缺业务可配置 workflow/chatflow/action graph | P2 |
| Enterprise connectors | MCP/ToolRuntime exists | 缺常用连接器规范：DB、OpenAPI、HTTP、邮件、日历、IM、SharePoint/Drive、CRM/工单 | P2 |

## 4. 推荐下一阶段切片

### P0-A: 完成 `plan-external-rag-graphrag-provider`

继续现有 active change，不另开大题。

最小目标：

- 等外部 RAG / GraphRAG provider 项目达到 readiness 后，再从 MyPrivateAgent 做 caller-side 对接。
- 将外部 provider 从静态 demo 推进到第一版 LlamaIndex-backed document RAG；这一步属于外部 provider 数据面，不应落进 MyPrivateAgent 主后端。
- 保持 HTTP contract 不变。
- 明确 graph 仍可先保持 schema/discovery 或 structured `GRAPH_NOT_IMPLEMENTED`，除非外部 provider 同时具备可验证 Neo4j GraphRAG。

对接前置条件：

- provider `/health` 稳定。
- provider `/api/capabilities` 稳定。
- provider `/api/catalog` 或等价 source catalog 稳定。
- provider `/api/rag/sources` 与 `/api/rag/retrieve` 稳定。
- provider `/api/graph/schemas` 稳定。
- provider `/api/graph/query` 要么真实可用，要么返回结构化 `GRAPH_NOT_IMPLEMENTED`，不能伪成功。
- MyPrivateAgent `.env` 可通过 `KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL` 指向该 provider。

建议验证：

```powershell
cmd /c openspec validate plan-external-rag-graphrag-provider --strict
cmd /c openspec validate --all --strict
```

如实现 provider 代码，再补 provider 侧 focused pytest。

### P0-B: Grounding Policy Contract

新开 OpenSpec change，建议名：

```text
add-agent-grounding-policy-contract
```

目标：

- 在 domain agent manifest 或 capability policy 中表达：
  - `require_citations`
  - `allow_ungrounded`
  - `must_use_knowledge_for_domains`
  - `fallback_policy`
  - `source_acl_mode`
- 先进入 Runtime Surface 和 provider readiness，不直接改默认 chat 自动检索。

### P1-A: PromptOps Contract

新开 OpenSpec change，建议名：

```text
add-promptops-versioned-prompt-contract
```

目标：

- 把现有 `/prompts` 从 CRUD 升级为 contract：
  - prompt key/version/status
  - template variables schema
  - owner/area/tags
  - eval set binding
  - approval/activation history
  - rollback metadata
- 前端先做治理台只读/最小编辑，不做复杂 prompt studio。

### P1-B: MemoryOps Contract

新开 OpenSpec change，建议名：

```text
add-agent-memoryops-lifecycle-contract
```

目标：

- 区分：
  - hot session state
  - conversation summary
  - long-term user/team/domain memory
  - retrieved knowledge evidence
- 定义 memory entry 的来源、TTL、置信度、删除/过期、冲突处理、注入 trace。

### P1-C: Multi-turn Evaluation Gate

新开 OpenSpec change，建议名：

```text
add-multiturn-agent-evaluation-gate
```

目标：

- 用小型 YAML/JSON scenario 描述多轮对话、预期工具调用、预期 grounding、预期拒答。
- 将 prompt/RAG/多轮上下文改动纳入 focused regression，而不是只靠单轮 smoke。

## 5. 当前结论

当前最值得继续做的不是再扩 UI，也不是把所有外部能力塞进主后端，而是沿 provider-first 路线补齐三层：

1. 真实知识 provider 数据面：RAG/GraphRAG。
2. 可治理的 agent behavior：grounding policy、PromptOps、MemoryOps。
3. 可验证的企业交付面：multi-turn eval、provider ops、cost/quota/SLA。

短期建议仍然守住 control-plane/data-plane 边界：MyPrivateAgent 不引入向量库、图数据库、OCR/VLM 模型依赖；主项目只收口 contract、policy、trace、audit、read model 和治理可见性。

## 5.1 稳定 OpenSpec 任务队列

本路线已固化到 OpenSpec change `stabilize-provider-capability-roadmap`，归档后进入 canonical `provider-capability-roadmap` spec。后续开发默认按以下顺序拆分：

| 顺序 | Change 名称 | 目的 | 是否依赖外部 provider |
|---|---|---|---|
| P0-A | `plan-external-rag-graphrag-provider` | 完成外部 RAG / GraphRAG provider readiness 与 caller-side smoke | 是 |
| P0-B | `add-agent-grounding-policy-contract` | 定义 agent knowledge grounding、引用、未命中 fallback、ACL 策略 | 部分依赖 |
| P1-A | `add-promptops-versioned-prompt-contract` | 将 `/prompts` 升级为版本化 PromptOps 合同 | 否 |
| P1-B | `add-agent-memoryops-lifecycle-contract` | 定义长期记忆、hot session、summary、证据注入生命周期 | 否 |
| P1-C | `add-multiturn-agent-evaluation-gate` | 用多轮场景验证 prompt/RAG/context 行为 | 部分依赖 |
| P2 | later focused changes | 多模态 taxonomy、workflow/chatflow、企业 connector、provider ops | 视场景 |

当前判断：外部 RAG / GraphRAG 项目仍在开发时，MyPrivateAgent 不需要等待空转，但只应推进两类工作：

- 不依赖 provider 的规格工作：Grounding Policy、PromptOps、MemoryOps、多轮 eval 的 proposal/design/spec。
- 依赖 provider 的对接工作：等外部 provider readiness 后再做 source readiness、RAG retrieve smoke、GraphRAG smoke 和默认行为 promotion。

## 6. External References

- OpenAI Agents SDK tracing: https://github.com/openai/openai-agents-python/blob/main/docs/tracing.md
- OpenAI Agents SDK guardrails: https://openai.github.io/openai-agents-python/guardrails/
- Microsoft Copilot Studio generative orchestration: https://learn.microsoft.com/en-us/microsoft-copilot-studio/faqs-generative-orchestration
- Microsoft Copilot Studio knowledge sources: https://learn.microsoft.com/en-us/microsoft-copilot-studio/knowledge-copilot-studio
- Amazon Bedrock Agents: https://docs.aws.amazon.com/bedrock/latest/userguide/agents-how.html
- Google Vertex AI grounding with Agent Search: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/grounding/grounding-with-vertex-ai-search
- LangGraph persistence: https://docs.langchain.com/oss/python/langgraph/persistence
- Dify Workflow & Chatflow: https://docs.dify.ai/en/use-dify/build/workflow-chatflow
- n8n AI memory: https://docs.n8n.io/advanced-ai/examples/understand-memory/
- CrewAI docs: https://docs.crewai.com/
