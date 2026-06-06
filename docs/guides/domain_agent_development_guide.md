# Domain Agent Development Guide

> 本文说明如何基于 MyPrivateAgent 搭建垂域智能体。目标是让电商客服、售后、商品知识库、公安业务助手、内部运维助手等业务 Agent 能共享同一个 runtime / governance / capability 底座。

## 1. 总体原则

垂域智能体不是复制一套 Runtime Core，也不是在 `chat.py` 里堆业务分支。正确做法是把业务能力放到独立垂域层，通过标准 seam 接入现有运行时。

```text
domain agent
  = agent profile
  + prompts
  + tools / ToolSpec
  + MCP capabilities
  + skills
  + RAG
  + policy / approval
  + evaluation data

shared runtime
  = AgentHarness / Orchestrator
  + ToolRuntimeService
  + SkillRuntimeService
  + MCP Runtime
  + Policy / Approval
  + Trace / Audit / Runtime Profile
```

## 2. 推荐目录结构

建议为垂域智能体创建专门目录：

```text
backend/domain_agents/
  ecommerce_support/
    agent.yaml
    README.md
    prompts/
      system.md
      workflows.md
    tools/
      order_tools.py
      refund_tools.py
      tool_specs.py
    skills/
      refund_policy.SKILL.md
      logistics_diagnosis.SKILL.md
    mcp/
      servers.yaml
    rag/
      sources.yaml
      retrieval_policy.md
    policies/
      approval_policy.yaml
      risk_rules.md
    tests/
      test_ecommerce_support_tools.py
      fixtures/

  public_security/
    agent.yaml
    README.md
    prompts/
    tools/
    skills/
    mcp/
    rag/
    policies/
    tests/
```

当前代码已经提供只读 `DomainAgentRegistryService`，会扫描 `backend/domain_agents/*/agent.yaml` 或 `agent.yml` 并在 Runtime Surface 的 `domain_agent_registry` 中暴露 agent 身份、角色、能力和治理边界。这个 registry 只登记资产，不导入垂域代码，不自动注册 Tool / Skill / MCP / RAG，也不改变主 chat 执行路径。

另外，当前也提供了最小只读 catalog API：`GET /api/agents`。它复用 registry 作为真源，但返回更窄的 API-facing contract，便于调用方或治理工具读取 agent 列表，而不需要依赖整个 Runtime Surface payload。每个 agent entry 还会包含 `capability_linkage`，用于只读展示 manifest 声明的 Tool、Skill、MCP server 或 MCP capability 是否能在当前能力层被识别；`rag_sources` 和 `graph_sources` 仍只作为外部 Knowledge Provider 声明，不在 MyPrivateAgent 内部执行检查。

因此垂域实现仍通过现有 Tool / Skill / MCP / Policy 服务接入；`agent.yaml` 是资产目录和治理可见性的真源。后续若要实现启停、编辑、自动注册、默认 chat 检索注入或最终回答生成，仍应另开 OpenSpec change。

## 3. agent.yaml 建议格式

`agent.yaml` 用于描述垂域智能体的稳定身份和能力边界。

```yaml
id: ecommerce_support
name: 电商售后客服智能体
version: 0.1.0
description: 面向订单、物流、退款和售后工单的垂域智能体

roles:
  - id: after_sales_specialist
    name: 售后专员
    default: true
  - id: logistics_specialist
    name: 物流诊断专员

runtime:
  default_model: default
  enable_query_control_timeline: true
  response_mode: stream

capabilities:
  tools:
    - order.lookup
    - logistics.trace
    - refund.create_request
  skills:
    - refund_policy
    - logistics_diagnosis
  mcp_servers:
    - ecommerce_order_mcp
  rag_sources:
    - refund_policy_docs
    - logistics_faq
  graph_sources:
    - ecommerce_order_graph
grounding_policy:
  require_citations: true
  allow_ungrounded: false
  must_use_knowledge_for_domains:
    - refund.policy
    - logistics.diagnosis
  fallback_policy: refuse_or_clarify_when_no_evidence
  source_acl_mode: agent_manifest

governance:
  approval_required:
    - refund.create_request
    - order.modify_address
  audit_tags:
    - ecommerce
    - after_sales
```

