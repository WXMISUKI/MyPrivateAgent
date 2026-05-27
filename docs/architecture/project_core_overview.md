# Project Core Overview

> 本文是 MyPrivateAgent 的核心文档入口，面向维护者、垂域智能体开发者和外部前端接入方。它描述当前已经成立的架构事实，不替代更细的 runtime contract 文档。

## 1. 项目定位

MyPrivateAgent 的正式定位是企业级 `Agent Runtime Control Plane`。它不是某个单一业务 Agent，也不是 LangGraph、OpenAI Agents SDK、Qwen-Agent、DeerFlow 等外部框架的替代实现。

本项目负责稳定掌握这些控制面能力：

- Runtime Core：`query / run / child_run / event / approval / artifact / trace / audit` 等一等对象。
- Capability Layer：Tool、Skill、MCP、Memory、Command、Framework Adapter 的统一接入。
- Governance Layer：权限审批、策略、审计、运行回放、诊断、quality gate。
- Delivery Layer：FastAPI service API、Embedded SDK、Vue 治理台和未来外部业务前端。

成熟外部框架只能作为 execution adapter、lifecycle mapping、tool/handoff/tracing 参考进入项目。业务智能体资产应沉淀在本项目的垂域层，而不是绑定死在某个外部框架 API 上。

## 2. 核心分层

```text
External Frontend / Business System
  |
  | HTTP/SSE API
  v
Delivery Layer
  - FastAPI routers
  - Agent Server presets
  - Embedded SDK / AgentHarnessFacade
  - Runtime Surface / Governance Timeline
  |
  v
Governance Layer
  - Policy / Approval
  - Runtime Trace / Audit
  - Runtime Contract Gate
  - Doctor / Health / Quality Gate
  |
  v
Capability Layer
  - ToolRuntimeService
  - SkillRuntimeService
  - MCP Runtime
  - Memory / Command / Domain Agent / Adapter registry
  |
  v
Runtime Core
  - AgentRunContext / AgentState / AgentEvent
  - Query Control lifecycle
  - Scheduler / Child Run / Artifact
```

维护原则：

- 垂域业务不得直接写进 Runtime Core。
- 前端不得反向定义后端 runtime contract。
- 高风险工具必须进入 policy / approval / audit 链路。
- 新增外部框架 adapter 必须先定义 adapter boundary、promotion gate 和非目标。
- 新增垂域智能体应优先放在垂域目录，通过注册点接入 Tool / Skill / MCP / RAG / Policy。
- `backend/domain_agents/*/agent.yaml` 会通过只读 registry 进入 Runtime Surface 的 `domain_agent_registry`，用于资产盘点和治理可见性。

## 3. 当前主执行链

当前对话入口以 FastAPI chat API 为主：

```text
POST /api/chat
  -> ChatRequest
  -> conversation / history
  -> Orchestrator
  -> AgentHarness / scheduled orchestrator
  -> ToolRuntime / SkillRuntime / MCP / Policy / Approval
  -> SSE events
  -> message persistence / trace / audit
```

非流式调用可使用：

```text
POST /api/chat/non-stream
```

当前主链路更准确地说是 `AgentHarness + LangChain tool/model abstraction + Runtime/Governance services`。LangGraph 已作为 draft adapter / external pilot / 可控接入路径存在，但不应把主 chat 链路描述为完全由 LangGraph 图编排驱动。

## 4. 垂域智能体与核心框架的边界

垂域智能体负责：

- 角色定位和系统提示词。
- 业务工具和 ToolSpec。
- MCP server / capability 配置。
- RAG 数据源、索引、检索策略和引用输出。
- 垂域 skill、最佳实践、工作流说明。
- 权限、审批、风险策略。
- 业务前端需要的结构化卡片或响应字段。
- 垂域测试、评估集和演示数据。

核心框架负责：

- 统一执行生命周期。
- 统一工具执行、权限判断和审批。
- 统一 trace、audit、runtime profile 和 governance timeline。
- 统一模型/provider 接入与运行时降级。
- 统一 contract snapshot、quality gate 和诊断能力。

