# Proposal: 试点 subagent_lane recent summary

## Why

当前高层边界判断已经明确：

- `main_chat` 是唯一完整实现了 `recent summary / query detail / query history / query workspace` 四层能力的 channel
- `subagent_lane` 已通过 `recent summary` readiness 评估
- 但它当前仍不进入 `query detail / query history / query workspace`

这意味着现在最稳的下一步，不是继续抽象多层能力，而是做一个**非常克制的轻量试点**：

- 只验证 `subagent_lane` 能否进入 `recent summary` 层
- 不越级进入更深的 query 模型

这样做的好处是：

1. 能验证 `main_chat` 以外的 channel 是否真的能复用 query 模式的第一层能力
2. 不会因为 scope 过大，把 `subagent_lane` 提前拉进 detail/history/workspace 的复杂度
3. 能给后续 `external_adapter` 是否跟进提供真实参照

## What Changes

本次变更拟定义：

1. `subagent_lane recent summary` 的最小 contract 目标
2. 试点的前端/后端落点
3. 不越级的边界
4. 验证完成线

## Non-Goals

本次变更**不**包括：

- 不新增 `subagent_lane` dedicated detail contract
- 不新增 `subagent_lane query history`
- 不新增 `subagent_lane workspace`
- 不重写 subagent lane timeline 事件流
- 不改变 scheduler fan-out 的既有合并协议

## Expected Outcome

完成后应达到：

- `subagent_lane` 在治理视角中，第一次具备正式 `recent summary` 候选实现
- 团队能据此判断这条线是否适合继续推进到 `query detail`
- roadmap 对“多 channel 试点”的优先级排序更稳

## Risks

1. 如果 summary 字段过浅，试点可能无法提供足够治理价值。
2. 如果试点 scope 膨胀，容易越级做成 detail/history。
3. 如果前后端语义没有保持克制，可能又会提前复制 `main_chat` 的产品壳。

## Verification

至少需要验证：

1. `subagent_lane` 的 summary contract 是否稳定
2. 前端是否能在不引入 detail/history 的前提下消费它
3. 文档和 roadmap 是否明确它只是 `recent summary` 试点，而不是完整 query 模式推广
