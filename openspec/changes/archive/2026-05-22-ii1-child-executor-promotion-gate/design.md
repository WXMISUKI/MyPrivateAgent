## Context

当前我们已经把 child executor preflight、binding catalog、recovery protocol、merged semantics 和 parent state surface 都做到了可运行状态，但它们仍分散在不同 contract 里。
下一步要解决的是：当调用方问“现在能不能把 `delegate_run(...)` 提升成真实 child executor？”时，系统应返回一个统一的 gate contract，而不是让 SDK / Runtime Surface / Facade 各自解释 preflight。

## Goals / Non-Goals

**Goals:**

- 提供一个稳定的 child executor promotion gate contract。
- 统一 gate 的 allowed / blocked、failure reason、executor path、blockers 与 next step。
- 让 Runtime Surface、Facade 和 SDK 使用同一个 gate 真源。
- 保持 `delegate_run(...)` 在 gate 未通过前仍是 relationship seam。

**Non-Goals:**

- 不实现真实 child executor 调度。
- 不改变 continuation recovery protocol。
- 不改 child output merge behavior 的既有语义。
- 不引入新的 worker backend。

## Decisions

### 1. Gate 作为 preflight 的后置真源，而不是另一套平行判断

Reasoning:

- preflight 已经负责“是否具备升格所需条件”的原子检查。
- gate 的职责是把 preflight 结果、workspace backend 状态、binding 解析和 merge contract 收成一个最终可消费决策。

Alternatives considered:

- 直接让 preflight 变成最终判断：会让 preflight 职责过宽。
- 让前端自行计算 gate：会破坏 contract 真源一致性。

### 2. Gate 输出最小稳定字段

Reasoning:

- gate 的核心任务是决策，不是把所有内部检查细节都外泄。
- 最小稳定字段更适合后续进入 Runtime Surface 和治理视图。

建议最小字段：

- `gate_status`
- `allowed`
- `failure_reason`
- `executor_path`
- `blockers`
- `recommended_next_step`

### 3. 允许 gate 复用 preflight 但不复用前端逻辑

Reasoning:

- gate 应该直接消费 SDK / service 的 preflight 和 backend readiness 结果。
- 前端只读 gate contract，不再重建升格逻辑。

### 4. Runtime Surface 的展示应以 gate contract 为主，preflight 作为辅助上下文

Reasoning:

- preflight 是解释“为什么”，gate 是解释“最终能不能升格”。
- 在治理视图里，gate 更适合成为 main surface，preflight 作为辅助块。

## Risks / Trade-offs

- [Risk] gate 与 preflight 字段重叠过多，导致 contract 冗余 → Mitigation: gate 保留决策字段，preflight 保留检查字段，避免双写全部明细。
- [Risk] 过早把 gate 直接接到真实 executor，会让 promotion contract 失去独立性 → Mitigation: 第一版只做 gate 真源，不做 executor 执行。
- [Risk] 前端继续自己判断 allowed/blocking → Mitigation: 只消费 backend contract，禁止 UI 重算。

## Migration Plan

1. 在 SDK / service 层定义正式 gate contract builder。
2. 在 runtime profile / governance overview 中暴露 gate。
3. 前端切换为只读 gate contract。
4. 补 focused tests 覆盖 blocked / allowed 两路径。
5. 若未来要升级真实 child executor，再在 gate 之上做 executor dispatch。

## Open Questions

- gate 是否要成为 `governance_overview.child_executor_gate` 还是 `embedded_runtime_boundaries.delegate_gate` 的后续替代？
- gate 与 `delegate_route` / `delegate_binding` 是否要保留并列展示，还是只保留决策结果？
- 未来真实 child executor 升格时，是否需要引入独立 `promotion_timestamp` 或 `promotion_actor` 字段？
