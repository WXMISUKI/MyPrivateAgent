## Context

当前 MyPrivateAgent 已经形成 Runtime Core、Capability Layer、Governance Layer、Delivery Layer 四层结构，但核心术语仍在多个模块中以近义词、别名或展示文案形式并存。最明显的漂移点是 `query / run / child_run / child_execution_id / scheduler_run / approval / artifact / trace / audit`。

治理前端已经完成 `main_chat` query history/workspace 的收口，说明局部浏览壳的价值开始下降。下一阶段需要回到更底层的 Runtime Core 语义，否则 Query/Run Read Model 和治理视图会继续被命名不一致反向拖累。

约束：

- 不改后端业务语义，只收口术语和对象边界。
- 不把前端治理台作为术语定义源。
- 文档与 contract 必须先于后续实现收口。

## Goals / Non-Goals

**Goals:**

- 固化 Runtime Core 的正式术语和对象模型。
- 明确 `child_run_id`、`child_execution_id`、`child_display_id` 的关系。
- 明确 `query` 与 `run` 的职责边界，避免把同一生命周期拆成多个不一致概念。
- 明确 `artifact` 与 `snapshot_ref`、`trace` 与 `audit` 的关系。
- 明确 `durable state` 与 `runtime state`、`control plane` 与 `execution plane` 的分层。
- 同步更新架构文档、change 记录和后续实现约束。

**Non-Goals:**

- 不实现新的运行时能力。
- 不重构 `main_chat` history 的前端交互。
- 不替换现有 query/read model contract。
- 不引入新的外部依赖或新的数据持久化 schema。
- 不强行一次性删除所有兼容字段；先完成术语与 contract 收口，再决定后续淘汰节奏。

## Decisions

### 1. 以 `child_run_id` 作为正式术语，`child_execution_id` 作为兼容键，`child_display_id` 作为正式 display field

原因：

- `child_run_id` 已经出现在 Runtime Core、前端展示、治理视图和测试中，是最接近正式主术语的选择。
- `child_execution_id` 在 repository / scheduler 语义里仍有历史存量，直接删除风险过高。
- 先统一主术语，再把兼容键限制在实现层，是最稳的迁移方式。
- `child_display_id` 已开始进入 Runtime Surface、scheduler 对外 contract、subagent/query-control 事件、framework adapter timeline、approval request 与 server serialization；它更适合作为跨消费面的统一稳定展示键，而不是继续让外层各自写 fallback。

备选方案：

- 继续双名并存：短期最省事，但会继续扩大术语漂移。
- 改成 `child_execution_id` 作为正式术语：与现有前端和 runtime contract 现状不一致，迁移成本更高。
- 把 `child_display_id` 继续视为前端临时派生字段：短期改动最少，但会导致 approval、adapter timeline、query-control payload、server serialization 等对外 contract 继续各自决定 fallback 逻辑。

### 2. 用“生命周期边界”定义 `query`，用“执行实例边界”定义 `run`

原因：

- `query` 对用户和治理台更像一次完整请求生命周期。
- `run` 更像 Runtime Core 的执行单元，属于 query 生命周期中的执行体。
- 这套区分能同时支撑 Query Control、read model、runtime state 和治理回放。

备选方案：

- 把 query 和 run 合并成同一个术语：会丢掉执行实例与请求生命周期的层次。
- 继续靠上下文区分：短期可行，但长期会在 contract、测试和文档里反复打架。

### 3. `artifact` 保持“可引用结果对象”，`snapshot_ref` 作为其一个常见引用形态

原因：

- `artifact` 是更上位的运行产物对象。
- `snapshot_ref` 是治理、回放、复制命令里最常见的展示/引用入口，但不应反过来定义 artifact 全部语义。

备选方案：

- 把 `snapshot_ref` 当成 artifact 的同义词：会抹平治理和持久化引用之间的边界。

### 4. `trace` 与 `audit` 保持并列但不复制

原因：

- `trace` 负责执行证据流。
- `audit` 负责治理记账流。
- 两者都进入治理视图，但不应默认互为完整拷贝。

备选方案：

- 只保留一套事件流：简化很多，但会破坏现有治理与执行观察的分工。

### 5. `durable state` 与 `runtime state` 作为跨层约束写入文档

原因：

- 当前最容易出问题的不是字段，而是“谁能代表事实”。
- 把状态分层写清后，前端 route/query focus 就不会被误当成后端事实。

## Risks / Trade-offs

- [Risk] 这次只做语义收口，代码层兼容字段仍会并存。 → [Mitigation] 在架构文档与 runtime contracts 中明确谁是正式术语、谁是兼容键。
- [Risk] 如果后续 read model 继续增长，术语收口后仍可能出现新漂移。 → [Mitigation] 将新增 contract 的术语准入规则写进本次 spec 的 tasks 和文档真源。
- [Risk] 前端展示层可能短期仍需显示历史别名。 → [Mitigation] 允许 display label 兼容，但 contract 字段与对象边界必须统一。

## Migration Plan

1. 更新 `docs/architecture/runtime_contracts.md`，把正式术语与漂移点判断写成真源。
2. 更新 `docs/architecture/current_architecture.md`，把 Runtime Core 对象边界写成架构总览。
3. 更新 `docs/change/2026-05-16-phase-g-agent-runtime-reference-alignment.md`，记录这次收口决策。
4. 如果 roadmap 仍在描述 `main_chat` 为重点，补一句“下一阶段优先回到 Runtime Core 术语与 read model 收口”。
5. 明确 `child_display_id` 是正式 display field：默认优先等于 `child_run_id`，必要时才回退 `child_execution_id`；审批对象、治理 payload、adapter timeline 与 server serialization 若暴露 child 身份，应直接透出它。
6. 后续实现阶段只允许在正式术语上新增 contract，不再扩散近义词。

Rollback strategy:

- 如果文档收口与后续实现发生冲突，优先回滚实现，不回滚术语定义。
- 兼容字段在一段时间内继续保留，避免一次性破坏现有前端和测试。

## Open Questions

- `artifact` 与 `snapshot_ref` 是否需要在后续阶段进一步拆成更明确的层次命名？
- `trace` 和 `audit` 的前端展示是否应继续保持并列，还是未来在某些视图中统一降噪？
- `child_execution_id` 的兼容窗口是否需要在下一阶段收敛时间表里显式列出？
