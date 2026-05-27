## Why

`GovernanceTimelinePanel` still owns a large focus summary template even after the main chat workspace was split out. Phase II calls for governance UI slimming so new governance signals do not keep growing the parent panel.

## What Changes

- Extract the focus summary grid from `GovernanceTimelinePanel` into a display-only child component.
- Keep route state, filter state, query state, clipboard actions, and backend contract interpretation in the parent.
- Add focused component coverage for rendering summary state and forwarding clear/copy actions.
- Update Phase II roadmap notes to record the new component boundary.

## Capabilities

### New Capabilities
- `governance-focus-summary-component-boundary`: Defines the frontend-only component boundary for the governance focus summary area.

### Modified Capabilities
- `governance-view-unification`: Clarifies that governance timeline parent panels SHALL keep orchestration while summary regions are allowed to move into display-only child components.

## Impact

- Affected frontend components:
  - `frontend-vue/src/components/GovernanceTimelinePanel.vue`
  - New `frontend-vue/src/components/GovernanceTimelineFocusSummaryGrid.vue`
- Affected tests:
  - New focused component test under `frontend-vue/src/components/__tests__/`
  - Existing `GovernanceTimelinePanel` integration test remains the parent smoke.
- No backend API, runtime contract, read model, database, or Vercel lightweight runtime changes.
