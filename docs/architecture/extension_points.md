# Extension Points

> 本文记录当前建议扩展点。新增垂域智能体或外部框架时，优先从这些 seam 接入。

## 1. 新增垂域智能体

推荐接入顺序：

1. 在 `backend/domain_agents/<agent_id>/` 下建立垂域目录。
2. 编写 `agent.yaml`，固定 `agent_id`、角色、能力和治理边界。
3. 定义垂域工具与 ToolSpec。
4. 注册到 tool runtime 或 command registry。
5. 需要知识/记忆时接入 skill / memory contract。
6. 需要外部系统时优先接入 MCP runtime。
7. 需要审批时接入 policy / approval seam。
8. 需要治理回放时写入 run trace 或 governance timeline。
9. 业务项目通过 service API 或 embedded SDK 接入。

推荐目录：

```text
backend/domain_agents/<agent_id>/
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

当前 `backend/domain_agents/` 是建议固定的垂域代码组织约定，自动 discovery / agent catalog 尚未作为运行时事实落地。新增自动发现或 `/api/agents/{agent_id}/chat` 包装接口前，必须先开 OpenSpec change。

当前业务前端统一入口：

```http
POST /api/chat
```

请求中使用白名单 `execution_context.agent_id` 与 `execution_context.agent_role` 表达垂域智能体身份。业务参数不应塞入未定义 execution context 字段，应通过用户问题、ToolSpec、MCP 或未来正式 request schema 承载。

不推荐：

- 直接改 `chat_service.py` 堆业务分支。
- 直接在前端治理台写领域规则。
- 绕过 Runtime Core 自己维护一套 run 状态。
- 绕过 agent loop 让业务前端直接决定工具调用。

## 2. 新增工具能力

主要 seam：

- `backend/harness/tool_registry.py`
- `backend/services/tool_runtime_service.py`
- `backend/services/command_registry_service.py`

最低要求：

- 工具名稳定。
- 参数 schema 明确。
- permission level 明确。
- risk level 可由后端归一化。
- 失败信息可被 trace / audit 记录。

治理要求：

- 高风险工具必须进入 approval / policy 体系。
- 工具执行结果不应直接污染最终回答，应经过 runtime event / tool result envelope。

## 3. 新增 MCP 能力

主要 seam：

- `backend/services/mcp_registry_service.py`
- `backend/services/mcp_runtime_service.py`
- `backend/services/mcp_adapter_service.py`
- `backend/services/mcp_session_service.py`

最低要求：

- MCP server / capability 有稳定 id。
- 连接失败应进入 runtime surface health。
- 运行异常应能被 doctor 或 governance timeline 定位。

## 4. 新增 Skill / Memory 能力

主要 seam：

- `backend/services/skill_runtime_service.py`
- `backend/services/agent_memory_service.py`
- `backend/agent_framework/memory.py`

最低要求：

- skill definition 可被 Runtime Surface 展示。
- memory entry 有来源、用途和生命周期说明。
- 注入上下文时必须可追踪，避免隐式污染 prompt。

## 5. 新增外部 Framework Adapter

主要 seam：

- `backend/agent_framework/framework_adapter_spi/base.py`
- `backend/agent_framework/framework_adapter_spi/health.py`
- `backend/agent_framework/framework_adapter_spi/registry.py`
- `backend/agent_framework/framework_adapters.py`
- `backend/services/framework_adapter_runtime_service.py`
- `backend/services/framework_adapter_external_pilot_service.py`
- `backend/services/framework_adapter_timeline_service.py`

新增 adapter 应实现：

- `health_check()`
- `can_execute()`
- `translate_input()`
- `stream_events()`
- `translate_output()`

推荐落点：

- adapter 自身放在 `backend/agent_framework/framework_adapter_spi/`。
- 外部 runtime client / translator 放在 `backend/agent_framework/external/` 或对应子目录。
- 诊断聚合复用 `FrameworkAdapterDiagnosticsService`。
- 时间线记录复用 `FrameworkAdapterTimelineRecorder`。

维护约束：

- `backend/agent_framework/framework_adapters.py` 继续作为 public facade。
- 新 adapter 必须出现在 adapter health contract 中。
- readiness、precheck、runtime execution、external pilot 不应混为一个开关。
- external pilot 必须分类错误类型，例如 configuration、connectivity、protocol、upstream runtime。

## 6. 新增治理策略

主要 seam：

- `backend/services/policy_engine_service.py`
- `backend/services/approval_engine_service.py`
- `backend/services/run_trace_service.py`
- `backend/services/runtime_contract_snapshot_service.py`

最低要求：

- 策略输入必须可序列化。
- 策略输出必须可审计。
- approval request 必须能回放。
- 阻塞原因必须有机器可读 code 和用户可读 detail。

## 7. 新增前端治理台视图

主要 seam：

- `frontend-vue/src/components/RuntimeSurfacePanel.vue`
- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
- `frontend-vue/src/api/index.js`

推荐方式：

- 后端先提供 contract。
- 前端按 contract 新增小组件。
- 父组件只做状态编排和路由跳转。
- 子组件负责展示和事件透出。

当前已拆出组件：

- `AdapterExternalPilotFailureSummary.vue`
- `AdapterHealthCard.vue`
- `AdapterPilotResultCard.vue`

后续建议继续拆：

- remediation action card
- snapshot command card

已拆出：

- `GovernanceTimelineFilters.vue`
- `GovernanceTimelineEventCard.vue`

## 8. 新增 Delivery 形态

当前 delivery 形态：

- FastAPI service API
- Vue governance console
- Embedded SDK draft

后续新增 delivery 时必须满足：

- 不复制 Runtime Core 状态机。
- 不绕过 Governance Layer。
- 不把领域业务写进公共 runtime contract。
- 能被 doctor / health / runtime surface 观察。
