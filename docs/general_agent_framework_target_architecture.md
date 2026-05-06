# 通用智能体框架目标架构设计稿

## 1. 文档定位

本文档给出 `MyPrivateAgent` 下一阶段目标架构，重点解决以下问题：

- 运行时内核应该由哪些一等对象组成
- planner、scheduler、subagent、MCP、memory、skill、command 分别位于哪一层
- 现有模块如何演进到目标架构
- 第一批代码改造应该落在哪些模块

配套总方案见：

- [general_agent_framework_enterprise_plan.md](./general_agent_framework_enterprise_plan.md)

## 2. 目标架构原则

### 2.1 分层明确

目标架构按“接口层 -> 编排层 -> 运行时层 -> 治理层 -> 能力层 -> 基础设施层”组织。

### 2.2 运行时一等对象明确

下列对象必须是一等对象，而不是分散 metadata：

- `AgentRun`
- `ChildRun`
- `AgentEvent`
- `ApprovalRequest`
- `ArtifactRef`
- `MemoryEntry`
- `SkillDefinition`

### 2.3 执行链可回放

任何一次执行都应该可以通过：

- `run_id`
- `parent_run_id`
- `event stream`
- `artifact refs`

恢复出主要执行路径。

### 2.4 治理能力内建

权限、审批、策略、追踪、告警必须是内建能力，而不是新增功能后的补丁。

## 3. 目标架构全景

```text
+--------------------------------------------------------------+
| Interface Layer                                              |
| FastAPI Routers / Vue UI / Future CLI / External API         |
+--------------------------------------------------------------+
| Orchestration Layer                                          |
| ChatService / PlannerService / CommandExecutor               |
+--------------------------------------------------------------+
| Runtime Core Layer                                           |
| AgentRunManager / Scheduler / ChildRunManager / EventBus     |
+--------------------------------------------------------------+
| Governance Layer                                             |
| PolicyEngine / ApprovalEngine / RunTrace / Audit / Doctor    |
+--------------------------------------------------------------+
| Capability Layer                                             |
| Tool Runtime / Skill Runtime / MCP Runtime / Memory Runtime  |
+--------------------------------------------------------------+
| Infrastructure Layer                                         |
| DB / Config / Logging / Metrics / Queue / File Storage       |
+--------------------------------------------------------------+
```

## 4. 目标模块职责

## 4.1 Interface Layer

### 职责

- 暴露稳定 API
- 接收用户输入与操作指令
- 展示运行态、治理态、审计态

### 对应当前模块

- `backend/routers/*`
- `frontend-vue/src/views/*`
- `frontend-vue/src/components/*`

### 演进要求

- 接口层不直接拼装运行时细节
- 尽量只消费 `Run DTO`、`Timeline DTO`、`Runtime Profile DTO`

## 4.2 Orchestration Layer

### 职责

- 将“用户请求”转换为“运行时执行意图”
- 选择 planner / direct run / command / governance action
- 对上提供简单服务接口，对下依赖运行时内核

### 目标模块

- `ChatService`
- `PlannerService`
- `CommandExecutionService`（建议新增）

### 当前问题

- 部分执行控制仍嵌在 chat path 内
- planner 与 scheduler 的职责边界仍不够清晰

### 改造目标

- `ChatService` 只负责发起 run
- `PlannerService` 只负责 durable plan
- `SchedulerService` 只负责 runtime execution graph

## 4.3 Runtime Core Layer

这是后续改造的核心。

### 一等对象

#### AgentRun

表示一次主执行链。

建议最小结构：

```text
AgentRun
- run_id
- conversation_id
- user_id
- parent_run_id
- run_kind
- state
- stop_reason
- model_name
- provider_name
- started_at
- ended_at
- context_snapshot_ref
- metadata
```

建议 `run_kind`：

- `chat`
- `planner`
- `child`
- `background`
- `governance`

#### ChildRun

表示从父执行链派生出的子执行单元。

建议最小结构：

