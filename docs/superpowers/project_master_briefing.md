# MyPrivateAgent 主讲稿与学习导图

> 这份文档是给“准备面试的自己”和“第一次接手项目的自己”同时看的。它不是重复已有材料，而是把 `project_overview.md`、`project_resume_pitch.md`、`project_interview_qa.md` 与当前架构事实重新整编成一条学习和表达合一的主线。

## 1. 一句话定位

`MyPrivateAgent` 当前最准确的定位，不是“私人聊天助手”，也不是“包了一层 LangGraph 的 Agent Demo”，而是一个 **企业内部通用智能体底座**。

它的核心路线是：

- **自研 runtime core + adapter**
- **最小治理台并行**
- **SDK + 标准服务双形态交付**

这意味着它的目标不是把某一个垂域功能先做花，而是先把后续任意垂域 Agent 都能复用的运行时底座打牢：执行循环、事件协议、调度、审批、治理、能力接入、可观测性都围绕统一内核收口。

HR 可理解版：这不是一个单点聊天产品，而是一套以后做更多智能体项目时都能复用的底层平台。

## 2. 用了什么技术、做了什么、想解决什么问题

这一节建议你在面试里单独讲，因为它正好回答面试官最常问的三个问题：

- 你用了什么技术？
- 你具体做了什么？
- 你做这个项目是想解决什么问题？

### 2.1 用了什么技术

这个项目是一个标准的全栈智能体底座项目，技术栈不是随便拼的，而是围绕“运行时 + 治理 + 可交付”选的。

**后端技术：**

- `FastAPI`：承载 API、SSE 流式输出、运行时管理接口
- `SQLAlchemy 2.0 + Alembic`：承载运行时对象、一等实体和数据库迁移
- `Python`：作为运行时内核、自研 harness、策略与治理服务的实现语言
- `LangChain / LangGraph`：只在 tool binding、message 兼容和 adapter/pilot 层做参考，不作为项目主内核
- `JWT + bcrypt`：处理认证与 demo_guest 之外的标准身份能力

**前端技术：**

- `Vue 3 + Vite`：构建前端治理台和聊天入口
- `Pinia + Vue Router`：管理运行时状态、页面路由和治理面板交互
- SSE 消费链路：承接 `AgentEvent` 流，实时展示状态、工具结果和治理事件

**运行时与治理相关技术：**

- 自研 `AgentHarness`
- 自研 `AgentRun / AgentEvent / ChildRun` 运行时协议
- `Tool / Skill / MCP` 三层能力合同
- `PolicyEngine / ApprovalEngine / RunTrace / Doctor / QualityGate`
- `Embedded SDK + Runtime Service` 双交付形态

**工程化与部署：**

- `pytest / unittest / Vitest`
- `ruff`
- 多个 smoke 脚本
- `Vercel` 一体化部署
- `Dockerfile`
- 默认 `SQLite`，可切 `MySQL`
- 大量设计文档和阶段蓝图

一句话概括：

> 技术上我用了 Python + FastAPI + Vue 3 做全栈骨架，用 SQLAlchemy/Alembic 做运行时持久化，用 LangChain/LangGraph 做兼容和参考层，但核心执行循环、运行时协议和治理逻辑是自研的。

### 2.2 具体做了什么

这个项目里“做了什么”不能只说“做了一个聊天系统”，更准确的说法是“我把智能体运行、治理和交付所需的关键骨架都做了一遍”。

可以拆成下面几类来讲：

**1. 我做了运行时内核。**

- 设计并实现了 `AgentHarness` 核心循环
- 把一次请求拆成显式状态机和事件流
- 统一了 `run_id`、状态迁移、错误分类、工具执行、最终合成

**2. 我做了运行时对象模型。**

- 设计并落地 `AgentRun / AgentEvent / ChildRun / PermissionRequest / Artifact` 等一等对象
- 把原本容易散落在 metadata 里的运行态，逐步升级为可查询、可回放、可治理的数据结构

**3. 我做了多智能体和调度能力。**

- 支持 planner item fan-out 成多个 child run
- 按角色注册子智能体，如 `frontend / backend / qa / docs / planner`
- 打通父子执行关系、状态流转和 provider 故障转移

