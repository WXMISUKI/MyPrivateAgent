## Why

Provider Ops is now visible in Settings, but it is still missing from the Runtime Surface, which is the canonical governance-facing profile for maintainers. This creates a split where operational posture exists, but cannot be reviewed from the same runtime contract view as other control-plane surfaces.

Adding Provider Ops to Runtime Surface makes the contract easier to inspect, compare, and eventually use in broader governance workflows without changing provider execution behavior.

## What Changes

- Add a compact `provider_ops` section to the Runtime Surface profile.
- Render Provider Ops inside `RuntimeSurfacePanel` as a read-only governance-visible card.
- Keep the surface diagnostic-only and avoid new mutations, invokes, or routing actions.

## Non-Goals

- Do not add provider ops to Governance Timeline event replay.
- Do not add provider ops editing actions.
- Do not alter provider execution, promotion, or routing.
- Do not redesign the full Runtime Surface layout.

## Impact

- Backend: Runtime Surface profile assembler includes `provider_ops`.
- Frontend: `RuntimeSurfacePanel` renders compact provider ops summary and provider posture.
- Tests: focused backend/frontend coverage for the new profile field and panel rendering.
