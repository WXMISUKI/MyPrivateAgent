## Why

`main_chat` 的 query/read model 已经从前端临时推导收口到后端正式 contract，但整体 read model 仍然分散在 `runtime-profile`、dedicated endpoint 和前端兼容逻辑之间。下一阶段需要继续把 query/detail/history 这条链条后端化，减少前端推导和重复解释。

## What Changes

- **收口 Query/Run Read Model 边界**
  - 明确 `main_chat_trace_overview`、`main_chat_query_detail`、`main_chat_query_history`、`recent_queries` 的职责分工。
  - 让 `query detail` 和 `query history` 成为稳定 read model，而不是前端临时聚合结果。
- **强化 dedicated read model**
  - 继续以 dedicated endpoint 作为主扩展路径。
  - 保持 `runtime-profile` 的兼容字段，但不再让它承担主要增长压力。
- **统一前端消费**
  - `RuntimeSurfacePanel` 与 `GovernanceTimelinePanel` 共享同一份 query/detail/history contract interpretation。
  - 降低前端各自维护兼容 fallback 的必要性。
- **边界收口**
  - 维持 `recent_queries` 作为 lightweight summary。
  - 维持 `main_chat_query_history` 作为分页/长历史 read model。
  - 不把 history 复杂度继续推回通用 timeline 本地重建。

## Capabilities

### New Capabilities
- `query-run-read-model-hardening`: 强化 `main_chat` query/detail/history 的后端 read model 收口、dedicated endpoint 边界和前端统一消费方式。

### Modified Capabilities
- `query-run-read-model`: 本次变更进一步强化 query/detail/history 的职责边界和 dedicated endpoint 主路径。

## Impact

- **Backend**
  - `backend/services/runtime_surface_service.py`
  - `backend/routers/health.py`
  - `backend/services/main_chat_query_control_service.py`
  - `backend/services/query_control_plane_service.py`
  - `backend/services/query_control_timeline_service.py`
- **Frontend**
  - `frontend-vue/src/components/RuntimeSurfacePanel.vue`
  - `frontend-vue/src/components/GovernanceTimelinePanel.vue`
  - `frontend-vue/src/components/MainChatQueryHistoryPanel.vue`
  - `frontend-vue/src/components/MainChatQueryDetailPanel.vue`
- **Documentation**
  - `openspec/specs/query-run-read-model/spec.md`
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`

