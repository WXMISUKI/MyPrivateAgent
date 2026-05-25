## Why

Parent merged semantics already exposes `merged_sections` and `parent_state_surface`, but consumers still need to trust implicit coherence between flat fields, sections, and parent overview counts. The next safe slice is to make that coherence explicit in the backend contract so future UI or governance consumers do not reconstruct section semantics locally.

## What Changes

- Add stable section metadata to child executor merged semantics sections.
- Add parent state section-source evidence that links parent overview counts back to the sectioned read model.
- Preserve all existing flat fields and current section ids.
- Add focused SDK and Runtime Surface tests for section/count coherence.
- Non-goals:
  - No new child executor execution path.
  - No new frontend view.
  - No database migration.
  - No change to existing section ids or flat field names.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `parent-merge-state-surface`: parent state surface must expose section-source evidence and count coherence.
- `child-intent-taxonomy-sections`: merged sections must expose stable section kind and item/text count metadata.

## Impact

- Backend:
  - `backend/agent_framework/sdk.py`
  - Runtime Surface child executor read model through existing SDK reader
- Tests:
  - `tests/agent_framework/test_embedded_runtime_sdk.py`
  - `tests/agent_framework/test_runtime_surface_service.py`
- Docs/specs:
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`