字段含义：

- `id`：前端请求中的 `execution_context.agent_id`。
- `roles.id`：前端请求中的 `execution_context.agent_role`。
- `capabilities`：该 agent 允许使用的能力清单，其中 `rag_sources` 和 `graph_sources` 会进入 Runtime Surface 的只读知识 registry。
- `grounding_policy`：该 agent 的知识行为策略，描述是否强制引用、是否允许无证据回答、哪些业务域必须使用知识、没有证据时如何 fallback，以及 source ACL 语义。
- `retrieval`：兼容旧写法的知识检索行为策略输入，后续应迁移到 `grounding_policy`。
- `governance.approval_required`：必须进入审批链路的高风险动作。

## 4. 垂域开发步骤

### Step 1：定义 Agent 身份

先回答四个问题：

- 这个 agent 服务哪个业务域？
- 它默认扮演什么角色？
- 它能调用哪些工具、MCP、skill 和知识库？
- 哪些动作必须审批或只允许给出建议？

结果写入：

```text
backend/domain_agents/<agent_id>/agent.yaml
backend/domain_agents/<agent_id>/README.md
```

### Step 2：编写垂域 Prompt

推荐拆成：

```text
prompts/system.md
prompts/workflows.md
prompts/refusal_and_risk.md
```

Prompt 只描述业务边界和行为规范，不要写运行时实现细节，例如“直接调用某 Python 函数”。工具调用能力应由 ToolSpec、Skill、MCP 和 runtime policy 提供。

当前 PromptOps v1 是轻量只读合同：后端会把现有 `SystemPrompt` 记录映射成版本化 PromptOps contract，但不会改变默认 chat prompt 注入行为。旧 prompt 不需要迁移；没有版本 tag 时默认视为 `version = "1"`。

如需让 prompt 进入治理可见性，可以在 tags 中使用以下约定：

```text
version:2
status:review
owner:agent-team
grounding_policy:ecommerce_support
eval_set:refund-policy-eval
approval:pending
rollout:manual
rollback_target:1
```

模板变量使用 mustache 风格占位符，例如：

```text
请根据订单 {{order_id}} 和客户 {{customer_id}} 判断退款策略。
```

`GET /api/learnings/prompts/contract` 会把这些占位符提取为 `variables_schema`，供后续 eval、审批和回滚治理使用。现阶段这些字段只用于可见性和试运行准备，不代表 prompt 已进入自动审批、灰度或强制 activation 流程。

### Step 2.1：理解 MemoryOps 边界

当前 MemoryOps v1 是只读生命周期合同，用于解释记忆相关数据的来源和状态，不负责自动写入长期记忆。

推荐区分：

- `runtime_instruction_memory`：来自 `GLOBAL_AGENT.md`、`PROJECT_AGENT.md` 等运行时指令层。
- `conversation_summary`：来自 `/compact` 或 conversation compact API 的持久摘要。
- `hot_session_state`：会话内临时状态，当前仅报告 posture。
- `long_term_memory`：长期用户/团队/领域记忆，当前尚未实现专用存储。
- `retrieved_knowledge_evidence`：外部 RAG/GraphRAG 检索证据，不等同于 durable memory。

`GET /api/admin/memoryops/contract` 可以查看当前 MemoryOps registry。传入 `conversation_id` 时，如果该会话已有 compact summary，会额外返回 `conversation_summary` entry。

重要边界：

- RAG 检索结果不会默认写入长期记忆。
- compact summary 不删除原始 messages。
- MemoryOps registry 当前是 `visibility_only`，不会改变 `/api/chat`、prompt injection 或 context packing 行为。

### Step 2.2：补充多轮 Eval 场景

当垂域 agent 的 prompt、grounding、memory、tool 或 refusal 行为会影响生产回答时，应补充轻量多轮 eval 场景。

