# Proposal: 增加 main_chat Query History Pagination

## Why

当前 `main_chat` 的 query 级治理观察已经具备：

- `recent_queries` 最近 N 次摘要
- `main_chat_query_detail` dedicated endpoint
- `query_id` drill-down

但还缺一个稳定的**历史读取边界**。现在的 `recent_queries` 更适合作为 lightweight summary，而不适合承担：

- 更长时间窗口的回溯
- 分页浏览
- 后续治理台历史审查

如果继续只依赖 `recent_queries`，会出现两个问题：

1. query 历史能力会继续卡在“最近几条摘要”层面
2. 后续一旦要补完整历史，容易再次把复杂度推回前端或 `runtime-profile`

## What Changes

本次变更拟定义：

1. `main_chat` query summary history 的 dedicated read model 边界
2. 分页型 query history endpoint 的 contract 轮廓
3. `recent_queries` 与 `history` 的职责分工
4. 前端后续如何从最近摘要过渡到历史浏览

## Non-Goals

本次变更**不**包含：

- 不直接实现数据库索引优化
- 不一次性实现完整治理台新页面
- 不替换现有 `recent_queries`
- 不改变 `main_chat_query_detail` 现有字段语义
- 不扩展到其他 channel 的历史分页

## Expected Outcome

完成后应达到：

- `recent_queries` 保持“轻摘要”
- query history 成为独立可扩展的 read model
- 后续实现分页接口时，不需要重新定义边界

## Risks

1. 如果把 summary 和 history 边界写不清，容易重复建设两个近似接口。
2. 如果直接引入太重的交互需求，scope 会过大。
3. 如果不约束后向兼容，现有 Runtime Surface 可能被迫同步重构。

## Verification

本次规格完成后至少应能验证：

1. history 与 recent summary 的边界是否清晰
2. dedicated history endpoint 的 contract 是否足够支撑后续实现
3. roadmap / canonical spec / OpenSpec README 是否同步
