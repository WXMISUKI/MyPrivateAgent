# Phase B Capability Layer Design And Implementation Plan

> 目标读者：后续接手 `MyPrivateAgent` 通用智能体底座的开发者、评审者和垂域智能体接入方。

## 1. 背景

Phase A 已经把运行时主链路收口到 `run / child-run / event / approval / audit` 这条主线上，并修复了高风险工具审批等待在 `AgentHarness -> Orchestrator -> ChatService / Router / Scheduler` 真实链路中丢失状态的问题。

Phase B 的重点不再是继续修补单次对话链路，而是把当前分散在 `ToolRegistry / MCP Runtime / Skill Runtime / Memory / Command / RuntimeSurface` 中的能力面收口成统一的 `Capability Layer`。这层能力以后要支撑任意垂域智能体，包括反诈、评估、业务助手、流程自动化，以及未来可能接入的 LangGraph / DeepAgents-style / CrewAI-style adapter。

## 2. 设计目标

- 建立统一能力层契约，让工具、MCP capability、Skill、Memory、Command、外部框架 adapter 都有明确接入边界。
- 让运行时能够解释“当前有哪些能力可用、哪些不可用、为什么不可用、由谁提供、调用风险是什么”。
- 让前端治理台和未来 SDK 都能读取相同的能力层 contract，而不是分别猜测后端内部结构。
- 保持兼容演进，不推倒 Phase A 已经收口的运行时内核。

## 3. 总体分层

Phase B 在 Phase A 的 `Runtime Core` 外新增更清晰的 `Capability Layer`：

```text
Runtime Core
  AgentRun / ChildRun / AgentEvent / ApprovalRequest / Audit

Capability Layer
  Tool Runtime / MCP Runtime / Skill Runtime / Memory Runtime / Command Runtime / Adapter Runtime

Governance Layer
  Policy / Approval / Audit / Replay / Diagnostics / Adapter Health

Delivery Layer
  Embedded SDK / Runtime Service API / Governance Console
```

`Capability Layer` 的原则是：业务智能体只依赖平台契约，不直接依赖某个工具实现、MCP server 或第三方 agent framework。

## 4. 阶段拆分

## 实施状态（2026-05-11）

### 已完成

- Phase B-1 第一轮：已落地 `ToolRuntimeService` 最小契约，能够聚合 BaseTool、LangChain tool、ToolSpec、Doubao tool definition 与 MCP capability 概览。
- Runtime profile 已新增 `tool_runtime` 与 `adapter_health`，前端治理台 `RuntimeSurfacePanel` 已增加最小展示和缺省占位。
- 已补充后端与前端局部测试，锁定工具运行时 contract、adapter health contract、空配置降级、异常降级与前端展示。
- 已修复首轮评审发现的健康语义问题：ToolRegistry / MCP catalog 异常会暴露为 `unavailable / degraded`，不会伪装成 `not_configured / healthy`；BaseTool 的 `ask / deny / high_risk` 权限会计入高风险工具数。
- Phase B-2 第一轮：已新增 `ArtifactRef` 与 `ToolExecutionEnvelope` 最小协议，`AgentHarness` 会在 legacy tool result 字段旁追加 `tool_execution_envelope`。
- `orchestrator_service.persist_tool_artifact()` 已支持优先消费 envelope，并在缺失 envelope 时回退旧字段，避免破坏历史事件与现有 structured card 行为。
- Phase B-3 第一轮：已在 `McpRuntimeService` 内部拆出最小 `McpRuntimeRegistry / McpSessionManager / McpCapabilityRouter / McpRuntimeAudit` 边界，并新增 `phase-b-mcp-runtime-v1` contract。
- Runtime profile 已新增 `mcp_runtime`，前端 `RuntimeSurfacePanel` 已增加 MCP Runtime 合同卡片，展示整体状态、capability 数、enabled server 数与四个子组件健康。
- Phase B-4 第一轮：已新增 `SkillDefinition` 与 `MemoryEntry` 最小治理合同，Runtime profile 新增 `skill_contract`，`memory_contract` 新增 `memory_entries`。
- 前端 `RuntimeSurfacePanel` 已增加 `SkillDefinition 合同` 与 `MemoryEntry 合同` 展示，能看到 skill 版本、scope、selection reason、required capabilities，以及 memory source、confidence、retrieval reason。
- Phase B-5 第一轮：已将 slash command 升级为 `CommandDefinition` 合同，`command_contract` 新增 `phase-b-command-runtime-v1`、`command_definitions` 与 `embedded_sdk` 草案。
- 已新增 `EmbeddedAgentRuntimeSDK` 草案接口，声明 `create_run / stream_events / register_tool / submit_approval / resume_run` 五个嵌入式 SDK 入口，并明确标记为 draft 边界。
- Phase B-6 第一轮：已新增 `AgentFrameworkAdapter` SPI、`NoopFrameworkAdapter` 与 `AgentFrameworkAdapterRegistry`，为 LangGraph / DeepAgents-style / CrewAI-style 预留稳定适配位。
- `adapter_health` 已支持读取 framework adapter registry 的健康条目；未注册真实 adapter 时继续保留 `external_frameworks = not_configured` 占位。