场景文件放在：

```text
docs/evals/multiturn/
```

最小结构：

```json
{
  "id": "refund_policy_no_evidence",
  "turns": [
    {"role": "user", "content": "这个订单能退款吗？"}
  ],
  "evidence": {
    "grounding": {
      "require_citations": true,
      "evidence_available": false
    },
    "response": {
      "behavior": "refuse_or_clarify"
    }
  },
  "assertions": {
    "grounding": {
      "require_citations": true,
      "evidence_available": false
    },
    "response": {
      "behavior": "refuse_or_clarify"
    }
  }
}
```

当前 eval gate 是 deterministic contract check：它只检查 scenario evidence 是否满足断言，不调用模型、不执行工具、不访问 RAG provider，也不改变默认 chat 行为。后续默认 RAG 注入、prompt rollout 或 memory injection promotion 前，应先让代表性场景通过。

### Step 3：定义 Tool 和 ToolSpec

工具应放在：

```text
backend/domain_agents/<agent_id>/tools/
```

最低要求：

- 工具名稳定，例如 `order.lookup`。
- 参数 schema 明确。
- 权限级别明确，例如 `read_only / ask / high_risk / deny`。
- 错误码稳定，可被 trace / audit 记录。
- 返回结果可序列化，不直接返回数据库 session、文件句柄或 Python callable。

接入点：

- `backend/harness/tool_registry.py`
- `backend/services/tool_runtime_service.py`

### Step 4：定义 Skill

垂域 skill 应描述“这个 agent 何时该使用某种业务策略”。示例：

```markdown
---
name: refund_policy
description: 处理退款、退货、仅退款、超时未发货等售后政策判断
domain: ecommerce_support
agent_roles:
  - after_sales_specialist
activation_mode: auto
priority: 10
---

当用户询问退款、退货、物流异常导致的赔付时，先判断订单状态、发货状态、签收状态和售后时效。
高风险动作只生成建议和审批请求，不直接执行退款。
```

接入点：

- `backend/services/skill_runtime_service.py`
- `GET /api/skills`
- `POST /api/skills`

### Step 5：接入 MCP

当能力需要连接外部系统，优先考虑 MCP：

```text
mcp/servers.yaml
```

适合 MCP 的能力：

- 订单系统查询。
- 工单系统查询或创建。
- 企业知识库检索。
- 地图、GIS、公安业务系统能力。
- 可被多个垂域复用的工具能力。

接入点：

- `backend/services/mcp_registry_service.py`
- `backend/services/mcp_runtime_service.py`
- `backend/services/mcp_adapter_service.py`
- `GET /api/mcp/catalog`

### Step 6：接入 RAG 与知识图谱

RAG 不建议直接塞进主 chat router。推荐放在：

```text
rag/sources.yaml
rag/retrieval_policy.md
```

如果业务需要实体、关系、路径或 ontology 约束，推荐额外声明知识图谱：

```yaml
capabilities:
  graph_sources:
    - ecommerce_order_graph
```

RAG 返回必须包含：

- source id
- title
- snippet
- confidence 或 score
- 可选 citation / url / document id

如果 RAG 结果会影响高风险动作，应让工具或 policy 再做一次权限判断。

知识图谱返回必须包含 `graph_id / entities / relations / paths / evidence`。RAG 与知识图谱都应由外部 Knowledge Provider 管理，MyPrivateAgent 只保存 `agent.yaml` 绑定、capability 注册、health、invoke 和审计证据。外部项目开发规范见 [external_rag_provider_development.md](./external_rag_provider_development.md)。

更完整的外部 provider 设计见 [external_rag_graphrag_provider_design.md](./external_rag_graphrag_provider_design.md)。当前推荐：