```text
ChildRun
- child_run_id
- parent_run_id
- role
- execution_mode
- state
- assigned_tools
- required_capabilities
- approval_mode
- worktree_ref
- started_at
- ended_at
- summary
- error
```

建议 `execution_mode`：

- `inline`
- `background`
- `worktree`
- `remote`

#### AgentEvent

所有运行时事件统一使用一个协议族，而不是各域单独扩展。

建议结构：

```text
AgentEvent
- event_id
- run_id
- parent_run_id
- event_type
- state
- source
- severity
- iteration
- summary
- detail
- payload
- created_at
```

建议 `source`：

- `runtime`
- `planner`
- `scheduler`
- `subagent`
- `tool`
- `permission`
- `hook`
- `mcp`
- `memory`
- `skill`
- `command`

#### ArtifactRef

统一表示执行中产生的工件。

建议结构：

```text
ArtifactRef
- artifact_id
- run_id
- artifact_type
- title
- storage_kind
- path_or_uri
- mime_type
- metadata
```

建议 `artifact_type`：

- `merged_output`
- `tool_output`
- `diff`
- `report`
- `snapshot`
- `worktree`

### 运行时状态机

建议统一主状态机：

```text
INIT
-> PLANNING
-> GENERATING
-> TOOL_CALLING
-> WAITING_APPROVAL
-> OBSERVING
-> MERGING
-> FINALIZING
-> DONE
-> FAILED
-> ABORTED
```

说明：

- 当前 `backend/agent_framework/runtime.py` 已有基础状态机
- 下一步建议补 `PLANNING`、`MERGING`、`WAITING_APPROVAL`
- `WAITING_PERMISSION` 建议向更通用的 `WAITING_APPROVAL` 演进

## 4.4 Governance Layer

### 目标职责

- 做策略判定
- 管审批与阻断
- 管运行轨迹
- 管审计导出
- 管诊断与整改建议

### 目标子模块

#### PolicyEngine

建议从当前 `policy_engine_service.py` 演进为三层策略：

1. `tool policy`
2. `child run policy`
3. `provider / capability policy`

建议输入：

```text
PolicyInput
- actor
- run_context
- action_type
- action_payload
- resource_scope
```

建议输出：

```text
PolicyDecision
- allowed
- decision_type
- reason_code
- human_message
- machine_payload
- requires_approval
```

#### ApprovalEngine

建议新增审批对象，而不是把所有等待行为都视为权限等待。

建议结构：

```text
ApprovalRequest
- approval_id
- run_id
- target_type
- target_name
- risk_level
- reason_code
- status
- requested_at
- resolved_at
- resolver
- resolution_note
```

建议 `target_type`：

- `tool`
- `child_run`
- `provider_switch`
- `worktree_remove`
- `external_action`

#### RunTrace / Audit

建议区分：

- `run_trace`：面向运行态和回放
- `audit_log`：面向治理与合规

两者可以共用事件源，但查询视角应不同。

## 4.5 Capability Layer

### Tool Runtime

负责：

- 工具注册
- 工具模式校验
- 工具执行
- 工具结果标准化

建议演进方向：

- 统一 tool schema
- 统一 tool result envelope
- 统一 tool execution metrics

### Skill Runtime

建议定义 `SkillDefinition`：

```text
SkillDefinition
- skill_id
- name
- description
- when_to_use
- allowed_tools
- model_override
- effort
- context_mode
- trigger_paths
- prompt_template
- enabled
- source
```

建议 `context_mode`：

- `inline`
- `fork`
- `background`

### MCP Runtime

建议正式拆分为：

- `McpRegistry`
- `McpSessionManager`
- `McpCapabilityRouter`
- `McpAuditTrail`

这样可以避免 registry、session、runtime 调用状态继续混在一起。

### Memory Runtime

建议从当前分层文件加载演进为：

```text
MemoryRuntime
- static_instruction_layers
- project_memory_index
- user_feedback_memory
- runtime_recall
- memory_validation
```

