## Why

`GovernanceTimelinePanel` 已经同时承担治理摘要、过滤、workspace、事件流和多个 summary/action 卡片编排，组件体积继续增长会让后续治理功能越来越难加，也越来越难测。现在适合先把它收回成主编排入口，让具体区块各自有更清晰的边界。

## What Changes

- 保持 `GovernanceTimelinePanel` 的数据加载、路由同步和主编排职责不变。
- 把 main chat workspace、recent snapshot commands、summary/action 区块、event list 区块继续拆成更清晰的子组件边界。
- 允许面板内部结构调整和少量模板整理，但不改治理语义和外部行为。
- 保持现有治理事件、过滤、复制视图、快照命令等交互可用。
- 同步补充 focused tests，确保拆分后仍然覆盖关键治理交互。

## Capabilities

### New Capabilities
- `governance-timeline-panel-slimming`: 将 `GovernanceTimelinePanel` 收敛为主编排入口，并把治理面板中的大块 UI/workspace 逻辑下沉到更清晰的子组件边界。

### Modified Capabilities
- `governance-view-unification`: 该能力下的治理视图实现将进一步强调“主编排 + 子区块组件化”的结构边界，但对外治理语义不变。

## Impact

- Frontend: `frontend-vue/src/components/GovernanceTimelinePanel.vue` 及其相关子组件与测试。
- Docs: `docs/roadmap/next_phase_hardening.md`, `docs/architecture/runtime_contracts.md`.
- OpenSpec: 新增 `governance-timeline-panel-slimming` 能力规格，作为治理面板继续瘦身的约束真源.
