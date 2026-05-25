# Proposal: 解耦 main_chat Query Read Model

## Why

当前 `main_chat` 的 query 级治理详情虽然已经具备正式后端 contract，但仍存在两个问题：

1. `runtime-profile` 仍然承担了过多 query 级 detail 读取职责，导致 profile 聚合接口继续膨胀。
2. `recent_queries` 仍然只适合“最近几次摘要”，尚未形成可扩展的 query 历史读取边界。

这会让 `H-2` 后续推进卡在一个中间状态：

- 后端已经开始做 read model
- 但 query 级数据面还没有完全从“大聚合 profile”中解耦出来

## What Changes

本次变更拟收口以下内容：

1. 把 `main_chat_query_detail` 明确为 query 级 dedicated read model，优先从独立接口读取。
2. 为 `recent_queries` 的后续分页/历史接口预留稳定 contract 边界。
3. 让 `RuntimeSurfacePanel` 与 `GovernanceTimelinePanel` 对 query detail 的解释逻辑共享同一 contract helper。
4. 在 roadmap / architecture / constitution 三处明确这一阶段的边界和停止条件。

## Non-Goals

本次变更**不**处理以下内容：

- 不进入数据库迁移或 trace 存储结构重构
- 不改动 Query Control stage 语义
- 不新增新的治理 UI 壳
- 不直接实现完整分页历史接口
- 不扩展到 `framework_adapter / mcp / scheduler` 的 query 级独立 read model

## Expected Outcome

完成后应达到：

- query 级详情从“profile 顺带带出来”变成“可独立读取的正式数据面”
- 前端不再需要为 query detail 维护多套解释逻辑
- 后续如果要补 `recent_queries` 分页接口，可以沿既有 read model 边界扩展，而不是再次回到前端推导

## Risks

1. 如果过度解耦，可能让当前 `runtime-profile` 和 dedicated endpoint 之间字段重复维护。
2. 如果 contract helper 不统一，前端可能仍然出现两个组件解释不一致。
3. 如果过早扩到分页历史接口，容易把本轮 scope 拉大。

## Verification

至少需要验证：

1. 后端 dedicated endpoint 的 contract 单测
2. 路由层 dedicated endpoint 的 API 单测
3. `GovernanceTimelinePanel` 是否优先消费 dedicated endpoint
4. `RuntimeSurfacePanel` 与 `GovernanceTimelinePanel` 是否共享同一 query detail helper
5. 文档是否同步更新到 roadmap / runtime_contracts / constitution 入口