建议 `MemoryEntry`：

```text
MemoryEntry
- memory_id
- type
- name
- description
- content
- source
- scope
- created_at
- updated_at
- enabled
- confidence
```

建议 `type`：

- `user`
- `feedback`
- `project`
- `reference`

## 4.6 Infrastructure Layer

### 目标职责

- 配置管理
- 数据持久化
- 日志与指标
- 文件与工件存储
- 队列与后台执行

### 建议演进项

1. 统一 Python 版本与构建基线
2. 统一配置层级
3. 提升日志和指标标准化程度
4. 为后台执行和 worktree 留出工件存储边界

## 5. 关键边界设计

## 5.1 Planner 与 Scheduler 的边界

建议明确：

- `Planner` 管“目标和计划”
- `Scheduler` 管“执行和运行”

换句话说：

- planner 负责 durable work graph
- scheduler 负责 runtime execution graph

不建议再让 planner 同时承担 child execution 生命周期管理。

## 5.2 Run Trace 与 Planner Trace 的边界

建议明确：

- `run trace` 归属于 `run`
- planner item 只保留引用和聚合视图

这样可以支持：

- 非 planner 场景也有统一 trace
- 一个 planner item 关联多个 run
- 后续增加 background run 和 governance run 不会变形

## 5.3 Permission 与 Approval 的边界

建议明确：

- `permission` 更偏规则判断
- `approval` 更偏人工或策略确认流程

当前 `WAITING_PERMISSION` 语义偏窄，企业级改造时建议上升为更通用审批模型。

## 5.4 Static Memory 与 Runtime Memory 的边界

建议明确：

- `GLOBAL_AGENT.md / PROJECT_AGENT.md` 是静态规则层
- `MemoryEntry` 是运行时可召回长期上下文

两者都属于 memory，但不是同一类对象，不应混为一个加载过程。

## 6. 建议的目录演进

不要求一次性重构完成，但建议逐步往以下组织方式演进：

```text
backend/
  runtime/
    models/
    services/
    events/
    approvals/
  governance/
    policy/
    audit/
    diagnostics/
  capabilities/
    tools/
    skills/
    mcp/
    memory/
  orchestration/
    chat/
    planner/
    commands/
```

短期内不必大搬迁，但建议先通过新增模块和清晰 import 边界过渡。

## 7. 第一批改造建议落点

如果下一阶段开始动代码，建议优先修改以下模块：

- `backend/agent_framework/runtime.py`
- `backend/agent_framework/events.py`
- `backend/services/run_trace_service.py`
- `backend/services/scheduler_service.py`
- `backend/services/chat_service.py`
- `backend/services/policy_engine_service.py`

第一批目标不是做完全部目标架构，而是先把下面三件事做成：

1. 统一 `run` 概念
2. 统一 `event` 概念
3. 统一 parent/child execution 边界

## 8. 第一批验收清单

### 架构验收

- `run_id` 成为主执行链统一主键
- child execution 不再只存在于 planner metadata
- scheduler 具备正式 child run 状态

### 行为验收

- 一次 fan-out / collect / merge 可按 run 视角完整回放
- 工具拒绝、审批等待、provider fallback 能统一落到事件流
- planner 页面仍可正常展示调度信息

### 工程验收

- 后端新增单测覆盖运行时协议变更
- 旧 smoke 能继续通过
- 现有前端面板不被破坏

## 9. 最终结论

目标架构的关键不在“模块越多越好”，而在：

- 一等对象清晰
- 运行时边界清晰
- 治理边界清晰
- 能力层可插拔

对当前项目而言，最关键的一步不是新增某个功能域，而是把现有 `planner / scheduler / subagent / policy / trace / memory / skill` 收口为统一运行时架构。

只要先把这一层做好，后续无论是 Claude 风格记忆、worktree、多智能体编排、MCP 长连接、还是企业审批治理，都可以在这套底座上平滑演进。