### 验证记录

```powershell
python -m unittest tests.agent_framework.test_tool_runtime_service tests.agent_framework.test_runtime_surface_service -v
```

结果：`Ran 6 tests ... OK`

```powershell
python -m unittest tests.agent_framework.test_tool_runtime_service tests.agent_framework.test_runtime_surface_service tests.agent_framework.test_events tests.agent_framework.test_policy_engine_service tests.agent_framework.test_agent_hook_service tests.agent_framework.test_run_trace_service tests.agent_framework.test_scheduler_service tests.agent_framework.test_chat_service tests.agent_framework.test_approval_engine_service tests.agent_framework.test_orchestrator_service -v
```

结果：`Ran 94 tests ... OK`

```powershell
cmd /c npm test -- --run src/components/__tests__/RuntimeSurfacePanel.test.js
```

结果：`1 passed, 6 passed`

```powershell
cmd /c npm test -- --run src/components/__tests__/RuntimeSurfacePanel.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：`2 passed, 35 passed`

```powershell
python -m unittest tests.agent_framework.test_events tests.agent_framework.test_agent_harness_tool_envelope tests.agent_framework.test_orchestrator_service -v
```

结果：`Ran 22 tests ... OK`

```powershell
python -m unittest tests.agent_framework.test_tool_runtime_service tests.agent_framework.test_runtime_surface_service tests.agent_framework.test_events tests.agent_framework.test_agent_harness_tool_envelope tests.agent_framework.test_policy_engine_service tests.agent_framework.test_agent_hook_service tests.agent_framework.test_run_trace_service tests.agent_framework.test_scheduler_service tests.agent_framework.test_chat_service tests.agent_framework.test_approval_engine_service tests.agent_framework.test_orchestrator_service -v
```

结果：`Ran 97 tests ... OK`

```powershell
python -m unittest tests.agent_framework.test_mcp_runtime_service tests.agent_framework.test_runtime_surface_service -v
```

结果：`Ran 10 tests ... OK`

```powershell
cmd /c npm test -- --run src/components/__tests__/RuntimeSurfacePanel.test.js
```

结果：`1 passed, 7 passed`

```powershell
python -m unittest tests.agent_framework.test_mcp_runtime_service tests.agent_framework.test_mcp_session_service tests.agent_framework.test_mcp_registry_service tests.agent_framework.test_tool_runtime_service tests.agent_framework.test_runtime_surface_service tests.agent_framework.test_chat_service tests.agent_framework.test_scheduler_service -v
```

结果：`Ran 67 tests ... OK`

```powershell
cmd /c npm test -- --run src/components/__tests__/RuntimeSurfacePanel.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：`2 passed, 36 passed`

```powershell
python -m unittest tests.agent_framework.test_skill_runtime_service tests.agent_framework.test_agent_memory_service tests.agent_framework.test_runtime_surface_service -v
```

结果：`Ran 10 tests ... OK`

```powershell
cmd /c npm test -- --run src/components/__tests__/RuntimeSurfacePanel.test.js
```

结果：`1 passed, 8 passed`

```powershell
python -m unittest tests.agent_framework.test_skill_runtime_service tests.agent_framework.test_agent_memory_service tests.agent_framework.test_runtime_surface_service tests.agent_framework.test_orchestrator_service tests.agent_framework.test_chat_service tests.agent_framework.test_scheduler_service -v
```

结果：`Ran 64 tests ... OK`

