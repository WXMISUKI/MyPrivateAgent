---
name: myagent-governance-ui-slimming
description: Slim and refactor MyPrivateAgent Vue governance UI without changing backend contracts. Use when splitting GovernanceTimelinePanel, RuntimeSurfacePanel governance cards, summary/action cards, event stream, query workspace, snapshot command UI, or governance timeline tests.
---

# MyPrivateAgent Governance UI Slimming

Use this skill to reduce frontend governance panel complexity while preserving runtime contract interpretation.

## Required Guardrails

- Preserve existing backend contract semantics; frontend should consume contracts, not redefine them.
- Keep parent panels responsible for data loading, route state, filter state, and cross-region coordination.
- Move display-only regions into child components that receive props and emit actions.
- Child components should not directly mutate parent state or own route behavior.
- Do not fragment the main event stream into many overlapping cards; keep `GovernanceTimelineEventStream` as the event-stream trunk.
- Follow existing Vue component style in `frontend-vue/src/components/`.

## Standard Workflow

1. Read current component and tests:
   - `frontend-vue/src/components/GovernanceTimelinePanel.vue`
   - Existing nearby child components.
   - `frontend-vue/src/components/__tests__/GovernanceTimelinePanel.test.js`
2. Pick one visual/behavioral region:
   - Overview cards.
   - Summary-action cards.
   - Framework Adapter cards.
   - Query workspace.
   - Event stream wrapper.
   - Remediation or snapshot command card.
3. Extract by prop/event boundary:
   - Props carry display data and flags.
   - Emits forward user actions with original payloads.
   - Parent keeps route/filter/history logic.
4. Add or update focused component tests:
   - Child component renders the state.
   - Child forwards action payloads without swallowing them.
   - Parent test still proves integration behavior.
5. Sync docs when the component boundary becomes stable:
   - `docs/architecture/runtime_contracts.md`
   - `docs/roadmap/next_phase_hardening.md`
6. Run focused Vitest only; do not run `npm build` unless the change is broad or build-sensitive.

## Common Verification Commands

```powershell
npm exec vitest run src/components/__tests__/GovernanceTimelinePanel.test.js
npm exec vitest run src/components/__tests__/<NewComponent>.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

## Completion Criteria

- Parent component is smaller or less region-heavy.
- Child component has a clear display/event seam.
- Existing governance timeline behavior still passes tests.
- Docs reflect the stable boundary if this is more than local cleanup.
