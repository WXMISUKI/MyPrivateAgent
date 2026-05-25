## Why

`main_chat_query_detail` 和 `main_chat_query_history` 现在已经有了自描述 metadata，但前端治理解释层还在不同组件里各自消费并组合这些合同。继续放任这种分散解释，会让 Runtime Surface、Governance Timeline、History workspace 对同一 read model 的理解继续漂移。

## What Changes

- 统一 `main_chat_query_detail` / `main_chat_query_history` 的前端 normalize 结果，确保同一份 read model contract 被同一套解释逻辑消费。
- 将 detail/history 的自描述 metadata 贯穿到共享解释层，而不是只停留在后端返回值里。
- 保持现有治理视图布局不变，只收口字段解释、默认值和 contract normalization。
- 同步更新 focused tests 和文档真源，确保前端解释口径与后端契约一致。

## Capabilities

### New Capabilities
<!-- No new capability. This change only unifies interpretation of existing read models. -->

### Modified Capabilities
- `governance-view-unification`: shared contract interpretation is tightened so query detail/history normalization is sourced from one helper path.

## Impact

- Frontend code: `frontend-vue/src/services/mainChatQueryDetail.js`, `frontend-vue/src/services/mainChatQueryHistory.js`, `frontend-vue/src/services/governanceViewInterpretation.js`, `frontend-vue/src/components/RuntimeSurfacePanel.vue`, `frontend-vue/src/components/GovernanceTimelinePanel.vue`.
- Frontend tests: `frontend-vue/src/services/__tests__/mainChatQueryGovernance.test.js`, `frontend-vue/src/components/__tests__/RuntimeSurfacePanel.test.js`, `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`.
- Docs truth source: `docs/architecture/runtime_contracts.md`, `docs/roadmap/next_phase_hardening.md`.