**4. 我做了能力接入层。**

- 统一 Tool、Skill、MCP 三层能力面
- 给每轮执行生成 Capability Profile
- 让系统能判断“当前能做什么、不能做什么、缺什么能力”

**5. 我做了治理闭环。**

- 增加 PolicyEngine 和审批语义
- 增加 run trace、doctor、自检、quality gate
- 让高风险动作、能力缺口、adapter 健康状态都能被观察和回放

**6. 我做了前端治理台。**

- 不只是聊天页，还包括 Runtime Surface、Governance Timeline、Planner、Doctor、Capability Gap、MCP 管理等面板
- 让运行时状态、治理信息和排障信息可以直接可视化

**7. 我做了工程化与文档沉淀。**

- 单测、smoke、CI、质量门禁
- 架构文档、阶段蓝图、运行时 contract 文档、面试材料和项目总览

一句话概括：

> 我不是只做了一个会聊天的入口，而是从运行时内核、对象模型、能力接入、治理闭环、前端工作台到工程化验证，完整做了一套可继续复用的智能体底座。

### 2.3 想解决什么问题

这个问题特别关键，因为它决定你讲出来的是“技术堆栈项目”，还是“有明确目标的系统设计项目”。

这个项目想解决的，不是“怎么接一个大模型做问答”，而是下面三类更本质的问题：

**问题 1：为什么很多智能体项目只能做 demo，不能复用？**

常见问题是：

- 一开始只是聊天 + 工具调用，后面慢慢堆 planner、memory、workflow、审批、MCP
- 每个能力都各长一套状态和元数据
- 结果项目越来越复杂，但没有统一运行时真相源

这个项目就是想解决：  
**如何把这些能力统一收口到一个可复用的 runtime core 上。**

**问题 2：为什么很多智能体项目能跑，但不能治理？**

常见问题是：

- 不知道一次执行到底做了什么
- 工具调用为什么发生、为什么失败、为什么被阻断说不清楚
- 高风险动作没有审批路径
- 出问题只能翻日志，不能按 run 回放

这个项目就是想解决：  
**如何让智能体系统从“能跑”升级到“可治理、可审批、可回放、可诊断”。**

**问题 3：为什么很多项目做完之后，下一个项目还是得重来？**

常见问题是：

- 工具层、调度层、治理层和前端控制台都绑死在一个业务里
- 换一个垂域，又得从头搭一次
- 或者被某一个外部框架的数据模型绑住，后续很难迁移

这个项目就是想解决：  
**如何把智能体项目做成一套后续可嵌入、可服务化、可扩展的基础设施。**

所以你可以把项目目标浓缩成一句更有力度的话：

> 我想解决的是：如何把一个原本容易停留在 demo 阶段的智能体系统，做成一套有统一运行时、能力合同、治理闭环和多交付形态的通用底座，让后续不同垂域的 Agent 都不需要从零重写。

### 2.4 面试时的直说版本

如果面试官直接问你“用了什么技术，做了什么，解决什么问题”，你可以直接这么说：

> 这个项目后端主要用 FastAPI、SQLAlchemy、Alembic 和 Python，前端用 Vue 3、Vite、Pinia，模型兼容层用了 LangChain/LangGraph，但核心执行循环和运行时协议是我自研的。  
> 我具体做的不是一个简单聊天页，而是把 AgentHarness 核心循环、`AgentRun / AgentEvent / ChildRun` 一等对象、多智能体调度、Tool/Skill/MCP 三层能力面、审批治理、run trace、doctor、quality gate 和前端治理台都做出来了。  
> 我想解决的问题也不是“怎么调模型”，而是“怎么把一个智能体项目真正做成可复用、可治理、可交付的底座”，这样以后做新的业务智能体时，不需要再从零重写调度、治理和能力层。

HR 可理解版：技术上是 Python 后端加 Vue 前端，事情上是做了一套智能体基础平台，目标上是解决“智能体项目很难复用、很难治理、很难长期演进”的问题。

## 3. 三档讲法

### 3.1 30 秒版

