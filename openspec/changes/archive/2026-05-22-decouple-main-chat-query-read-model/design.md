# Design: 解耦 main_chat Query Read Model

## Overview

本次设计不是重做 Query Control，也不是重做治理视图，而是把当前已经跑通的 `main_chat query detail` 继续往“后端正式 read model”收紧。

设计原则：

1. `runtime-profile` 仍可保留 `main_chat_query_detail`，用于兼容现有面板
2. 但 dedicated endpoint 应成为 query 级详情的主读取路径
3. query detail 的字段解释逻辑在前端必须共用 helper
4. 后续分页历史接口应围绕 dedicated query read model 扩展，而不是继续把复杂度塞回 `runtime-profile`

## Affected Areas

### Backend

- `backend/services/runtime_surface_service.py`
  - 继续承担 query detail contract assembler
- `backend/routers/health.py`
  - 暴露 dedicated endpoint

### Frontend

- `frontend-vue/src/api/index.js`
  - 提供 dedicated query detail API 方法
- `frontend-vue/src/services/mainChatQueryDetail.js`
  - 作为统一 contract normalization helper
- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
  - query drill-down 优先读取 dedicated endpoint
- `frontend-vue/src/components/RuntimeSurfacePanel.vue`
  - 使用相同 helper，避免 contract 解释分叉

### Documentation

- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`
- `.specify/memory/constitution.md`

## Contract Boundary

### Current Stable Contract

`main_chat_query_detail` 当前稳定字段包括：

- `query_id`
- `recording_state`
- `stage_chain`
- `dedupe_keys`
- `recent_events`
- `latest_snapshot_id`
- `latest_warning_summary`
- `latest_stage`
- `latest_summary`
- `stage_count`
- `warning_count`
- `event_count`
- `reason`

### Forward Boundary

后续若扩展 `recent_queries` 分页历史接口，应保持：

- `recent_queries` 仍可作为 lightweight summary list 存在于 `main_chat_trace_overview`
- dedicated endpoint 负责 query-level detail
- history endpoint 若新增，应服务于 query summary list，而不是替代 detail endpoint

## Tradeoffs

### Why keep `runtime-profile` compatibility

因为当前 `RuntimeSurfacePanel` 已在用 profile 聚合上下文，完全移除会造成无必要的破坏性收口。

### Why introduce dedicated endpoint first

因为 dedicated endpoint 可以先把“query detail 是一等 read model”这件事定下来，比一次性做分页历史接口更稳。

### Why not add pagination now

因为当前 H-2 的真正目标是**先定边界**，而不是一次把所有 query 历史能力做完。

## Exit Criteria

设计完成的标志是：

1. query detail 主读取路径已独立
2. 前端共用同一 contract helper
3. 文档已经明确 dedicated endpoint 是未来 read model 扩展的主边界
4. 本轮没有把 scope 拉到分页历史接口实现
