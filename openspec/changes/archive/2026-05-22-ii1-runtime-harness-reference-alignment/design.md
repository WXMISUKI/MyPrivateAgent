## Context

通过初步阅读，两个参考源的价值并不相同：

### `learn-claude-code`

这个仓库本质上是教学型 harness 拆解，更强调：

- agent loop
- tool runtime
- permission / hooks / memory / prompt construction
- error recovery
- durable task vs runtime task split
- teammate / subagent / task lane 的概念边界

它非常适合拿来做“架构语言”和“演化顺序”的参照，而不是直接复用实现。

### `claude-code`

这个仓库更接近真实产品控制面，更强调：

- swarm teammate backend abstraction
- in-process runner
- reconnection / session recovery
- permission sync
- pane / tmux / iTerm backend executor
- teammate lifecycle / mailbox / session hydration

它非常适合拿来做“真实控制面机制”的参照，但里面有大量产品化、历史兼容和平台接线细节，不适合直接照搬到当前项目。

## Goals / Non-Goals

**Goals:**

- 明确参考源在我方项目中的不同职责
- 明确当前项目应该吸收的成熟模式
- 明确不该照搬的接口、命名和产品耦合
- 把这些结论沉淀成后续 II-1.6 / child executor / worker runtime 的前置约束

**Non-Goals:**

- 不把外部仓库代码直接迁入当前项目
- 不在这一步实现 child executor
- 不修改现有 Runtime Core 领域语义以贴合外部项目命名

## Decisions

### 1. `learn-claude-code` 作为概念分层与术语校正参考

Reasoning:

- 它对 loop、recovery、runtime task、subagent、teammate 的分层解释清晰。
- 很适合用来检查我们是否把 durable task / runtime slot / worker identity 混在一起。

### 2. `claude-code` 作为控制面机制参考

Reasoning:

- 它在 backend abstraction、permission sync、reconnection、in-process runner 方面更接近真实复杂运行时。
- 这些正是我们后续 child executor 和 worker runtime 容易重复造轮子的地方。

### 3. 只借鉴模式，不照搬领域语义

Reasoning:

- 当前项目已经有自己的 Runtime Core / Governance / Approval / Query-Run Read Model 语义。
- 如果直接照搬外部命名，很容易让我方领域模型漂移。

## Recommended Reference Slices

后续实现优先参考这些切面：

1. `learn-claude-code`
   - `docs/zh/s11-error-recovery.md`
   - `docs/zh/s13a-runtime-task-model.md`
   - `docs/zh/s15-agent-teams.md`
   - `docs/zh/team-task-lane-model.md`

2. `claude-code`
   - `src/utils/swarm/backends/InProcessBackend.ts`
   - `src/utils/swarm/inProcessRunner.ts`
   - `src/utils/swarm/permissionSync.ts`
   - `src/utils/swarm/reconnection.ts`
   - `src/utils/swarm/backends/registry.ts`

## Risks / Trade-offs

- [Risk] 参考过多会让当前设计过早复杂化。  
  Mitigation：每一轮只吸收与当前阶段直接相关的切面。

- [Risk] 团队可能误把参考源当成“应该复刻的目标产品”。  
  Mitigation：spec 中明确“借模式，不借产品耦合；借分层，不借命名”。

- [Risk] 外部项目中与当前系统无关的历史兼容逻辑会污染实现。  
  Mitigation：所有吸收动作都必须先映射到我方 OpenSpec 变化任务，不允许直接搬运。

## Migration Plan

1. 先固化 reference alignment 规范
2. 把 II-1.6 child executor preflight 的参考切面明确进任务说明
3. 后续每个阶段实现，只允许引用本 spec 中定义的参考切面