> 我做了一个叫 `MyPrivateAgent` 的项目，它的定位是企业内部通用智能体底座，不是普通 chatbot。这个项目参考了 Claude Code 一类的 harness 思路，自研了运行时内核、统一事件协议、多智能体调度、Tool/Skill/MCP 三层能力面、审批治理和前端治理台，目标是让后续不同业务方向的 Agent 都能直接复用这套基础设施。

### 3.2 3 分钟版

> `MyPrivateAgent` 是我从零搭建的一套通用智能体运行时框架。后端用 FastAPI，前端用 Vue 3，底层不是直接依赖某个外部 agent 框架，而是自己收口了 `AgentRun / AgentEvent / ChildRun` 这些一等对象，用统一状态机和事件流把聊天、工具调用、子任务调度、审批等待、回放追踪串起来。  
> 在能力层上，它不是只接工具，而是把 Tool、Skill、MCP 都纳入统一能力合同；在治理层上，已经做了最小闭环，包括策略判断、权限审批、run trace、doctor 自检和 quality gate。前端也不只是聊天页面，而是有 Runtime Surface、Governance Timeline、Planner、Doctor、Capability Gap 等治理面板。  
> 我现在把它定位成“下一个垂域 Agent 要坐上去的底座”，而不是一个单独卖点很强的应用。它最值钱的部分，是已经把运行时协议和治理骨架做出来了。

### 3.3 5 分钟技术展开版

> 这个项目最核心的点，是我没有把它做成“请求进来 -> 调模型 -> 返回文本”这种简单链路，而是把执行过程建模成了显式的 runtime。一次请求会从 `ChatService` 进入 `SimplifiedOrchestrator`，再进入 `AgentHarness` 核心循环。在循环里会做状态迁移、system prompt 拼装、工具流式调用聚合、权限判断、结果回写和最终合成，每一轮都落到统一 `run_id` 的事件流里。  
> 项目的主协议是 `AgentRun / AgentEvent / ChildRun / ArtifactRef / ApprovalRequest` 这类对象，数据库里也已经把 child run、permission request、artifact、capability remediation 等做成了一等表，而不是塞在 metadata 里。  
> 我把系统收口成四层来看更容易理解：Runtime Core 负责状态机和事件；Capability Layer 负责 Tool、Skill、MCP、Memory、Adapter 接入；Governance Layer 负责 policy、approval、trace、doctor、quality gate；Delivery Layer 则向前端治理台、嵌入式 SDK 和标准 API 暴露能力。  
> 当前我认为它已经不是“做出来一个 demo”阶段，而是“如何把已有能力收口成企业内部通用底座”的阶段。已经跑通的部分很多，但我也保留了比较清醒的边界判断，比如类型化记忆、三级权限模型、跨进程 continuation 持久化、前端 TS 化都还在后续阶段。

HR 可理解版：30 秒讲价值，3 分钟讲系统边界，5 分钟讲为什么它不是普通 demo 而是一个有架构收口能力的底座项目。

## 4. 项目全景地图

如果把这个项目当成一张地图来看，可以分成四块：

| 板块 | 解决什么问题 | 关键落点 |
|---|---|---|
| Runtime Core | 一次智能体执行怎么开始、流转、暂停、结束 | `backend/agent_framework/runtime.py`、`events.py`、`backend/harness/agent_harness.py` |
| Capability Layer | 模型到底能调用什么能力、为什么能调用 | `tool_runtime_service.py`、`skill_runtime_service.py`、`mcp_runtime_service.py`、`agent_memory_service.py` |
| Governance Layer | 什么能执行、什么要审批、出了问题怎么回放 | `policy_engine_service.py`、`approval_engine_service.py`、`run_trace_service.py`、`doctor_runtime_service.py` |
| Delivery Layer | 怎么把这套底座交给前端、业务系统和未来项目使用 | `backend/routers/`、`runtime_surface_service.py`、`backend/agent_framework/sdk.py`、`frontend-vue` |

配套还有三个重要支撑面：

- **数据与持久化**：`backend/models.py` + Alembic 迁移，把运行态对象真正落到数据库
- **工程化与验证**：CI、smoke 脚本、quality gate、doctor
- **文档与蓝图**：`docs/architecture/` 记录当前事实，`docs/change/` 记录阶段收口与实施计划

