## Why

Runtime Surface 和 Governance Timeline 已经共享了 `main_chat` 的部分 query/detail 解释逻辑，但治理视图之间的 domain、filter、drill-down 和 snapshot 语义仍存在分散实现。下一阶段需要把这些治理入口统一起来，避免同一个事件在不同面板里被重新解释。

## What Changes

- **收口治理视图语义**
  - 统一 `main_chat / framework_adapter / mcp / permission / scheduler` 的治理入口表达。
  - 统一 route filter、overview card、detail contract、snapshot 复制语义。
- **统一 contract interpretation**
  - `RuntimeSurfacePanel` 与 `GovernanceTimelinePanel` 共享同一份 interpretation 逻辑。
  - 避免各自维护语义近似但实现不同的辅助函数。
- **收口交互路径**
  - 明确 summary -> detail -> timeline drill-down 的稳定跳转方式。
  - 让治理视图的路由态只承载观察焦点，不承担业务对象定义。
- **为后续治理台扩展留边界**
  - 统一治理入口后，再考虑是否增加独立 query 级视图或更强聚合面板。

## Capabilities

### New Capabilities
- `governance-view-unification`: 统一 Runtime Surface 与 Governance Timeline 的治理入口、过滤、钻取和 snapshot 语义。

### Modified Capabilities
- `query-run-read-model`: 其前端消费语义会受治理视图统一化影响，但核心 read model 契约不变。

## Impact

- **Frontend**
  - `frontend-vue/src/components/RuntimeSurfacePanel.vue`
  - `frontend-vue/src/components/GovernanceTimelinePanel.vue`
  - `frontend-vue/src/components/GovernanceTimelineEventCard.vue`
  - `frontend-vue/src/components/GovernanceTimelineFilters.vue`
  - `frontend-vue/src/components/MainChatQueryHistoryPanel.vue`
  - `frontend-vue/src/components/MainChatQueryDetailPanel.vue`
- **Backend**
  - `backend/services/runtime_surface_service.py`
  - `backend/services/main_chat_query_control_service.py`
- **Documentation**
  - `docs/architecture/runtime_contracts.md`
  - `docs/architecture/current_architecture.md`
  - `docs/roadmap/next_phase_hardening.md`