```powershell
cmd /c npm test -- --run src/components/__tests__/RuntimeSurfacePanel.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：`2 passed, 37 passed`

```powershell
python -m unittest tests.agent_framework.test_command_registry_service tests.agent_framework.test_embedded_runtime_sdk -v
```

结果：`Ran 4 tests ... OK`

```powershell
cmd /c npm test -- --run src/components/__tests__/RuntimeSurfacePanel.test.js
```

结果：`1 passed, 9 passed`

```powershell
python -m unittest tests.agent_framework.test_command_registry_service tests.agent_framework.test_embedded_runtime_sdk tests.agent_framework.test_runtime_surface_service tests.agent_framework.test_skill_runtime_service tests.agent_framework.test_agent_memory_service tests.agent_framework.test_mcp_runtime_service tests.agent_framework.test_tool_runtime_service tests.agent_framework.test_chat_service tests.agent_framework.test_scheduler_service -v
```

结果：`Ran 69 tests ... OK`

```powershell
cmd /c npm test -- --run src/components/__tests__/RuntimeSurfacePanel.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：`2 passed, 38 passed`

```powershell
python -m unittest tests.agent_framework.test_framework_adapter_spi tests.agent_framework.test_tool_runtime_service -v
```

结果：`Ran 8 tests ... OK`

```powershell
python -m unittest tests.agent_framework.test_framework_adapter_spi tests.agent_framework.test_command_registry_service tests.agent_framework.test_embedded_runtime_sdk tests.agent_framework.test_runtime_surface_service tests.agent_framework.test_skill_runtime_service tests.agent_framework.test_agent_memory_service tests.agent_framework.test_mcp_runtime_service tests.agent_framework.test_tool_runtime_service tests.agent_framework.test_chat_service tests.agent_framework.test_scheduler_service -v
```

结果：`Ran 73 tests ... OK`

未纳入通过统计：`tests.agent_framework.test_mcp_router` 在当前本地环境导入 `backend.agent_server.app` 时缺少 `slowapi` 依赖，报错 `ModuleNotFoundError: No module named 'slowapi'`。该问题属于测试环境依赖缺口，本轮未修改 router 行为。

### 当前保留边界

- External Framework Adapter 仍是 `not_configured` 预留状态，本阶段只建立 SPI、健康契约和事件翻译边界，不接入 LangGraph / DeepAgents / CrewAI。
- MCP Runtime 仍未拆分为 registry/session/router/audit 四个正式模块，本轮只读取现有 capability catalog 作为健康面输入。
- Artifact Registry 仍未正式落库建模，本轮只定义可传递的 `ArtifactRef` 指针，不引入完整 registry 生命周期。
- Tool result 事件继续保留 `name / result / tool_execution / render_mode / card_schema / card` 等 legacy 字段，前端和历史链路暂不需要同步迁移。

### Phase B-1：Tool Runtime Contract 与 Adapter Health

#### 目标

先把最基础、最影响后续扩展的能力面立起来：工具运行时契约和 adapter 健康状态。

#### 改造范围

- 新增或等价实现 `ToolRuntimeService`
  - 聚合 `ToolRegistry`
  - 读取 `ToolSpec`
  - 识别 BaseTool、LangChain tool、Doubao tool definition
  - 汇总 MCP capability 概览
  - 输出统一 `tool_runtime_contract`
- 扩展 `RuntimeSurfaceService`
  - 增加 `tool_runtime`
  - 增加 `adapter_health`
- 前端 `RuntimeSurfacePanel`
  - 展示工具总数、LangChain 工具数、MCP capability 数、不可用 adapter 数
  - 展示 contract version 和降级状态
- 测试
  - 后端 contract 结构测试
  - 空 registry 降级测试
  - 前端字段展示和占位测试

#### 建议后端契约

```json
{
  "contract_version": "phase-b-tool-runtime-v1",
  "tool_runtime": {
    "total_tools": 0,
    "base_tool_count": 0,
    "langchain_tool_count": 0,
    "tool_spec_count": 0,
    "doubao_definition_count": 0,
    "mcp_capability_count": 0,
    "high_risk_tool_count": 0,
    "tools": []
  },
  "adapter_health": {
    "contract_version": "phase-b-adapter-health-v1",
    "overall_status": "healthy",
    "adapters": []
  }
}
```

#### 验收标准

