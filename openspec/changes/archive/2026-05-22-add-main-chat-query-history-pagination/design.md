# Design: main_chat Query History Pagination

## Overview

本次设计不直接做实现，而是先把 query history 变成正式的下一层 read model。

核心思想：

- `recent_queries`：保留为 lightweight summary list
- `main_chat_query_detail`：保留为单 query detail
- `query_history`：新增为可分页的 query summary history

这样三层职责清晰：

1. overview 层看最近摘要
2. detail 层看单 query 详情
3. history 层看跨 query 的时间序列浏览

## Proposed Contract Boundary

### Current Stable Layers

- `main_chat_trace_overview.recent_queries`
- `main_chat_query_detail`

### New Layer

建议新增 dedicated history endpoint，对外返回：

- `items`
- `page`
- `page_size`
- `has_more`
- `next_cursor` 或等价分页游标
- 每个 item 至少包含：
  - `query_id`
  - `latest_stage`
  - `latest_summary`
  - `latest_timestamp`
  - `latest_snapshot_id`
  - `stage_counts`
  - `last_success_stage`
  - `last_warning_stage`
  - `recording_state`

## Why Cursor-Friendly Design

当前 trace 数据天然是时间序列，后续若 history 增长，cursor 比简单 page number 更稳。

但为了减少首轮复杂度，本次只要求：

- contract 必须允许后续支持 cursor
- 首轮实现是否先用 page/page_size，可在实现阶段再决定

## Compatibility Strategy

- `recent_queries` 不删除
- `RuntimeSurfacePanel` 当前仍可继续显示最近摘要
- 后续治理历史浏览可单独接 history endpoint

## Exit Criteria

本次设计完成时，应能明确：

1. recent summary、detail、history 三层边界
2. history endpoint 的字段集合
3. 后向兼容策略
4. 后续实现不需要再重开边界讨论
