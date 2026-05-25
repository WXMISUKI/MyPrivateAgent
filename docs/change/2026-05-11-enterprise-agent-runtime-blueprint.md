# MyPrivateAgent 企业内部通用智能体底座三阶段落地蓝图

## 1. 文档定位

本文档用于在 `MyPrivateAgent` 当前代码与既有方案文档基础上，正式收口一版可执行的企业内部通用智能体底座设计。本文档重点回答以下问题：

1. 为什么当前项目不适合继续按“加功能”的方式推进
2. 未来底座应采用什么主路线
3. 哪些现有模块应该保留，哪些应该重构，哪些应该降级为兼容层
4. 三个阶段分别做什么、交付什么、如何验收

本文档是对以下文档的进一步收口和工程化表达：

- `docs/general_agent_framework_target_architecture.md`
- `docs/general_agent_framework_enterprise_plan.md`
- `docs/framework_execution_roadmap.md`

## 2. 现状判断

当前项目已经不是“从零做 Agent Demo”的阶段，而是进入了“如何把已有能力收口为企业级底座”的阶段。

从现有文档和工程结构看，项目已经具备以下基础：

- 主执行链已经形成：`AgentHarness -> Orchestrator -> ChatService`
- 运行时、事件、调度、子智能体、治理、MCP、技能、记忆都已有雏形
- 前端已经存在基础治理台入口，而不是纯聊天界面
- 工程上已经有最小测试与若干治理向面板

但当前最核心的问题也非常明确：

- `run / planner / scheduler / subagent / trace` 的边界还没有彻底统一
- `permission / approval / policy / audit` 仍偏“功能点”而不是“治理内核”
- `memory / skill / command / mcp` 已经存在，但仍没有统一接入契约
- 前端虽然能看部分运行效果，但还没有围绕统一运行时模型组织

结论是：

当前项目最大的风险不是能力不足，而是底层对象与边界没有完全收口。如果继续堆业务能力、堆新工具、堆新页面，会持续放大跨层耦合、回放困难、审批失真、适配器失控这些结构性问题。

## 3. 目标定位

本轮底座设计的目标定位固定为：

`企业内部通用智能体底座，后端内核优先，前端最小治理台并行，双形态交付。`

这里的“双形态”指：

1. `Embedded SDK`
其他 Python 项目可以把底座作为库嵌入，直接复用运行时、治理、能力层。

2. `Runtime Service`
底座也可以独立对外暴露标准 API / SSE / 事件流，供前端、外部系统或未来垂域项目调用。

这里的“前端最小治理台并行”指：

- 前端不是业务壳，不承担垂域业务流程
- 前端主要承载运行效果可视化、审批、审计、回放、适配器健康检查
- 前端优先服务研发调试、治理排障和企业接入，而不是先做平台运营功能

## 4. 推荐路线

结合当前项目现状，不推荐以下两条路线：

### 4.1 不推荐路线一：继续在现有骨架上横向堆功能

风险：

- 每新增一个能力域，就会新增一套旁路状态
- 调度、技能、记忆、审批、MCP 会继续各自生长
- 后续做垂域智能体时，业务会反向绑定当前 demo 期结构

### 4.2 不推荐路线二：直接选一个外部框架作为主底座

风险：

- 运行时对象、审批语义、治理事件会被外部框架抽象反向约束
- 前端治理台会被迫围着外部框架数据模型适配
- 双形态交付难以稳定，尤其是嵌入式 SDK 场景

### 4.3 推荐路线：兼容演进型自研内核 + 外部框架适配器

主张：

- 自己定义统一运行时协议、治理协议、能力接入契约
- 外部框架只作为执行引擎参考或适配来源
- 当前项目先不大爆炸重写，而是在现有代码骨架上逐步插入正式内核

这样做的核心收益是：

- 保住当前已有的治理台、调度器、事件体系、运行时面板投资
- 同时为未来接入 DeepAgents、CrewAI、LangGraph 或自研 lightweight runtime 预留 adapter 边界
- 避免在没有统一内核前，把业务能力写死在某一个框架品牌语义里

## 5. 目标架构骨架

建议将整体架构收口为四层，而不是继续按分散服务自然生长：

### 5.1 Runtime Core

负责统一定义和维护以下一等对象：

- `AgentRun`
- `ChildRun`
- `AgentEvent`
- `ApprovalRequest`
- `ArtifactRef`
- `RunSnapshot`