- Runtime profile 可以稳定返回 `tool_runtime` 和 `adapter_health`。
- 即使没有 MCP server 或外部 adapter，也能返回空数组和 `not_configured` 状态，而不是异常。
- 前端治理台可以看到能力层最小健康面。
- 后续 Tool / MCP / Adapter 的新增不需要改前端字段结构。

#### 本阶段不做

- 不真正接入 LangGraph / DeepAgents / CrewAI。
- 不重构所有工具执行路径。
- 不做复杂 adapter 生命周期管理。

### Phase B-2：Tool Result Envelope 与 ArtifactRef 草案

#### 目标

把工具结果从“字符串结果 + 附带 metadata”升级为可治理的结果 envelope，为后续 Artifact Registry 做准备。

#### 改造范围

- 设计 `ToolExecutionEnvelope`
  - `tool_name`
  - `tool_call_id`
  - `status`
  - `result_text`
  - `render_mode`
  - `card_schema`
  - `artifact_ref`
  - `execution_metadata`
- 让 `AgentHarness` 生成工具结果时保留统一 envelope 字段。
- 让 `orchestrator_service.persist_tool_artifact()` 使用 envelope 字段，不再依赖松散字段。
- 文档中定义 `ArtifactRef` 最小结构，但不要求一次性落完整 registry。

#### 验收标准

- 工具结果可以解释来源、执行状态、渲染方式和 artifact 引用。
- 现有 structured card 行为不回退。
- 后续引入文件、截图、报告、证据链时不需要重写工具结果协议。

#### 实施状态（2026-05-11）

- 已完成 `backend.agent_framework.tools.ArtifactRef` 与 `ToolExecutionEnvelope`。
- 已完成 `AgentHarness._build_tool_event_payload()` envelope 输出。
- 已完成 `persist_tool_artifact()` envelope 优先读取与 legacy fallback。
- 已补充协议序列化、harness envelope 输出、artifact envelope 持久化测试。

### Phase B-3：MCP Runtime 拆分

#### 目标

把当前 MCP 能力从“能配置、能 probe、能调用”升级为更清晰的 runtime 子系统。

#### 改造范围

- 拆清四个职责：
  - `McpRegistry`
  - `McpSessionManager`
  - `McpCapabilityRouter`
  - `McpAudit`
- Adapter Health 接入 MCP server 状态。
- Runtime trace 记录 MCP handshake、tools/list、tools/call、fallback。
- Capability guard 使用统一 capability health。

#### 验收标准

- planner / scheduler 判断 capability 是否可用时，不再直接依赖零散 MCP 查询。
- MCP 调用失败能解释是 registry 缺失、server 不可用、session 失败、tool call 失败还是返回格式错误。
- 前端 MCP 管理面板和 RuntimeSurfacePanel 对同一健康数据达成一致。

#### 实施状态（2026-05-11）

- 已完成 `McpRuntimeRegistry`：封装 capability catalog 与 registry health。
- 已完成 `McpSessionManager`：封装 session execute 边界，保留最近错误用于健康诊断。
- 已完成 `McpCapabilityRouter`：封装 capability validation 与 adapter fallback，异常时返回 diagnostics 而不是直接冒泡。
- 已完成 `McpRuntimeAudit`：提供轻量内存审计缓冲，记录 registry sync、capability validation、session execute 与 adapter fallback。
- 已完成 `McpRuntimeService.build_runtime_contract()`，向 Runtime Surface 输出 `phase-b-mcp-runtime-v1`。
- 已完成前端 MCP Runtime 合同展示。

#### 当前保留边界

- MCP router / planner / scheduler 仍未全面迁移到 `mcp_runtime` contract，本轮先建立统一数据源和内部职责边界。
- MCP 审计仍是轻量内存 buffer，尚未接入持久化 run trace / audit store。
- MCP session 的真实协议实现沿用现有 `McpSessionService`，本轮不重写底层 JSON-RPC 调用。

### Phase B-4：SkillDefinition 与 MemoryEntry 治理化

#### 目标

让 skill 和 memory 从“提示词注入能力”升级为可解释、可治理、可版本化的运行时资产。

#### 改造范围

- 定义 `SkillDefinition`
  - `skill_id`
  - `name`
  - `version`
  - `scope`
  - `trigger_rules`
  - `required_capabilities`
  - `allowed_tools`
  - `model_preferences`
  - `selection_reason`
