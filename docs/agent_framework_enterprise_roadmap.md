# Agent Framework 企业级路线图

## 目标

将当前可复用的 Agent Demo 继续演进为更成熟的通用智能体框架，使其在执行质量、治理能力和可扩展性上更接近 Claude Code 风格。

本路线图聚焦于当前项目评审中识别出的关键缺口：

1. 真正的多智能体调度
2. 长生命周期 MCP Runtime
3. Skill Runtime 集成
4. 学习治理
5. 可观测性与审计
6. 企业级调度治理

## 当前基线

项目已经具备较强的第一阶段基础：

- 可复用的 chat + harness + orchestrator 骨架
- planner / todo 领域与面板
- 伪 subagent handoff 与最小 spawned runtime 协议
- MCP registry、probe、handshake skeleton、`tools/call`、runtime capability binding，以及 settings panel
- runtime learning 注入和 feedback-to-learning 的最小闭环
- 有针对性的前端回归覆盖和后端服务测试

这意味着项目已经不再是一个简单的聊天 Demo，而是具备清晰执行架构的可复用框架 Demo。下一阶段应优先补成熟度和运行时确定性，而不是继续横向增加 UI 面。

## 优先级原则

### P0 原则

- 优先保证执行正确性，而不是新增表面功能
- 优先澄清 scheduler / runtime 边界，而不是继续堆叠 ad hoc chat-route 逻辑
- 优先治理能力和可审计性，而不是依赖隐式“魔法行为”
- 每个阶段都必须留下可测试边界和清晰回滚点

### 推荐优先顺序

1. 真正的多智能体调度器
2. 长生命周期 MCP Runtime
3. 调度治理与审计
4. Skill Runtime 集成
5. 学习治理
6. 更广泛的 UX 与运营工具

## 阶段规划

## Phase A：真正的多智能体调度器

### 目标

将当前的伪 handoff 模型升级为真正的调度器，使其能够将 plan item fan-out 为多个 child execution，并把结果 merge 回 parent run。

### 范围

- 引入独立于 chat route 控制流的 scheduler service
- 支持一个 parent run 派生多个 child execution
- 增加 `queued`、`running`、`completed`、`failed`、`cancelled` 等 child execution 状态
- 支持 plan item 的 `fan-out -> collect -> merge`
- 持久化 child execution metadata 和 merge summaries
- 通过统一 runtime event layer 发出 scheduler 事件

### 预期交付物

- `SchedulerService` 或等效运行时协调器
- planner item 到 child execution 的映射模型
- child result 聚合用的 merge strategy abstraction
- 面向 scheduler 的事件 schema 与后端测试
- 最小可用的前端 planner 审计 / 历史可视化

### 验收标准

- 一个 planner item 可以产生多个 child execution
- parent plan item 可以在所有必需子执行返回前保持打开状态
- 失败会被确定性记录，不会静默消失
- merge 结果可持久化并通过 API 查看
- 至少有一个回归测试覆盖成功的 fan-out / fan-in
- 至少有一个回归测试覆盖部分失败处理

### 风险

- 如果 parent / child 状态流转没有归一化，状态数量会快速膨胀
- 如果重试不具备幂等性，可能出现重复执行
- 如果 child 职责边界不清，merge 质量会不稳定

## Phase B：长生命周期 MCP Runtime

### 目标

将当前 MCP registry 与最小 session skeleton 提升为稳定的长生命周期 Runtime，支持 session 复用、健康状态和重试治理。

### 范围

- 增加 session 生命周期管理
- 增加健康缓存与 probe 新鲜度策略
- 增加 reconnect / invalidation 规则
- 增加按 server 维度的 session 状态追踪
- 增加 capability-provider 选择策略
- 为 handshake、`tools/list`、`tools/call`、errors 和 retries 增加 MCP 审计轨迹

### 预期交付物

- `McpSessionManager` 或等效长生命周期运行时层
- 可复用的 connection / session cache
- session invalidation 与 reconnect 策略
- MCP API 中的 health 与 freshness 元数据
- 覆盖 reconnect、无效 session 复用和 degraded provider fallback 的后端测试

### 验收标准

- 对同一 MCP server 的重复调用，在可能时会复用有效 session
- 不健康 session 会被确定性失效并重新建立
- 运行时能够区分 configuration errors、probe failures 和 call failures
- MCP 调用历史可查询，用于调试和审计

### 风险

