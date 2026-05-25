## Why

`main_chat_query_detail` 和 `main_chat_query_history` 已经被统一解释为共享 read model，但治理视图里还看不到这层契约的自描述信息。现在补一层轻量可见 metadata，可以让 Runtime Surface 和 Governance Timeline 在不改变布局的前提下，一眼确认自己读的是哪一层 read model。

## What Changes

- 在 query detail/history 相关面板里轻量展示 read model metadata。
- 保持现有列表、摘要、detail 卡片结构不变，只增加一行或一小块解释性信息。
- 不改变后端 contract，不改变路由，不改变 workspace 结构。
- 同步更新 focused tests，让 metadata 可见性成为明确的治理视图行为。

## Capabilities

### New Capabilities
<!-- No new capability. This change is a visibility supplement to an existing governance view contract. -->

### Modified Capabilities
- `governance-view-unification`: shared contract interpretation is extended so governance views visibly surface query read model metadata without changing layout or navigation.

## Impact

- Frontend components: `frontend-vue/src/components/RuntimeSurfacePanel.vue`, `frontend-vue/src/components/GovernanceTimelinePanel.vue`, `frontend-vue/src/components/MainChatQueryDetailPanel.vue`, `frontend-vue/src/components/MainChatQueryHistoryPanel.vue`。
- Frontend tests: `frontend-vue/src/components/__tests__/RuntimeSurfacePanel.test.js`, `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`, `frontend-vue/src/components/__tests__/MainChatQueryDetailPanel.test.js`, `frontend-vue/src/components/__tests__/MainChatQueryHistoryPanel.test.js`。
- Docs truth source: `docs/architecture/runtime_contracts.md`, `docs/roadmap/next_phase_hardening.md`。