HR 可理解版：可以把它理解成“后端运行时 + 能力插件层 + 治理控制面 + 前端工作台”四块组成的智能体底座。

## 5. 核心执行链与四层架构

### 5.1 核心执行链

一次典型请求的路径是：

```text
HTTP /api/chat
  -> routers/chat.py
  -> ChatService
  -> SimplifiedOrchestrator
  -> AgentHarness.run(...)
  -> 状态迁移 / prompt 拼装 / 模型调用 / 工具执行 / 审批判断 / 事件输出
  -> SSE AgentEvent 流回前端
```

这条链的重点不在“能调用模型”，而在“执行过程可被建模、回放、治理”。

在 `AgentHarness` 中，至少做了这些关键事：

1. 拼装包含 Agent Identity、Capability Profile、分层 Memory、Skill、MCP 能力目录的上下文。
2. 调用模型并处理流式工具调用分块。
3. 判断工具是否允许执行，是否需要进入 `WAITING_APPROVAL` 或 `WAITING_PERMISSION`。
4. 把工具结果、错误、反思、完成状态统一写入事件流。
5. 根据 `CompletionEvaluator`、迭代预算和防抖规则决定是否继续。

### 5.2 四层架构

从当前真源文档 `docs/architecture/current_architecture.md` 来看，项目最适合用四层去讲：

- **Runtime Core**：统一的状态机、事件协议、run/child run、trace 关系
- **Capability Layer**：Tool、Skill、MCP、Memory、Command、Framework Adapter
- **Governance Layer**：Policy、Approval、Audit、Replay、Doctor、Risk Classification
- **Delivery Layer**：Embedded SDK、Runtime Service、Vue 最小治理台

这样讲有两个好处：

- 和当前项目事实一致，不会把历史上六层、七层的不同表述混在一起
- 更容易解释“为什么这个项目不是某个业务 Agent，而是一个通用底座”

HR 可理解版：系统不是一坨代码，而是分成“运行时、能力层、治理层、交付层”四个清晰部分。

## 6. 七个最值得讲的技术亮点

### 5.1 自研 AgentHarness 核心循环

这是最值得优先讲的亮点。因为它代表你不是只会拼 API，而是在做执行内核。

- 真实落点：`backend/harness/agent_harness.py`
- 关键能力：流式工具调用聚合、双模 tool binding、错误分类、指数退避、相似调用防抖、最终合成
- 最有代表性的工程点：`StreamingToolCallTracker` 解决模型流式 `tool_calls` 分块和 JSON 片段容错

一句话价值：把“模型输出”升级成“可控制、可治理的执行循环”。

### 5.2 一等对象协议：`AgentRun / AgentEvent / ChildRun`

项目不是靠松散 metadata 串起来的，而是逐步把运行态对象升级成了一等对象。

- 真实落点：`backend/agent_framework/runtime.py`、`backend/agent_framework/events.py`、`backend/models.py`
- 关键收益：可查询、可回放、可扩展，不会因为新增一种子执行模式就继续堆 metadata

一句话价值：把运行时从“隐式过程”变成“显式协议”。

### 5.3 多智能体调度不是概念，而是父子执行模型

- 真实落点：`scheduler_service.py`、`subagent_service.py`、`subagent_registry_service.py`
- 已有能力：planner item fan-out 成 child run、角色化子智能体、子执行状态独立流转、provider 故障转移

一句话价值：项目不是单代理问答，而是已经进入“父 run 管多个 child run”的执行模型。

### 5.4 Tool / Skill / MCP 三层能力面

- Tool 代表直接执行能力
- Skill 代表上下文化、可触发的经验与工作流
- MCP 代表外部能力目录和协议化接入

真实落点：

- `tool_runtime_service.py`
- `skill_runtime_service.py`
- `mcp_runtime_service.py`
- `capability_profile_service.py`

一句话价值：模型每一轮不是盲调用，而是在明确的“能力合同”里做决策。

### 5.5 策略、审批、回放的最小治理闭环