这层是未来一切执行行为的真实来源，任何 chat、planner、scheduler、tool、hook、mcp、memory、skill 行为都必须能映射到运行时对象。

### 5.2 Capability Layer

负责统一接入和解释：

- Tool Runtime
- Skill Runtime
- Memory Runtime
- MCP Runtime
- Model / Provider Runtime
- External Framework Adapters

这层的原则是：

- 业务不直接依赖具体框架品牌
- 能力域必须通过统一契约暴露给 Runtime Core
- 所有能力调用都应可观测、可审计、可限权

### 5.3 Governance Layer

负责治理与企业控制面：

- Policy Engine
- Approval Engine
- Audit Log
- Replay / Trace
- Diagnostics / Doctor
- Risk Classification

这层是项目从“通用 Agent Demo”迈向“企业内部底座”的关键差异点。

### 5.4 Delivery Layer

负责两类对外交付方式：

- Embedded SDK
- Runtime Service

同时前端治理台也归属于这一层，只消费稳定 DTO，不直接依赖底层服务实现细节。

## 6. 核心边界定义

### 6.1 Planner 与 Scheduler 的边界

- `Planner` 负责“目标拆解”和“durable plan”
- `Scheduler` 负责“执行图推进”和“child run 生命周期”

不再建议让 planner 同时承担执行控制职责。

### 6.2 Permission 与 Approval 的边界

- `Permission` 是策略判断结果
- `Approval` 是治理流程对象

当前偏窄的 `WAITING_PERMISSION` 语义，后续应统一升级为 `WAITING_APPROVAL`，并把审批单作为第一类对象持久化。

### 6.3 Static Memory 与 Runtime Memory 的边界

- `GLOBAL_AGENT.md / PROJECT_AGENT.md` 是静态规则与项目上下文层
- `MemoryEntry` 是运行时长期记忆对象

两者都属于 memory 域，但不是一个层次，不能继续混成一个“加载记忆文件”的流程。

### 6.4 Run Trace 与 Audit 的边界

- `Run Trace` 面向研发调试、执行回放、行为诊断
- `Audit Log` 面向治理合规、审批留痕、组织级审查

它们可以复用相同事件源，但查询模型与对外表达必须分离。

### 6.5 Runtime Core 与 Adapter 的边界

- Runtime Core 定义平台自己的协议和状态机
- Adapter 负责把外部框架或外部能力翻译成平台协议

平台后续可以更换 adapter，但不能让 adapter 倒过来定义平台主协议。

## 7. 三阶段实施蓝图

## Phase A：统一运行时内核与治理主线

### 目标

先把底座最关键的“执行对象”和“治理对象”统一下来，停止旁路生长。

### 工作重点

1. 定义正式的 `AgentRun / ChildRun / AgentEvent / ApprovalRequest / ArtifactRef`
2. 统一运行时状态机与停止原因、错误分类
3. 将 `run trace` 升级为 `run` 原生能力，不再主要依附 planner item
4. 把 scheduler 提升为第一类运行时服务
5. 把审批对象从权限等待语义中拆出来
6. 让前端治理台先按 `run / approval / audit / adapter health` 视图做最小对齐

### 交付物

- 统一运行时协议文档与数据结构稿
- 运行时状态机实现或兼容层实现
- 新版 trace/approval 写入接口
- `run` 视角的治理台最小查询接口
- 旧 API 的兼容适配层

### 验收标准

- 任意一次执行都可以按 `run_id` 回放主链路
- child execution 有正式状态，而不是只存在于 planner metadata
- 工具拒绝、审批等待、fallback、merge 都能统一落到同一事件链
- 前端至少能稳定查看 `run / approval / audit / adapter health` 四类信息

### 本阶段不做

- 不优先扩充垂域业务功能
- 不优先做复杂前端交互改版
- 不优先引入大量新 provider 或新 MCP

### Phase A 实施状态（2026-05-11）

本阶段已经完成第一轮兼容演进落地，当前状态如下：