- 文档型知识问答、制度问答、产品手册、内部资料检索，优先用 LlamaIndex 作为外部 provider 内部 RAG 编排框架。
- 实体关系、多跳路径、ontology 约束、关系型证据查询，优先用 Neo4j GraphRAG 作为外部 provider 内部图谱检索实现。
- 两者都不进入 MyPrivateAgent 主后端；主项目只通过 `knowledge.rag.retrieve` 和 `knowledge.graph.query` 调用 provider。

推荐在 `agent.yaml` 里显式记录 grounding policy，`retrieval` 仅作为兼容输入：

```yaml
grounding_policy:
  require_citations: true
  allow_ungrounded: false
  must_use_knowledge_for_domains:
    - refund.policy
    - logistics.diagnosis
  fallback_policy: refuse_or_clarify_when_no_evidence
  source_acl_mode: agent_manifest
```

推荐在 `rag/retrieval_policy.md` 里补充自然语言规则：

```text
- 只有当用户问题需要内部政策、产品资料或历史文档证据时才检索 RAG。
- 没有 citation 时不得声称来自知识库。
- 涉及实体关系、路径、归属、依赖时优先查询 graph source。
- 高风险业务动作必须经过 policy / approval，不因 RAG 命中而自动执行。
```

### Grounding policy readiness

`domain_agent_registry` 会把每个 agent 的 `grounding_policy` 和 `grounding_policy_status` 一并暴露出来。这个状态是治理可见、非阻断的：

- `ready`：字段完整且可直接解释。
- `unknown`：策略存在，但 provider catalog / source readiness 仍未确认。
- `degraded`：策略字段缺失或值不合法。

在这个阶段，`grounding_policy_status.enforcement` 始终应保持 `visibility_only`，默认 `/api/chat` 的检索注入仍然保持关闭。

### Grounding decision gate

`AgentGroundingPolicyService` 提供最小只读决策闸门，用来判断已经返回的 evidence pack 是否允许进入某个垂域 agent 的 grounded answer path。这个服务只读取 domain agent registry 和调用方传入的 evidence pack，不调用 Knowledge Provider、不创建 source binding、不写审计记录，也不改变默认 `/api/chat`。

决策结果只允许三类：

- `allowed`：policy 与 evidence pack 均满足要求，调用方只能使用返回的 `citation_allowlist`。
- `blocked`：缺少 citation、证据不足、未知 agent、GraphRAG 尚未 promotion 等硬阻断。
- `review`：policy 未声明或允许无证据回答，但仍需要调用方显式处理。

后续若要让默认 `/api/chat` 自动注入 RAG，必须另开 behavior promotion change，并通过代表性多轮 eval gate。

### Grounded answer promotion gate

`DomainAgentGroundedAnswerPromotionService` 是进入真实试接前的最小聚合闸门。它把 provider trial、grounding decision、PromptOps version、MemoryOps boundary 和 multi-turn eval 结果汇总成 `go / review / blocked`，用于回答“这个 domain agent 是否可以进入 grounded answer repo-side trial”。

这个 gate 仍然是只读能力：

- 不调用 RAG / GraphRAG provider。
- 不生成最终回答。
- 不创建 source-to-agent binding。
- 不写长期记忆或审计事件。
- 不改变默认 `/api/chat` retrieval injection。

推荐判断口径：

- `go`：provider ready、grounding allowed、prompt version 可见、retrieved evidence 仍是 explicit-only、multi-turn eval passed。
- `review`：policy 或 PromptOps / MemoryOps 证据还需要人工确认，但没有硬阻断。
- `blocked`：provider 不可用、citation 缺失、grounding blocked、multi-turn eval failed/blocked，或 GraphRAG 尚未 promotion。

如果该 gate 返回 `go`，下一步也只是进入调用方 repo-side grounded answer trial；默认聊天路径自动 RAG 注入仍需要单独的 behavior promotion change。

### Grounded answer trial surface

`DomainAgentGroundedAnswerTrialService` 和 `POST /api/domain-agents/{agent_id}/grounded-answer-trial` 提供显式 opt-in 的试运行入口。调用方可以把已经拿到的 provider evidence、evidence pack、PromptOps、MemoryOps 和 multi-turn eval evidence 传入，接口会返回统一 trial report。