判断标准很简单：如果某段代码回答的是“这个业务怎么做”，放在垂域层；如果回答的是“任意智能体如何被执行、治理、审计和观测”，才属于核心框架。

## 5. 当前可用的对外接口

业务前端最小只需要接入下面几类接口。

### 5.1 认证

```http
POST /api/auth/login
POST /api/auth/guest
GET  /api/auth/me
```

所有受保护接口使用：

```http
Authorization: Bearer <token>
```

### 5.2 模型列表

```http
GET /api/models
```

用于前端展示可用模型、默认模型、provider 和可用状态。

### 5.3 统一智能体问答

```http
POST /api/chat
Content-Type: application/json
Accept: text/event-stream
```

请求体：

```json
{
  "conversation_id": 123,
  "message": "帮我查询这个订单为什么还没发货",
  "model_name": "default",
  "execution_context": {
    "agent_id": "ecommerce_support",
    "agent_role": "after_sales_specialist",
    "enable_main_chat_query_control_timeline": true
  }
}
```

当前 `execution_context` 是白名单输入，只允许稳定字段：

- `run_id`
- `run_kind`
- `agent_role`
- `agent_id`
- `enable_main_chat_query_control_timeline`

不要把任意业务 payload 塞进 `execution_context`。业务参数应放在用户问题、专用工具参数、MCP 请求或未来正式定义的垂域 request schema 中。

### 5.4 非流式问答

```http
POST /api/chat/non-stream
```

适合后台任务、简单表单问答或不需要实时输出的业务前端。返回：

```json
{
  "message": "回答内容",
  "conversation_id": 123
}
```

### 5.5 会话

```http
GET    /api/conversations
POST   /api/conversations
GET    /api/conversations/{conversation_id}
PATCH  /api/conversations/{conversation_id}
DELETE /api/conversations/{conversation_id}
```

用于业务前端维护会话列表、历史消息和标题。

### 5.6 权限审批

```http
GET  /api/permissions/pending
POST /api/permissions/approve
POST /api/permissions/deny
GET  /api/permissions/result/{request_id}
```

当工具或业务动作需要人工确认时，前端应展示审批卡片，而不是让模型绕过高风险操作。

### 5.7 能力与治理观察

```http
GET /api/runtime-profile
GET /api/runtime-profile/main-chat-query-detail
GET /api/runtime-profile/main-chat-query-history
GET /api/runtime-profile/channel-promotion-gate
GET /api/health
GET /api/doctor
```

业务前端通常不必全部接入；治理台、运维台或调试面板应优先接入这些只读 contract。

### 5.8 Skill / MCP 管理

```http
GET  /api/skills
POST /api/skills
GET  /api/mcp/servers
POST /api/mcp/servers
GET  /api/mcp/catalog
POST /api/mcp/servers/{server_name}/tools/{tool_name}/call
```

普通业务前端不建议直接调用 MCP tool call 接口绕过 agent loop。它更适合作为管理、调试和显式工具调用入口。

## 6. SSE 事件约定

`POST /api/chat` 返回 `text/event-stream`。前端应按事件 JSON 的 `type` 字段处理。

建议业务前端至少支持：

- `conversation_id`：后端确认或新建会话。
- `content`：模型输出片段。
- `status`：执行进度、心跳或阶段状态。
- `tool_result`：工具执行结果或工具观察。
- `approval_required`：需要人工审批。
- `structured_card`：可结构化展示的业务卡片。
- `done`：本轮完成，通常包含最终内容和 `message_id`。
- `error`：本轮失败。

实际事件可能随 runtime contract 演进扩展。前端应忽略未知事件类型，并保留原始 payload 方便排障。

## 7. 推荐阅读顺序

1. `docs/architecture/project_core_overview.md`
2. `docs/guides/domain_agent_development_guide.md`
3. `docs/architecture/current_architecture.md`
4. `docs/architecture/runtime_contracts.md`
5. `docs/architecture/extension_points.md`
6. `openspec/specs/agent-runtime-control-plane-positioning/spec.md`
7. `docs/roadmap/next_phase_hardening.md`