- 定义 `MemoryEntry`
  - `memory_id`
  - `source`
  - `scope`
  - `content`
  - `confidence`
  - `retrieval_reason`
  - `expires_at`
- Runtime profile 暴露 skill / memory contract。
- Governance timeline 能解释 skill/memory 选择原因。

#### 验收标准

- 运行时能解释“为什么激活了这个 skill”。
- 运行时能解释“为什么召回了这条 memory”。
- 垂域智能体可以声明自己依赖的 skill / memory 范围。

#### 实施状态（2026-05-11）

- 已完成 `SkillDefinition` 最小结构：
  - `skill_id`
  - `name`
  - `version`
  - `scope`
  - `trigger_rules`
  - `required_capabilities`
  - `allowed_tools`
  - `model_preferences`
  - `selection_reason`
- 已完成 `RuntimeSkillContext.metadata.skill_definitions`，用于解释本轮为什么激活某个 skill。
- 已完成 `SkillRuntimeService.build_runtime_contract()`，用于 Runtime Surface 暴露已注册启用 skill 定义。
- 已完成 `MemoryEntry` 最小结构：
  - `memory_id`
  - `source`
  - `scope`
  - `content`
  - `confidence`
  - `retrieval_reason`
  - `expires_at`
- 已完成 `AgentMemoryContext.memory_entries` 与 `memory_contract.memory_entries`。
- Runtime profile 已新增 `skill_contract`，并继续保留原 `memory_contract.loaded_layers / missing_layers / layer_order / active`。
- 前端治理台已展示 `SkillDefinition 合同` 与 `MemoryEntry 合同`。

#### 当前保留边界

- 本轮不改 Skill / Memory 数据库存储结构。
- 本轮不新增向量检索、embedding、长期用户记忆或过期策略，只给现有分层记忆补 `MemoryEntry` 解释合同。
- 本轮不改变 skill 选择算法，只把现有选择结果治理化、可解释化。

### Phase B-5：Command Runtime 与 SDK 接入草案

#### 目标

把 command 从前端交互功能升级为平台级执行入口，同时为 Embedded SDK 做最小边界设计。

#### 改造范围

- 设计 `CommandDefinition`
  - `command_id`
  - `name`
  - `description`
  - `parameters_schema`
  - `required_capabilities`
  - `permission_level`
  - `execution_handler`
- 让 slash command、治理台动作、未来 SDK 调用共享 command contract。
- 设计 Embedded SDK 最小接口：
  - `create_run`
  - `stream_events`
  - `register_tool`
  - `submit_approval`
  - `resume_run`

#### 验收标准

- 前端 command 不再只是页面跳转或 UI shortcut。
- 业务系统可以通过 SDK 或 Runtime Service 调用同一套平台能力。
- 每个 command 都有权限等级和能力依赖说明。

#### 实施状态（2026-05-11）

- 已完成 `CommandDefinition` 最小结构：
  - `command_id`
  - `name`
  - `description`
  - `parameters_schema`
  - `required_capabilities`
  - `permission_level`
  - `execution_handler`
- 已完成 `command_contract.contract_version = phase-b-command-runtime-v1`。
- 已完成 `command_contract.command_definitions`，并保留旧的 `framework_commands / conversation_commands / governance_commands / system_commands`。
- 已完成 `EmbeddedAgentRuntimeSDK` 草案接口与 `phase-b-embedded-sdk-v1` 合同。
- 前端治理台已展示 `CommandDefinition` 和 Embedded SDK draft methods。

#### 当前保留边界

- 本轮不实现真实 SDK 调用运行时，只建立可评审的嵌入式接口边界。
- 本轮不改变前端 slash command 的执行行为。
- `execution_handler` 仍是 handler 标识字符串，后续 Phase C 可再接入真正 command router / dispatcher。

### Phase B-6：External Framework Adapter SPI

#### 目标

为未来接入 LangGraph、DeepAgents-style、CrewAI-style 框架预留稳定适配位，但不在本阶段深度绑定某个外部框架。

#### 改造范围

- 定义 `AgentFrameworkAdapter` 接口
  - `adapter_id`
  - `framework_name`
  - `supported_run_kinds`
  - `capability_requirements`
  - `health_check`
  - `translate_input`
  - `stream_events`
  - `translate_output`
- Adapter 事件必须翻译为 Phase A 的 `AgentEvent`。
- Adapter 健康进入 `adapter_health`。