请求示例：

```json
{
  "domain": "refund.policy",
  "query": "退款政策是什么？",
  "evidence_pack": {
    "status": "answerable",
    "allowed_citations": ["refund_policy_2026#section-3"]
  },
  "provider_evidence": {"status": "trial_passed"},
  "promptops_evidence": {"prompt_key": "refund_policy", "version": "2", "status": "active"},
  "memoryops_evidence": {"retrieved_knowledge_promotion_mode": "explicit_only"},
  "eval_evidence": {"overall_status": "passed"}
}
```

返回的 `trial.trial_status` 只允许：

- `go`：可以进入调用方 repo-side grounded answer trial。
- `review`：还需要人工确认 PromptOps、MemoryOps 或 grounding policy warning。
- `blocked`：provider、citation、grounding、eval 或 GraphRAG 边界存在硬阻断。

这个 endpoint 仍然不是默认聊天执行入口：它不调用 provider、不生成最终回答、不写 audit / trace / memory、不创建 source binding，也不改变 `/api/chat` 的默认检索注入。

### Grounded answer package dry-run

`DomainAgentGroundedAnswerPackageService` 和 `POST /api/domain-agents/{agent_id}/grounded-answer-package-dry-run` 提供下一层只读能力：把 trial report 或同一批 evidence 输入整理成一个可供后续 answer composer 消费的 `grounded_answer_package`。

它的目标不是生成回答，而是准备一个受控输入包，通常包含：

- `package_status`: `ready / review / blocked`
- `allowed_citations`
- `evidence_items`
- `prompt_binding`
- `memory_boundary`
- `fallback_policy`
- `blockers / warnings`

这个 package dry-run 仍然保持严格边界：

- 不调用 LLM。
- 不调用 provider。
- 不调用 `/api/chat`。
- 不生成最终回答。
- 不写 memory / audit / trace / source binding。

只有当 trial report 是 `go` 时，package 才能进入 `ready`。如果 trial 还是 `review` 或 `blocked`，package 也必须保持同级收口，而不能越级进入回答阶段。

### Grounded answer composition trial

`DomainAgentGroundedAnswerCompositionTrialService` 和 `POST /api/domain-agents/{agent_id}/grounded-answer-composition-trial` 是这条 grounded-answer 控制面链路的最后一层受控试运行。

当外部 `unifiedKnowledgeRAG` provider 已在本地启动后，可以运行一个显式 live trial，把真实 provider document RAG evidence 接入同一条 grounded-answer 控制面链路：

```powershell
python backend/scripts/domain_agent_live_grounded_answer_trial.py `
  --agent-id ecommerce_support `
  --domain refund.policy `
  --query "退款政策是什么？" `
  --provider-base-url http://127.0.0.1:8020 `
  --pretty
```

该命令会读取 `agent.yaml` 中声明的 `rag_sources`，调用 provider 的 `/api/rag/retrieve`，再把返回的 `evidence_pack` 交给 grounded-answer trial、package dry-run 和 composition trial。它仍然是显式 opt-in 的只读试运行：不调用默认 `/api/chat`，不写 memory/audit/trace，不创建 source-to-agent binding，不执行 GraphRAG，也不推广 retrieval runtime defaults。

它会消费 `grounded_answer_package`，并返回：

- `composition_status`: `ready / review / blocked`
- `answer_preview`
- `used_citations`
- `composition_policy`
- `fallback_behavior`

这里的 `answer_preview` 仍然是 deterministic preview，不是默认聊天结果，也不是 live LLM answer。当前边界依然保持：

- 不调用 provider
- 不调用 LLM
- 不调用 `/api/chat`
- 不写 memory / audit / trace / source binding
- 不提升 GraphRAG

推荐把这一层视为当前 domain-agent grounded-answer 分支的收尾层。做完 composition trial 后，后续若要继续推进，就应单独评估是否真的有必要进入默认 `/api/chat` retrieval injection promotion，而不是沿着这条线继续拆更多局部切片。

### Repo-side minimal integration trial pack

当前推荐把 repo-side 试接收口为一条最小链路，而不是继续追加新的控制面层：

```text
GET /api/agents
  -> inspect capability_linkage
  -> POST /api/domain-agents/{agent_id}/grounded-answer-trial
  -> POST /api/domain-agents/{agent_id}/grounded-answer-package-dry-run
  -> POST /api/domain-agents/{agent_id}/grounded-answer-composition-trial