- 真实落点：`policy_engine_service.py`、`approval_engine_service.py`、`run_trace_service.py`
- 关键语义：高风险动作可以阻断或审批，审批结果进入事件流，前端可从 Governance Timeline 回放

一句话价值：治理不是事后日志，而是执行链内建的一部分。

### 5.6 Doctor + Quality Gate 的工程化意识

- 真实落点：`backend/scripts/doctor.py`、`quality_gate_report.py`
- 关键能力：启动前自检、最近治理数据汇总、CI 中作为 artifact 与门禁输出

一句话价值：不仅能运行，还在持续判断“当前底座是否处于健康状态”。

### 5.7 前端治理台不是演示壳，而是最小工作台

- 真实落点：`frontend-vue/src/components/RuntimeSurfacePanel.vue`、`GovernanceTimelinePanel.vue` 及相关面板
- 关键特点：Chat 只是入口，真正重要的是 Runtime Surface、Planner、Doctor、Governance Timeline、Capability Gap、MCP 管理等治理视角

一句话价值：前端不只是展示回答，而是给研发、治理、排障提供观察面。

HR 可理解版：这七点分别对应“执行内核、数据模型、任务调度、能力插件、审批治理、工程质量、操作台”。

## 7. 真实完成度与成熟度判断

这部分在面试里很重要，因为它决定你讲得是不是可信。

我建议你把成熟度说成下面这种状态：

- **已经明显超出 demo/chatbot 阶段**
- **运行时协议和治理骨架已经成形**
- **可以作为通用底座继续演进**
- **但还没有达到完全产品化、完全企业化的成熟度**

更细一点可以这样讲：

| 能力域 | 当前判断 | 说明 |
|---|---|---|
| Runtime Core | 主体完成 | 状态机、事件协议、run/child run、基础 trace 已收口 |
| Capability Layer | 主体可用 | Tool/Skill/MCP/Memory/Adapter 已有明确 seam |
| Governance Layer | 最小闭环完成 | policy、approval、doctor、timeline、quality gate 已跑通 |
| Delivery Layer | 可演示可扩展 | Runtime Surface、治理台、Embedded SDK preview、标准 API 已存在 |
| 产品化与企业化 | 部分完成 | 权限、记忆、持久化恢复、多租户等仍在硬化 |

一句人话总结就是：

> 它已经是一套“能跑、能管、能讲清楚”的底座，但还不是一套完全打磨到企业产品级的成熟平台。

HR 可理解版：项目已经做出了核心框架和治理骨架，但还有一些企业级细节在继续完善。

## 8. 当前不足与下一阶段路线

这部分不要回避，反而要主动讲，因为这能体现你的判断力。

### 7.1 当前不足

1. **类型化记忆未完全落地**  
   当前 Memory 仍偏静态加载和条目注入，距离真正的 `user / feedback / project / reference` 语义记忆还有距离。

2. **权限模型仍偏单层**  
   最小审批闭环有了，但组织 / 项目 / 用户三级策略、正式 ApprovalEngine 体系还没完全成型。

3. **Embedded SDK 仍在硬化**  
   目前已能 preview 运行和审批 continuation，但跨进程持久化、复杂恢复和更完整的默认 harness 体验还在推进。

4. **外部 Framework Adapter 仍以 pilot 为主**  
   LangGraph draft adapter 和 local fake adapter 更像受控验证骨架，而不是主执行路径。

5. **前端工程约束还不够强**  
   Vue 主体仍未完成 TS 化，前后端 contract 也还没走 OpenAPI 到前端类型闭环。

### 7.2 下一阶段路线

按 `docs/roadmap/next_phase_hardening.md`，下一阶段最值得做的仍然是：

1. 文档入口产品化
2. Embedded SDK 最小可用闭环继续深化
3. Governance Timeline 和 Runtime Surface 按 contract 继续瘦身
4. 为第二个真实 external adapter 留模板

一句话讲法：

> 现在不是再堆更多功能，而是继续把“运行时内核、治理闭环、交付形态”做实。

HR 可理解版：项目最大的不足不是功能少，而是还在把一些企业级细节从“能跑”继续打磨成“可规模化复用”。

## 9. 高频追问应答