- 泄漏过期 session 或子进程
- 通过静默 fallback 掩盖基础设施问题
- 如果没有 freshness window，health state 会发生漂移

## Phase C：调度治理与审计

### 目标

增加企业级运行时治理，让执行过程由策略驱动，而不是 best-effort。

### 范围

- scheduler 层 capability policy engine
- blocking、fallback、retry 和 approval checkpoints
- planner audit trail 与 scheduler timeline
- planner、subagent、tool 与 MCP 事件统一 run trace
- 确定性错误分类

### 预期交付物

- 面向 plan execution 的 policy evaluator
- planner timeline / audit API
- 面向 run、handoff、tool、MCP records 的统一 trace model
- 运营可读的 blocked / fallback / retry 原因

### 验收标准

- 被阻断的 item 会显示明确原因和恢复指引
- fallback 行为通过配置控制，而不是隐藏在代码路径中
- retries 有上限且会被记录
- planner run 可以通过审计日志重建

### 风险

- 如果规则在多个服务中重复定义，会导致策略行为不一致
- 如果阻断原因没有明确展示，会降低可用性

## Phase D：Skill Runtime 集成

### 目标

将 Skills 从 CRUD 资产升级为一等运行时参与者。

### 范围

- 编排过程中的 skill discovery
- 基于 planner item、user intent 和 required capabilities 的 skill matching
- 来自 Skills 的受控 prompt / tool / context injection
- skill activation policy 和 priority resolution
- skill audit 和命中归因

### 预期交付物

- `SkillRuntimeService` 或等效运行时选择器
- 每次运行的 skill activation records
- skill-to-tool / skill-to-prompt 绑定策略
- 覆盖 matching、priority conflict 和 disabled skill fallback 的测试

### 验收标准

- 运行时可以解释为什么选择了某个 skill
- 在候选项冲突时，skill selection 结果仍然是确定性的
- 禁用或无效的 skills 不会破坏主执行链

### 风险

- Prompt 无控制膨胀
- 重叠 skills 导致行为不可预测
- 如果不记录命中结果，归因能力会很弱

## Phase E：学习治理

### 目标

将当前 feedback 与 learning 闭环升级为受治理的学习系统，使其具备可评估、可版本化、可回滚、可按域隔离的能力。

### 范围

- learning quality score
- conflict detection 和 resolution workflow
- versioning 与 approval state
- rollback / disable controls
- domain / tenant / project isolation
- learning hit attribution 和 effect evaluation

### 预期交付物

- 受治理的 learning model 扩展
- 面向已提升 runtime knowledge 的 review workflow
- hit / effect attribution records
- learning analytics 与 conflict APIs

### 验收标准

- 单条 learning 可以禁用或回滚，而不删除历史
- 冲突的 learnings 会被显式暴露
- 运行时能够归因响应使用了哪些 learning entries
- learning quality 可以排序并复核

### 风险

- 噪声反馈污染运行时 prompts
- 冲突 learnings 静默降低输出质量
- learning 审批缺乏明确 owner

## Phase F：运营端 UX 与产品化

### 目标

将框架收口为一个面向运营者可用的 Demo，而不只是工程骨架。

### 范围

- planner timeline UI
- scheduler state panel
- MCP health dashboard 与调用历史
- learning review console
- 与 planning / operations 相关的更丰富 command palette 集成

### 验收标准

- 运营者可以理解 agent 为什么执行、阻断、重试或失败
- 核心治理状态无需查看原始日志即可可视化
- Demo 可以作为可复用平台展示，而不是隐藏的后端框架

## 推荐实施顺序

### Track 1：Runtime Core

1. Phase A
2. Phase B
3. Phase C

### Track 2：Intelligence Governance

1. Phase D
2. Phase E

### Track 3：Productization

1. Phase F

## 当前最重要的下一步

最关键的下一项实现是：

1. 先完成 Phase A 的真正多智能体调度器

之所以优先做这件事：

- 当前 planner + 伪 subagent 模型已经接近自然上限
- 没有真正的 scheduler，planner 无法成为中心执行层
- MCP、skills 和 learning governance 都会从更强的 parent / child runtime 边界中受益

## 下一轮迭代的完成定义

只有同时交付以下内容，下一轮实现才能视为完成：

1. planner item 到 child execution 的模型
2. scheduler runtime service
3. fan-out / collect / merge 事件流
4. 覆盖成功和部分失败的后端回归测试
5. 进度日志更新和 docs 索引同步
