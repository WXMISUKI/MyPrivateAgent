# 运行层集成战略

> 本文定义 MyPrivateAgent 如何利用成熟执行/运行时基础设施，同时保持治理控制面主权。这是当前阶段最重要的架构方向文档。

## 1. 为什么需要这个战略

MyPrivateAgent 的控制面契约（run/event/approval/trace/audit/policy/governance）已经远比执行层能力丰富。如果继续自研执行层，项目会变成一个不可维护的平台克隆，而不是 Coze 迁移的治理底座。

**核心判断**：执行层用成熟框架，治理层自己管控。

## 2. 目标架构

```
┌──────────────────────────────────────────────────────────┐
│ Business Frontend / API / 外部系统                        │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│ Intent Router / Gateway                                  │
│ - auth context / tenant / user / conversation            │
│ - route to agent_id                                      │
└────────────────────────┬─────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
  │ Domain      │ │ Domain      │ │ Domain      │
  │ Agent A     │ │ Agent B     │ │ Agent C     │
  │ agent.yaml  │ │ agent.yaml  │ │ agent.yaml  │
  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
         │               │               │
         └───────────────┼───────────────┘
                         ▼
┌──────────────────────────────────────────────────────────┐
│ Execution Plane (外部成熟框架)                             │
│                                                          │
│ LangGraph / AgentRun / ADK / OpenAI Agents SDK            │
│ - graph / state / checkpoint / streaming                 │
│ - human-in-the-loop / handoff / retry                    │
│ - deployment / sandbox / model proxy                     │
└────────────────────────┬─────────────────────────────────┘
                         │ normalized events
                         ▼
┌──────────────────────────────────────────────────────────┐
│ MyPrivateAgent Control Plane                             │
│                                                          │
│ - agent catalog / agent.yaml                             │
│ - capability catalog (Tool/MCP/Skill/Memory/Provider)    │
│ - policy / approval                                      │
│ - trace / audit                                          │
│ - runtime contract gate                                  │
│ - governance timeline                                    │
│ - quality gate / promotion gate                          │
└──────────────────────────────────────────────────────────┘
```

## 3. 分层定义

### 3.1 Control Plane（治理控制面）

**我们拥有，我们管控。**

| 职责 | 主要落点 |
|---|---|
| Agent 资产注册与发现 | `backend/domain_agents/*/agent.yaml`、`DomainAgentRegistryService` |
| 能力目录 | `ToolRuntimeService`、`MCPRuntimeService`、`SkillRuntimeService`、`MemoryService` |
| 策略与审批 | `PolicyEngineService`、`ApprovalEngineService` |
| 运行追踪与审计 | `RunTraceService`、Runtime Surface、Governance Timeline |
| 质量门禁 | `RuntimeContractGate`、`QualityGateReport`、promotion gate |
| 治理台 | Vue 前端治理台 |

**目录边界**：`backend/control_plane/`（新建，逐步收口）

### 3.2 Runtime Plane（运行层面）

**我们定义合同，外部框架执行。**

| 职责 | 实现方式 |
|---|---|
| 执行合同定义 | `ExecutionRequest` / `ExecutionEvent` / `ExecutionResult` 标准 envelope |
| 运行框架适配 | LangGraph adapter、AgentRun adapter、ADK adapter |
| 网关路由 | Intent Router、Runtime Selector |
| 三条竖切 MVP | simple_agent / tool_agent / approval_agent |

**目录边界**：`backend/runtime_plane/`（新建，逐步承载）

### 3.3 Framework Adapters（框架适配层）

**我们写 adapter，不改框架本身。**

| 适配器 | 状态 | 目标 |
|---|---|---|
| `LangGraphDraftAdapter` | 已有 pilot 骨架 | 复杂图编排、循环、checkpoint、human-in-loop |
| `AgentRunAdapter` | 待实现 | 托管运行、沙箱、模型代理、可观测 |
| `ADKAdapter` | 待实现 | 跨语言/跨团队 agent 发现与互操作 |
| `OpenAIAgentsAdapter` | 待实现 | 轻量 agent、handoff、guardrails |
| `NoopFrameworkAdapter` | 已有 | 测试/开发用 |
| `LocalFakeFrameworkAdapter` | 已有 | 本地 smoke 测试 |