- 运行时对象与事件协议：已落地。`AgentRunContext` 快照已暴露 runtime core 标记，`AgentEvent` 已支持 `source / severity / summary / detail` 统一事件壳。
- 审批对象与策略结果：已落地。新增 `ApprovalEngineService`，策略结果已区分 `allowed / requires_approval / reason_code`，审批状态对象进入 scheduler runtime entities。
- scheduler 与 run-scoped trace：已落地。调度运行、子执行、审批请求已补齐 run-scoped 字段，显式 `run_id / child_run_id / child_display_id / plan_id / item_id` 优先级已通过回归测试固定。
- chat runtime 映射与治理 DTO：已落地。审批创建/审批处理事件已映射为统一 governance trace，runtime surface DTO 已从松散 dict 收口为结构化 schema。
- high-risk 审批贯通：已落地。`PolicyDecision.requires_approval` 已从 hook 传递到 harness，高风险工具会进入 `WAITING_APPROVAL` 并产生 `approval_created` 事件，不再被误归类为普通 `tool_denied`。`AgentHarness -> Orchestrator -> ChatService / Router / Scheduler` 真实链路现在会保留 `state / stop_reason / approval_request_id`，上层 chat / scheduler 会保持 `waiting_approval` 暂停态，不会误完成计划或 child run。
- 前端最小治理台对齐：已落地。`GovernanceTimelinePanel` 可查看当前 run 与待处理审批摘要，`RuntimeSurfacePanel` 可通过后端 runtime profile 查看 runtime core 和 governance overview contract。
- 剩余边界：`ArtifactRef / Adapter Health` 仍以设计目标保留，尚未在 Phase A 第一轮中作为正式运行时对象完全落地，建议进入 Phase B 前补一个轻量契约草案。

本轮验证命令：

```powershell
python -m unittest tests.agent_framework.test_events tests.agent_framework.test_policy_engine_service tests.agent_framework.test_agent_hook_service tests.agent_framework.test_runtime_surface_service tests.agent_framework.test_run_trace_service tests.agent_framework.test_scheduler_service tests.agent_framework.test_chat_service tests.agent_framework.test_approval_engine_service tests.agent_framework.test_orchestrator_service -v
cmd /c npm test -- --run src/components/__tests__/GovernanceTimelinePanel.test.js src/components/__tests__/RuntimeSurfacePanel.test.js
```

## Phase B：能力层与 Adapter 体系重构

### 目标

在运行时内核稳定后，把当前分散的能力面收口成统一接入层，并为外部框架适配做好边界。

### 工作重点

1. 统一 Tool Runtime 契约与工具结果封装
2. 设计 `SkillDefinition`，补齐模型覆盖、工具白名单、上下文模式、触发条件
3. 设计类型化 `MemoryEntry` 与基础召回解释链
4. 将 command 从 UI 能力目录升级为统一命令协议
5. 拆分 MCP Runtime 的 registry、session、capability router、audit
6. 增加外部框架 adapter 契约，至少支持未来接入：
   - LangGraph adapter
   - DeepAgents-style adapter
   - CrewAI-style adapter

### 交付物

- `Capability Layer` 契约文档
- `SkillDefinition` 与 `MemoryEntry` 数据结构
- 统一命令协议
- MCP 运行时重构草案
- Adapter SPI 或等效扩展接口

### 验收标准

- 运行时能解释“为什么激活了这个 skill”
- 运行时能解释“为什么召回了这条 memory”
- 外部框架即使尚未真正接入，也已有明确适配位和翻译协议
- command 不再只是前端跳转动作，而是平台级执行入口之一

### 本阶段不做

- 不把 adapter 做成深度耦合某个外部框架的实现
- 不追求一次性做完高级记忆治理或复杂知识库编排

## Phase C：企业治理与产品化收口

### 目标

让底座具备企业接入和长期演进的最小完备性，而不是停留在技术 demo。

### 工作重点

1. 完成组织 / 项目 / 用户三级策略覆盖设计
2. 完成审批链、审计导出、风险分级与整改动作抽象
3. 统一配置分层与运行时覆写来源
4. 增强结构化日志、指标、trace、告警
5. 固化 Embedded SDK 与 Runtime Service 的发布边界
6. 让前端治理台具备最小平台化操作能力

### 交付物

- 策略治理模型
- 审批与审计导出方案
- 配置分层规范
- 发布与版本策略
- 前端治理台最小产品化方案

### 验收标准

- 高风险动作具备明确阻断或审批路径
- 运行时配置可解释“值来自哪里、谁覆盖了谁”
- 业务系统可以明确选择 SDK 接入或独立服务接入
- 研发和运维无需翻原始日志即可理解主执行链与主要风险点

## 8. 保留 / 重构 / 引入清单

## 8.1 建议保留的部分

这些能力已有继续演进价值，应保留骨架：

