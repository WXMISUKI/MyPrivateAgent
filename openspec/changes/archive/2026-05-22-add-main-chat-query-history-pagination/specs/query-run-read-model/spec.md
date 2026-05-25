## ADDED Requirements

### Requirement: Query History Read Model

系统 SHALL 支持 `main_chat` 的 query summary history 读取边界，以便后续治理历史浏览和分页能力扩展。

#### Scenario: Query History Browse

- **WHEN** 调用方需要读取超出 `recent_queries` 范围的 query 摘要历史
- **THEN** 系统 SHALL 提供 dedicated history read model
- **AND** history read model 不得要求前端从全量 timeline 本地重建 query 列表

### Requirement: Separation of Summary, Detail, and History

系统 SHALL 保持 recent summary、single-query detail、query history 三层职责分离。

#### Scenario: Recent Summary

- **WHEN** 调用方只需要最近若干次 query 概览
- **THEN** 系统 SHALL 继续通过 `recent_queries` 暴露 lightweight summary

#### Scenario: Single Query Detail

- **WHEN** 调用方需要某一个 `query_id` 的生命周期详情
- **THEN** 系统 SHALL 继续通过 `main_chat_query_detail` 提供 dedicated detail contract

#### Scenario: History Expansion

- **WHEN** 调用方需要跨多个 query 的历史列表
- **THEN** 系统 SHALL 通过 dedicated history read model 提供
- **AND** 不得让 `recent_queries` 或 `main_chat_query_detail` 混承担 history 职责

### Requirement: Pagination-Friendly History Contract

系统的 query history 读取边界 SHALL 为后续分页或 cursor 扩展保留空间。

#### Scenario: History Pagination

- **WHEN** 后续实现 query history endpoint
- **THEN** contract SHALL 至少支持分页元数据或 cursor 元数据
- **AND** item 字段集合应保持与现有 `recent_queries` 可兼容映射
