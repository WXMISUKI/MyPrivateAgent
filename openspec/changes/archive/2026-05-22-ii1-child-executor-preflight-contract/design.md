## Context

我们已经完成了 child run relationship seam、continuation recovery protocol、registry-backed reattach、binding catalog、child output merge behavior、parent merge state surface 和 governance overview run state surface。
当前还缺的是一个稳定的 preflight contract，用来判断 `delegate_run(...)` 是否可以从“关系 seam”升格到真实 child executor 前置条件已满足。

这个 contract 会跨越 SDK、registry、runtime surface、router 和前端消费面，因此不适合继续散落在内部 helper 里。

## Goals / Non-Goals

**Goals:**

- 提供一个机器可读的 child executor preflight contract。
- 统一表达 binding 可解析性、worker backend 可用性、merge semantics 完整性、promotion readiness。
- 让 Runtime Surface 与 Facade 共享同一套 preflight 结果，而不是各自推导。
- 保持当前 `delegate_run(...)` 仍然只负责 relationship seam，不直接执行真实 child executor。

**Non-Goals:**

- 不实现真实 child executor 调度。
- 不引入新的 worker runtime backend。
- 不重写 continuation registry 或 persistence seam。
- 不改变 child output merge behavior 的既有 contract。

## Decisions

### 1. Preflight 作为独立 read model，而不是继续挂在 metadata 里

Reasoning:

- `metadata` 适合承载执行过程中的附属信息，但 preflight 是稳定判断结果，应该可被 SDK、Runtime Surface 和治理视图共同消费。
- 独立 contract 更容易做版本控制、测试和后续演进。

Alternatives considered:

- 继续塞进 `delegate_run` metadata：改动小，但会继续让 contract 漂移。
- 仅放在前端解释层：会让“是否可 promotion”失去后端真源。

### 2. 以 binding catalog + merge semantics + backend readiness 作为 preflight 输入

Reasoning:

- 当前最稳定的升格判断依赖三类信息：
  - continuation binding 是否可解析
  - child merge contract 是否完整
  - worker runtime backend 是否就绪
- 这三类输入已经分别有自己的 seam，preflight 只做汇总判断。

Alternatives considered:

- 只看 binding catalog：无法判断 merge semantics 是否足够。
- 直接看 `delegate_run(...)` 返回值：会把 relationship seam 和 promotion gate 混为一谈。

### 3. 只定义最小 promotion modes

Reasoning:

- 第一版只需要回答“当前是否 promotion candidate”和“当前缺什么”。
- 过早做复杂策略引擎会把 preflight 变成另一个 runtime scheduler。

建议最小模式：

- `relationship_only`
- `promotion_candidate`
- `blocked_missing_binding`
- `blocked_missing_merge_semantics`
- `blocked_backend_unavailable`

### 4. 前端只读展示 preflight，不反向解释 promotion 逻辑

Reasoning:

- 这里的真源应始终是后端 contract。
- 前端只负责把 preflight 结果展示在 Runtime Surface / child executor workspace，不再重复判断。

## Risks / Trade-offs

- [Risk] preflight contract 和现有 `delegate_preflight` / embedded runtime boundaries 可能部分重叠 → Mitigation: 统一版本号与字段归属，只保留一个正式结果出口。
- [Risk] 过早把 preflight 做得太宽会增加 contract 漂移面 → Mitigation: 先只覆盖 binding、merge semantics、backend readiness 三类输入。
- [Risk] 前端如果继续自己推导 promotion 状态，会和后端结果打架 → Mitigation: 前端只能读 contract，不做二次判断。

## Migration Plan

1. 先在 SDK / service 层建立正式 preflight contract builder。
2. 接入 Runtime Surface contract。
3. 前端只读展示 preflight 结果。
4. 补 focused tests 固定 promotion candidate 与 blocked 路径。
5. 若未来需要更复杂策略，再在不破坏现有 contract 的前提下扩展字段。

## Open Questions

- 是否需要把 `delegate_preflight` 与 `embedded_runtime_boundaries` 合并为同一层 read model？
- 是否要让 preflight 直接输出 `promotion_next_step` 还是只输出 `recommended_next_step`？
- 未来真实 child executor 的 promotion gate 是否要与 approval gate 共享一部分字段？