```

如果调用方只想在仓库内先做 smoke，可以运行：

```powershell
python backend/scripts/domain_agent_trial_smoke.py --payload docs/examples/domain_agent_trial_payload.json --pretty
```

该脚本会读取最小 evidence payload，复用现有 trial / package / composition service，并输出统一 `overall_status`：

- `go`：可以进入调用方 repo-side grounded answer trial。
- `review`：没有硬阻断，但需要先确认 warnings。
- `blocked`：存在 provider、citation、grounding、eval 或 GraphRAG blocker。

该 trial pack 仍然保持只读：不启动服务、不调用 provider、不调用 LLM、不调用 `/api/chat`、不写 memory / audit / trace、不创建 source binding，也不改变默认聊天检索注入。

### Step 7：定义审批和风险策略

高风险动作必须进入审批链路：

```text
policies/approval_policy.yaml
policies/risk_rules.md
```

示例：

```yaml
rules:
  - action: refund.create_request
    permission_level: high_risk
    approval_required: true
    reason: 涉及退款金额和售后责任认定
  - action: order.lookup
    permission_level: read_only
    approval_required: false
```

接入点：

- `backend/services/policy_engine_service.py`
- `backend/services/approval_engine_service.py`
- `GET /api/permissions/pending`
- `POST /api/permissions/approve`
- `POST /api/permissions/deny`

## 5. 统一前端对接接口

### 5.1 当前推荐主接口

垂域业务前端统一调用：

```http
POST /api/chat
Authorization: Bearer <token>
Content-Type: application/json
Accept: text/event-stream
```

请求：

```json
{
  "conversation_id": 123,
  "message": "客户说订单三天没发货，帮我判断该怎么处理",
  "model_name": "default",
  "execution_context": {
    "agent_id": "ecommerce_support",
    "agent_role": "after_sales_specialist",
    "enable_main_chat_query_control_timeline": true
  }
}
```

当前 `execution_context.agent_id` 和 `execution_context.agent_role` 是垂域路由语义的推荐承载字段。后端可以据此选择 prompt、skill、tool、MCP 和 policy。

### 5.2 非流式接口

```http
POST /api/chat/non-stream
```

适合不需要实时输出的场景，例如后台自动分析、表单提交后的单次建议生成。

### 5.3 前端必须处理的事件

```text
conversation_id
content
status
tool_result
approval_required
structured_card
done
error
```

处理建议：

- `content`：追加到当前回答。
- `status`：展示轻量进度，不要作为最终答案。
- `tool_result`：可折叠展示工具执行证据。
- `approval_required`：展示审批卡片，调用审批接口。
- `structured_card`：按业务卡片渲染。
- `done`：停止 loading，保存 `message_id` 用于反馈。
- `error`：展示错误提示，并保留 trace id 或原始 payload。

### 5.4 审批交互

```http
GET  /api/permissions/pending
POST /api/permissions/approve
POST /api/permissions/deny
GET  /api/permissions/result/{request_id}
```

业务前端不要让用户在聊天框里输入“我批准了”来绕过审批。审批必须走正式接口，便于审计和回放。

### 5.5 治理和调试接口

```http
GET /api/runtime-profile
GET /api/runtime-profile/main-chat-query-detail
GET /api/runtime-profile/main-chat-query-history
GET /api/runtime-profile/channel-promotion-gate
GET /api/health
GET /api/doctor
```

业务产品前端可以只接 `POST /api/chat`。治理台、运维台、内部调试台再接这些只读接口。其中 `GET /api/runtime-profile` 的 `domain_agent_registry` 字段是当前垂域 agent 资产列表的统一只读来源。

## 6. 已有和未来可选包装接口

当前已实现：

```http
GET /api/agents
```

该接口只提供 agent catalog 和 capability linkage readiness，不启停 agent，不自动注册能力，不调用 provider，也不改变 `/api/chat` 行为。

如果后续多个外部项目前端都接入本后端，可以继续新增更明确的包装接口：

```http
POST /api/agents/{agent_id}/chat
GET  /api/agents/{agent_id}
GET  /api/agents/{agent_id}/capabilities
```

除 `GET /api/agents` 外，这些接口当前不是已实现事实。新增前必须开 OpenSpec change，至少说明：

- agent catalog 来源，默认应复用 `domain_agent_registry`。
- `agent_id` 到 prompt / skill / tool / MCP / policy 的解析规则。
- 与现有 `/api/chat` 的关系。
- 是否仍复用 `ChatRequest`。
- SSE 事件是否完全兼容。
- 权限、审计、runtime profile 如何落地。

默认建议先用 `/api/chat + execution_context.agent_id` 跑通垂域闭环，再决定是否新增包装接口。

## 7. 垂域 Agent 开发清单

开始前：

- [ ] 创建 `backend/domain_agents/<agent_id>/`。
- [ ] 写 `agent.yaml` 和 `README.md`。
- [ ] 明确默认 role 和可选 role。
- [ ] 明确工具、MCP、skill、RAG、审批范围。
- [ ] 确认 `GET /api/runtime-profile` 中的 `domain_agent_registry` 能看到该 agent。

实现中：

- [ ] 工具有稳定名称和参数 schema。
- [ ] 高风险工具有审批策略。
- [ ] Skill 有触发条件、domain、agent_roles。
- [ ] MCP server 有稳定 id 和健康检查。
- [ ] RAG 返回 source / snippet / confidence / citation。
- [ ] 知识图谱声明 graph source，并返回 entity / relation / path / evidence。
- [ ] 前端只调用统一 chat API，不绕过 agent loop。

验证时：

- [ ] 只读问题能返回普通回答。
- [ ] 工具问题能产生 tool observation。
- [ ] 高风险动作能触发 approval_required。
- [ ] 审批通过后能继续执行或给出明确结果。
- [ ] runtime profile / trace 能看到 agent_id 或 query evidence。
- [ ] unknown SSE event 不会拖垮前端。

## 8. 示例：电商售后 Agent

```text
backend/domain_agents/ecommerce_support/
  agent.yaml
  prompts/system.md
  tools/order_tools.py
  tools/refund_tools.py
  skills/refund_policy.SKILL.md
  mcp/servers.yaml
  rag/sources.yaml
  policies/approval_policy.yaml
```

前端请求：

```json
{
  "message": "订单 202605270001 三天没发货，客户要求退款，应该怎么处理？",
  "execution_context": {
    "agent_id": "ecommerce_support",
    "agent_role": "after_sales_specialist",
    "enable_main_chat_query_control_timeline": true
  }
}
```

期望流程：

```text
用户问题
  -> ecommerce_support prompt / skill 生效
  -> order.lookup 查询订单
  -> logistics.trace 查询物流
  -> refund_policy 判断售后规则
  -> refund.create_request 命中 high_risk
  -> approval_required
  -> 用户审批
  -> 工具继续执行或生成处理建议
  -> done 返回前端
  -> trace / audit 可回放
```

## 9. 不推荐做法

- 不要为每个垂域复制一份 `backend/agent_framework`。
- 不要直接修改 `backend/routers/chat.py` 增加业务 if/else。
- 不要让前端直接决定使用哪个工具。
- 不要让 MCP tool call 接口替代 agent loop。
- 不要把订单号、警情编号等业务字段硬塞进 `execution_context` 未定义字段。
- 不要让外部框架原生 payload 成为前端主 contract。
