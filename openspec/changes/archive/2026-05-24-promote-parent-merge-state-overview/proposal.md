## Why

`parent_state_surface` now exposes section-source and section-count evidence, but runtime/governance overview only promotes the older child merge intent/entities/conclusion fields. Consumers still need to call the dedicated merged semantics read model to understand section provenance and count coherence.

This change promotes the stable parent merge section evidence into existing overview contracts without adding UI or execution behavior.

## What Changes

- Add child merge section-source evidence to runtime core and `governance_overview.run`.
- Add section ids and section counts to the parent-facing overview contract.
- Update response schema to explicitly model existing and new child merge overview fields.
- Preserve existing overview fields and dedicated merged semantics read model.
- Non-goals:
  - No frontend redesign.
  - No true child executor implementation.
  - No new endpoint.
  - No change to merge behavior or section ids.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `governance-overview-run-state-surface`: run overview must expose child merge section-source and section-count evidence.
- `parent-merge-state-surface`: parent state surface section evidence must be reusable by runtime/governance overview.

## Impact

- Backend:
  - `backend/services/runtime_surface_service.py`
  - `backend/schemas_runtime_surface.py`
- Tests:
  - `tests/agent_framework/test_runtime_surface_service.py`
  - schema tests if needed
- Docs/specs:
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`

