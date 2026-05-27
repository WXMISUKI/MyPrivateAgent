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

当前代码还没有自动扫描 `backend/domain_agents/` 的通用 loader。因此这套目录是从现在开始建议固定的项目约定：垂域实现先落在这里，实际注册仍通过现有 Tool / Skill / MCP / Policy 服务接入。后续若要实现自动发现、启停和 agent catalog，应另开 OpenSpec change。

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
- `capabilities`：该 agent 允许使用的能力清单。
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

### Step 6：接入 RAG

RAG 不建议直接塞进主 chat router。推荐放在：

```text
rag/sources.yaml
rag/retrieval_policy.md
```

RAG 返回必须包含：

- source id
- title
- snippet
- confidence 或 score
- 可选 citation / url / document id

如果 RAG 结果会影响高风险动作，应让工具或 policy 再做一次权限判断。

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

业务产品前端可以只接 `POST /api/chat`。治理台、运维台、内部调试台再接这些只读接口。

## 6. 未来可选包装接口

如果后续多个外部项目前端都接入本后端，可以新增更明确的包装接口：

```http
POST /api/agents/{agent_id}/chat
GET  /api/agents
GET  /api/agents/{agent_id}
GET  /api/agents/{agent_id}/capabilities
```

但这些接口当前不是已实现事实。新增前必须开 OpenSpec change，至少说明：

- agent catalog 来源。
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

实现中：

- [ ] 工具有稳定名称和参数 schema。
- [ ] 高风险工具有审批策略。
- [ ] Skill 有触发条件、domain、agent_roles。
- [ ] MCP server 有稳定 id 和健康检查。
- [ ] RAG 返回 source / snippet / confidence。
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