- `ChatService` 作为用户请求进入编排层的主入口
- `scheduler_service` 的 fan-out / collect / merge 思路
- `run_trace_service` 的运行轨迹能力方向
- `policy_engine_service` 的最小治理入口
- `runtime_surface_service` 与前端治理面板的运行时展示思路
- 前端已有的 `PlannerPanel / RuntimeSurfacePanel / GovernanceTimelinePanel / DoctorPanel / McpManagementPanel`

保留不代表不改，而是说明这些模块的方向是对的，值得升级而不是推倒。

## 8.2 建议重构的部分

这些部分是后续重构重点：

- `runtime.py`：从现有状态机演进为正式运行时核心
- `events.py`：从事件集合演进为统一事件协议族
- `scheduler_service.py`：从计划增强能力演进为第一类运行时调度服务
- `run_trace_service.py`：从附属轨迹能力演进为 run 原生回放层
- `policy_engine_service.py`：从最小阻断逻辑演进为正式策略内核
- `agent_memory_service`：从静态分层加载演进为受治理的 memory runtime
- `skill_runtime_service`：从静态技能资源演进为可解释的 skill runtime

## 8.3 建议新增的正式对象或模块

建议逐步新增：

- `ApprovalEngine`
- `ChildRunManager`
- `ArtifactRegistry`
- `AdapterRegistry`
- `CommandExecutionService`
- `MemoryRuntime`
- `McpSessionManager`
- `McpCapabilityRouter`
- `AuditExportService`

这些新增模块的目标不是“模块越多越好”，而是把此前混在一处的边界显式化。

## 8.4 建议降级为兼容层的部分

下列逻辑后续更适合被保留为兼容层，而不是继续作为核心真相源：

- planner item 上承载的部分运行态 metadata
- 以页面展示为目标倒推出来的部分 command 结构
- 只服务单一 demo 链路的特化事件字段

原则是：

旧结构先兼容，不强拆；但新的运行时事实来源必须逐步迁到正式内核对象上。

## 9. 对前端治理台的具体要求

前端治理台当前优先级为“中优先级并行”，因此建议控制范围：

### 9.1 当前阶段必须看到

- run 列表与 run 详情
- child run 关系
- approval 队列与处理结果
- audit 时间线
- adapter / capability 健康状态

### 9.2 当前阶段不优先做

- 复杂平台运营后台
- 多租户组织管理完整 UI
- 大量业务配置录入页面

### 9.3 前端设计原则

- 前端只消费稳定 DTO
- 前端不直接理解底层服务实现细节
- 任何治理卡片、时间线、状态标签都尽量围绕统一运行时对象构建

## 10. 实施顺序建议

如果进入代码阶段，建议严格按以下顺序推进：

1. 先补运行时协议与对象模型
2. 再收口 scheduler / child run / trace / approval
3. 再改 skill / memory / command / mcp
4. 最后再推进组织级治理与前端平台化

不建议把顺序打乱。原因很简单：

- 没有统一内核，能力层会继续旁路生长
- 没有治理主线，前端平台化会变成“展示很多，但真相不统一”
- 没有 adapter 边界，未来接外部框架会造成二次架构反噬

## 11. 风险与约束

### 11.1 最大风险

最大的风险不是技术难度，而是“边改边继续加功能”，导致统一内核永远无法收口。

### 11.2 最大约束

必须兼容当前已有前后端面板与 demo 主链路，避免一次性重写造成验证链路断裂。

### 11.3 管控建议

- 所有新增能力必须先回答它归属于哪一层
- 所有新增状态必须先回答它是不是 `run / child-run / approval / artifact` 的派生
- 所有新增页面必须先回答它展示的是不是统一 DTO，而不是临时拼装数据

## 12. 结论

`MyPrivateAgent` 后续最优路线，不是继续堆成“功能更多的 Agent Demo”，也不是立即推倒重写，而是：

`以兼容演进的方式，先做企业可控的统一运行时内核，再把能力层、治理层、交付层逐步收口。`

长期看，这条路线能同时满足以下目标：

- 支撑未来多个垂域智能体项目
- 允许接入外部成熟框架，但不被其反向定义平台
- 保持 SDK 与独立服务双形态
- 让前端治理台真正围绕企业底座工作，而不是围绕单一 demo 工作

如果后续进入实施阶段，建议以下内容作为第一批代码改造范围：

1. `run / child-run / event / approval` 协议落地
2. `scheduler / trace / policy` 收口改造
3. 前端治理台最小 run 视图对齐

这三件事完成后，项目才算真正进入“企业内部通用智能体底座”的正确轨道。
