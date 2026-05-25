# Design: 试点 subagent_lane recent summary

## Overview

本次设计只做一件事：

**让 `subagent_lane` 进入 `recent summary` 层的轻量试点。**

也就是说，我们只验证这条线是否具备：

- 稳定 `query_id`
- latest stage
- latest summary
- latest timestamp

这些最轻的一层 query summary 能力。

## Scope Boundary

### In Scope

- 为 `subagent_lane` 定义 `recent summary` 候选形态
- 判断现有 Query Control timeline 是否足够支撑 summary 聚合
- 评估前端最小展示位置
- 补验证完成线

### Out of Scope

- dedicated detail contract
- query history 分页
- workspace 壳
- scheduler / subagent 执行协议重构

## Proposed Shape

建议以与 `main_chat_trace_overview.recent_queries` 类似的最小摘要形态试点：

- `query_id`
- `latest_stage`
- `latest_summary`
- `latest_timestamp`
- `recording_state`

可选但需克制的字段：

- `last_success_stage`
- `last_warning_stage`

当前不建议带入：

- 最近事件列表
- stage chain
- dedupe keys
- snapshot 回放增强字段

## Candidate Landing

### Backend

优先考虑：

- `query_control` 已有 persisted trace
- 在现有 read model assembler 中补 `subagent_lane recent summary` 候选 contract

但只作为试点：

- 不要求本轮抽出通用多 channel summary service
- 不要求本轮立刻进入 Runtime Surface 顶层总览

### Frontend

优先考虑：

- 在现有治理视图中增加轻量入口或卡片
- 只展示 recent summaries

不建议：

- 新建 subagent workspace
- 复制 `main_chat` 的 detail/history 面板

## Success Criteria

试点成功的标志是：

1. `subagent_lane` 的 summary 字段足够稳定
2. 团队确认这条线值得继续评估 `query detail`
3. 试点没有越级变成 history/workspace 能力

## Exit Criteria

本次设计完成时，应能明确：

1. `subagent_lane recent summary` 的最小 contract
2. 前端候选落点
3. 本轮明确不做哪些更深层能力