### 8.1 为什么不直接用 LangGraph？

因为这个项目的核心需求不是“把节点连起来”，而是把执行过程收口成统一 runtime core。LangGraph 更适合图编排库，而这个项目更接近 harness-style agent loop，控制流、状态机、审批、能力合同和治理对象都需要平台自己掌握。

### 8.2 这个项目最难的是什么？

不是某个功能点，而是把原来分散在 planner、scheduler、trace、permission、memory、skill 里的事实，统一收口到 `run / child run / event / approval / artifact` 这些一等对象上。

### 8.3 为什么你说它不是 chatbot？

因为聊天只是入口。真正难和有价值的部分是调度、治理、能力接入、事件回放和交付形态，这些才是底座能力。

### 8.4 这个项目有什么商业价值？

它的价值不在直接卖一个聊天功能，而在于降低后续任意垂域 Agent 的重复建设成本。下一个业务 Agent 不用再从零重写调度、治理、审批、能力层和操作台。

### 8.5 你觉得它离真正企业级还差什么？

差的主要是权限模型深化、类型化记忆、跨进程 continuation 持久化、前端类型系统、外部 adapter 生产化这些“硬化项”，而不是核心方向不对。

HR 可理解版：这部分相当于你对面试官最可能追问的问题提前准备了标准答案。

## 10. 你的学习顺序与源码阅读路径

如果你接下来要靠这套材料真正熟悉项目，我建议按下面顺序读，不要一上来扎进 `docs/change/`：

### 第一步：先建立当前事实

先读：

1. `docs/architecture/current_architecture.md`
2. `docs/architecture/runtime_contracts.md`
3. `docs/architecture/extension_points.md`
4. `docs/roadmap/next_phase_hardening.md`

目的：先知道“系统现在是什么、contract 在哪、怎么扩展、下一步做什么”。

### 第二步：再理解为什么这样设计

再读：

1. `docs/change/2026-05-11-enterprise-agent-runtime-blueprint.md`
2. `docs/change/2026-05-11-phase-a-runtime-core-implementation-plan.md`
3. `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`

目的：知道项目为什么从“功能堆叠”转向“底座收口”，以及阶段推进顺序。

### 第三步：再回到面试表达

最后读：

1. `docs/superpowers/project_overview.md`
2. `docs/superpowers/project_resume_pitch.md`
3. `docs/superpowers/project_interview_qa.md`
4. `docs/superpowers/resume_bullet_points.md`

目的：把前两步形成的技术理解压缩成适合对外表达的话术。

### 第四步：源码阅读主线

如果你要进代码，建议按这条线读：

1. `backend/harness/agent_harness.py`
2. `backend/agent_framework/runtime.py`
3. `backend/agent_framework/events.py`
4. `backend/services/chat_service.py`
5. `backend/services/scheduler_service.py`
6. `backend/services/policy_engine_service.py`
7. `backend/services/runtime_surface_service.py`
8. `frontend-vue/src/components/RuntimeSurfacePanel.vue`
9. `frontend-vue/src/components/GovernanceTimelinePanel.vue`

这样读的好处是：先抓主骨架，再看治理和前端投影，不容易迷失在细节里。

HR 可理解版：这部分不是给 HR 看的，是给你自己准备面试前补课用的最短路径。

## 11. 最后怎么把它讲得既真实又有分量

建议你始终坚持这三个表达原则：

1. **先讲定位，再讲功能**  
   先说它是通用智能体底座，再说它有哪些能力。

2. **先讲运行时和治理，再讲聊天和工具**  
   聊天是表现层，运行时和治理才是技术壁垒。

3. **主动说边界，不要假装它已经完美**  
   你越能清楚说出还没做完的地方，越说明你真的理解这个项目。

一句收口稿可以直接这么说：

> `MyPrivateAgent` 对我来说最重要的不是“做了一个能聊天的应用”，而是“我把一个通用智能体项目真正往企业内部可复用底座的方向推了一步”。它已经有统一运行时、能力合同、审批治理、可观测性和最小治理台，也保留了对未来 SDK 和标准服务双形态交付的边界。这才是我希望在面试里重点讲清楚的价值。