**目录边界**：`backend/agent_framework/framework_adapter_spi/`（现有，保持）

### 3.4 Domain Agents（垂域智能体层）

**每个团队负责自己的 agent package。**

```text
backend/domain_agents/<agent_id>/
  agent.yaml          # 必须，manifest 驱动
  prompts/            # 系统提示词
  tools/              # 工具定义
  workflows/          # 工作流图定义（LangGraph subgraph）
  rag/                # RAG 配置
  policies/           # 治理策略
  evals/              # 评估用例
```

**关键约束**：垂域 agent 只通过 registry / API / tool contract 调用其他 agent，不直接 import 内部代码。

### 3.5 Capability Runtime（能力运行时）

**已有，保持现有边界。**

| 能力 | 落点 |
|---|---|
| Provider 接入 | `backend/capability_runtime/provider_onboarding_catalog.py` |
| 知识/RAG | `unifiedKnowledgeProvider`（外部服务） |
| 语音 | `backend/voice_runtime/` |
| 文档 | `backend/capability_runtime/` |

## 4. ExecutionAdapter v1 合同概念

运行层与治理层之间的标准化通信 envelope。这是防膨胀的关键——我们控制 envelope，不控制每个框架的内部实现。

### 4.1 ExecutionRequest

```python
class ExecutionRequest:
    request_id: str           # 全局唯一请求标识
    agent_id: str             # 目标 agent 标识
    user_input: str           # 用户输入
    thread_id: str | None     # 会话线程标识
    runtime: str              # 目标运行时标识（langgraph / agentrun / adk / local）
    context_refs: list[str]   # 上下文引用（conversation_id、knowledge_source 等）
    metadata: dict            # 扩展元数据
```

### 4.2 ExecutionEvent

```python
class ExecutionEvent:
    event_id: str             # 全局唯一事件标识
    run_id: str               # 运行实例标识
    stage: str                # 阶段（planning / generating / tool_calling / observing / finalizing）
    type: str                 # 事件类型（started / completed / failed / approval_required / tool_call）
    payload_summary: str      # 事件摘要（不含大块 raw payload）
    raw_ref: str | None       # 原始事件引用（框架内部 id，用于回溯）
    timestamp: float          # 时间戳
```

### 4.3 ExecutionResult

```python
class ExecutionResult:
    status: str               # 完成状态（success / failed / aborted / approval_pending）
    final_answer: str         # 最终回答
    artifacts: list[dict]     # 产出物引用列表
    tool_calls: list[dict]    # 工具调用记录
    citations: list[dict]     # 引用来源
    trace_ref: str            # 追踪引用
    metadata: dict            # 扩展元数据
```

**关键约束**：
- envelope 不得包含 Python callable、active stream iterator 或 provider client
- envelope 是治理层消费的标准格式，不是框架内部格式的透出
- 每个 adapter 负责将框架原生事件翻译为标准 envelope

## 5. 四阶段推进计划

### Stage 0：冻结与定位收口（当前阶段，1 周）

**目标**：明确方向，停止扩展，建立边界。

| 任务 | 产出 | 状态 |
|---|---|---|
| 更新项目定位文档 | PROJECT_AGENT.md、entrypoint、current_architecture | 本次完成 |
| 创建运行层集成战略文档 | 本文档 | 本次完成 |
| 创建 OpenSpec spec | `runtime-plane-integration-strategy/spec.md` | 本次完成 |
| 收口目录骨架 | `backend/control_plane/`、`backend/runtime_plane/` 已存在，后续新能力优先收口到这两个正式承载位置 | 本次完成 |
| 冻结 AgentHarnessFacade 扩展 | 不再新增 preview 方法 | 立即生效 |
| 更新开发约束 | 10 条硬约束写入文档 | 本次完成 |