#### 验收标准

- 即使没有真正接外部框架，也能清楚知道 adapter 要实现什么。
- 外部框架产生的事件不会绕过审批、审计、trace。
- 垂域业务不直接依赖外部框架对象。

#### 实施状态（2026-05-11）

- 已完成 `AgentFrameworkAdapter` 抽象接口：
  - `adapter_id`
  - `framework_name`
  - `supported_run_kinds`
  - `capability_requirements`
  - `health_check`
  - `translate_input`
  - `stream_events`
  - `translate_output`
- 已完成 `FrameworkAdapterHealth`，并统一输出给 `adapter_health`。
- 已完成 `NoopFrameworkAdapter`，用于在未安装外部框架时声明 adapter 语义、能力要求和 `not_configured` 健康状态。
- 已完成 `AgentFrameworkAdapterRegistry`，支持注册 adapter、输出 `phase-b-framework-adapter-spi-v1` 合同、构建 health entries。
- 已完成 `ToolRuntimeService` 对 framework adapter registry 的接入：有注册 adapter 时展示真实条目，没有注册 adapter 时保留 `external_frameworks` 占位。
- `translate_output()` 已把外部框架输出翻译成 Phase A `AgentEvent` 字典，避免未来 adapter 绕过运行时事件标准。

#### 当前保留边界

- 本轮不安装、不绑定、不运行 LangGraph / DeepAgents / CrewAI。
- `stream_events()` 在 `NoopFrameworkAdapter` 中明确抛出 `NotImplementedError`，表示 SPI 已定义但外部执行器尚未启用。
- Adapter registry 当前为内存注册表，后续如果要支持插件发现、配置文件启用或租户隔离，需要进入 Phase C 再设计。

## 5. 推荐执行顺序

建议按以下顺序推进：

1. Phase B-1：Tool Runtime Contract 与 Adapter Health
2. Phase B-2：Tool Result Envelope 与 ArtifactRef 草案
3. Phase B-3：MCP Runtime 拆分
4. Phase B-4：SkillDefinition 与 MemoryEntry 治理化
5. Phase B-5：Command Runtime 与 SDK 接入草案
6. Phase B-6：External Framework Adapter SPI

原因是 `Tool Runtime Contract` 是所有能力治理的入口，`ArtifactRef` 是所有工具结果和证据链的基础，MCP 是当前已有能力里最需要健康治理的部分，Skill/Memory/Command/Adapter 再逐步上升为可治理资产。

## 6. 测试策略

### 后端测试

- `tests/agent_framework/test_tool_runtime_service.py`
- `tests/agent_framework/test_runtime_surface_service.py`
- `tests/agent_framework/test_chat_service.py`
- `tests/agent_framework/test_mcp_runtime_service.py`
- `tests/agent_framework/test_orchestrator_service.py`

每个阶段至少包含：

- 空配置降级测试
- 正常 contract 输出测试
- 运行时事件映射测试
- 回归测试，确保 Phase A 的 approval waiting 行为不被破坏

### 前端测试

- `frontend-vue/src/components/__tests__/RuntimeSurfacePanel.test.js`
- `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`

每个阶段至少包含：

- contract 字段展示
- 缺省字段占位
- 健康状态和风险提示

## 7. 风险与边界

### 主要风险

- 能力层抽象过大，导致第一阶段迟迟无法落地。
- adapter 健康状态与 MCP 健康状态重复建设。
- ToolSpec、MCP capability、SkillDefinition 三者之间边界不清。
- 前端过早产品化，反而把 contract 固死在 UI 形态上。

### 控制策略

- 每个阶段只新增一个主 contract。
- Runtime profile 只暴露稳定字段，不暴露内部实现细节。
- 前端只做治理窗口，不承载业务逻辑。
- 每次改造都保留兼容字段，避免破坏现有 Demo。

## 8. 当前下一步

Phase B 的能力层主干已经完成第一轮收口。Phase C-1 Contract Snapshot Guard 已在 `2026-05-11-phase-c-runtime-contract-hardening-plan.md` 中继续推进。

当前下一步建议：

- Phase C-2：选择一个低风险 adapter pilot，例如 LangGraph workflow adapter 或一个本地 fake adapter，验证 `translate_input -> stream_events -> translate_output -> AgentEvent -> audit/trace` 全链路。