**完成标准**：
- 所有文档内部链接可跳转
- `backend/control_plane/` 与 `backend/runtime_plane/` 作为正式承载位置存在且可被 Python import
- 新开发有明确的"该放哪里"指引

### Stage 1：运行层 MVP（2-3 周）

**目标**：三条竖切跑通，验证 LangGraph/AgentRun 接入路径。

**首切片**：`simple_agent`。先验证 ExecutionRequest / ExecutionEvent / ExecutionResult envelope 和 adapter boundary，再进入 tool/approval 复杂度。

**当前进度**：

- `simple_agent` 最小适配器已落地
- `tool_agent` 最小适配器已落地
- `approval_agent` 最小适配器已落地
- ExecutionRequest / ExecutionEvent / ExecutionResult / AgentManifest 已落地
- `simple_agent` 的最小单测已通过
- `tool_agent` 的最小单测已通过
- `approval_agent` 的最小单测已通过
- 当前 Stage 1 三条 MVP 竖切已经闭合，但仍未进入真实审批提交、审批恢复、multi-agent 或 managed runtime 复杂切片

| 竖切 | 验证什么 | 框架选择 |
|---|---|---|
| simple_agent | 只调用模型，不调用工具。验证部署、调用、trace 回传 | LangGraph 或 AgentRun |
| tool_agent | 调一个只读工具。验证 tool schema、MCP/Function Call、错误归一化 | LangGraph |
| approval_agent | 高风险工具意图不执行，归一化为 `approval_pending` envelope | Local adapter proof first |

**产出**：
- 三个 demo agent（`backend/domain_agents/` 下新增）
- 统一 Execution envelope 实现
- LangGraphAdapter 和/或 AgentRunAdapter 最小实现
- trace 回传到 MyPrivateAgent 治理层

**约束**：
- 每个 agent 必须有 `agent.yaml`
- 每个 agent 必须有最小 smoke 测试
- 只通过 adapter 接入，不直接调用框架原生 API
- 每完成一个竖切，必须写一份阶段回顾，确认是否仍符合 Stage 1 非目标与后续推广条件

### Stage 2：治理最小接入（3-4 周）

**目标**：治理层能观察运行层，高风险操作走审批。

| 阶段 | 治理接入深度 | 目标 |
|---|---|---|
| 第 1 步 | 只读治理 | agent 注册、能力目录、trace 摘要、运行状态可见 |
| 第 2 步 | 轻量拦截 | 高风险工具调用前走 policy / approval |

**产出**：
- agent catalog 可展示外部运行层的 agent 状态
- capability catalog 可展示外部运行层的工具调用
- approval bridge 可在高风险操作前拦截并走审批流程
- Runtime Surface 可看到外部运行结果

### Stage 3：模板硬化（4-6 周）

**目标**：形成可复制的开发模式，新人可按模板快速上手。

**产出**：
- agent 模板（agent.yaml + prompts/ + tools/ + evals/ 的最小脚手架）
- adapter 模板（新框架 adapter 的最小实现骨架）
- eval 模板（每个 agent 的最小验证用例）
- CI quality gate（新 agent 必须通过的自动化检查）
- promotion 流程（experimental → pilot → production 的标准化路径）
- 阶段回顾模板正式固化为团队执行规范

## 6. 10 条开发硬约束

这些约束的目的是防止项目在迁移过程中膨胀为不可维护的平台克隆。

| # | 约束 | 为什么 |
|---|---|---|
| 1 | 任何新 agent 必须先有 `agent.yaml` | 没有 manifest 的 agent 不可发现、不可治理、不可审计 |
| 2 | 任何运行框架只允许通过 adapter 接入 | 防止框架原生 payload 散落到业务代码和治理台 |
| 3 | MyPrivateAgent 不实现通用 checkpoint、worker scheduler、sandbox、模型网关 | 这些是成熟框架/平台的能力，自研成本高且质量无法保证 |
| 4 | 高风险工具必须走 policy / approval | 安全底线，不允许绕过 |
| 5 | `runtime_plane/` 只产出标准事件 | 运行层不直接写治理 UI，保持单向依赖 |
| 6 | `control_plane/` 只消费标准事件 | 治理层不理解框架私有结构，保持可替换性 |
| 7 | 新能力必须先写 OpenSpec | 目标、非目标、边界、验收、回滚，防止无序扩展 |
| 8 | 每个 adapter 必须有 promotion gate | experimental → pilot → production，防止未验证的 adapter 进入生产 |
| 9 | 每个 agent 必须有最小 eval 或 smoke | 证明没有越界，不需要复杂但必须存在 |
| 10 | 禁止"顺手扩展平台能力" | 发现缺口先记录到 backlog，不在业务迁移中顺手补平台 |

## 7. 当前项目的正确使用方式

### MyPrivateAgent 适合做什么

- **Agent 资产管理**：注册、发现、版本管理、能力声明
- **治理管控**：策略引擎、审批流程、审计追踪
- **可观测性**：运行追踪、治理时间线、质量门禁
- **能力接入**：Tool / MCP / Skill / Memory / Provider 统一接入
- **Contract Gate**：运行时契约检查、promotion 门禁

### MyPrivateAgent 不适合做什么

- 复杂图编排和循环执行 → 用 LangGraph
- 云端沙箱和 Serverless 部署 → 用 AgentRun
- 多智能体协作和 handoff → 用 LangGraph 或 OpenAI Agents SDK
- 跨语言/跨团队 agent 发现 → 用 ADK / A2A / Nacos Agent Registry

### 对于 Coze 迁移的建议

1. **先不急着迁移 Coze 工作流**，先把运行层基础设施跑通
2. **选 2 个典型 Coze 工作流**做 PoC，验证 LangGraph 接入路径
3. **每个 Coze workflow 迁移为一个 domain_agent** + workflow graph/subgraph
4. **所有工具调用、审批点、RAG 引用、最终输出**都转成标准 envelope
5. **多人并行迁移时**，各自负责自己的 agent package，通过 registry 和 API 协作

## 8. 外部参考框架

| 框架/平台 | 我们借鉴什么 | 不做什么 |
|---|---|---|
| **LangGraph** | 图/状态/checkpoint/human-in-loop 执行语义 | 不复制其图引擎 |
| **AgentRun** | 托管运行/沙箱/模型代理/可观测/部署 | 不绑定其基础设施 |
| **ADK / A2A** | AgentCard/注册发现/跨 agent 通信 | 不复制其通信协议 |
| **OpenAI Agents SDK** | handoff/guardrail/session/tracing 事件规范化 | 不绑定 OpenAI 生态 |
| **Nacos Agent Registry** | namespace/version/registration/discovery | 不复制其注册中心 |
| **CrewAI** | 角色分工/快速原型模式参考 | 不作为复杂执行底座 |

## 9. 推荐阅读顺序

1. 本文档
2. [agent_runtime_control_plane_entrypoint.md](./agent_runtime_control_plane_entrypoint.md)
3. [current_architecture.md](./current_architecture.md)
4. [runtime_contracts.md](./runtime_contracts.md)
5. [extension_points.md](./extension_points.md)
6. [domain_agent_development_guide.md](../guides/domain_agent_development_guide.md)
7. [next_phase_hardening.md](../roadmap/next_phase_hardening.md)
8. [runtime_plane_stage_review_protocol.md](../roadmap/runtime_plane_stage_review_protocol.md)
9. [runtime_plane_stage_0_review.md](../roadmap/runtime_plane_stage_0_review.md)

## 10. 阶段回顾协议

每完成一个 stage，必须按统一模板记录回顾，避免推进过程中慢慢偏离原计划。

建议模板：

```text
Stage:
Date:
Completed work:
What stayed within scope:
What drifted or got tempting:
What must not be expanded next:
What evidence shows the stage is done:
Is the next stage still justified:
Next allowed action:
```

回顾原则：

- 只写事实，不写愿望
- 如果出现偏离，先回 freeze-and-align stage 再继续
- 回顾必须附上当前 stage 的非目标
