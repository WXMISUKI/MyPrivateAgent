## Why

`RuntimeSurfaceProfileAssembler` already exists, but it still lives inside `runtime_surface_builders.py` with many concern-specific builders. Phase II calls for a clearer Runtime Surface assembler boundary so `RuntimeSurfaceService.get_runtime_profile()` stays a stable orchestration entrypoint without the profile shell being hidden in a broad builders module.

## What Changes

- Move `RuntimeSurfaceProfileAssembler` into a dedicated backend module for the top-level runtime profile shell.
- Keep `RuntimeSurfaceService.get_runtime_profile()` as the public orchestration entrypoint.
- Preserve the external runtime profile payload shape.
- Add focused backend coverage proving the service delegates through the dedicated assembler without changing core profile fields.
- Update docs and OpenSpec state to mark the assembler boundary as started.

## Capabilities

### New Capabilities

### Modified Capabilities
- `runtime-surface-contract-assembler`: Clarify that the top-level profile shell assembler SHALL live behind a dedicated module boundary and preserve external profile shape.

## Impact

- Affected backend files:
  - `backend/services/runtime_surface_service.py`
  - `backend/services/runtime_surface_builders.py`
  - New `backend/services/runtime_surface_profile_assembler.py`
- Affected tests:
  - `tests/agent_framework/test_runtime_surface_service.py`
- Affected docs/specs:
  - `openspec/specs/runtime-surface-contract-assembler/spec.md`
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`
- No frontend, API route, database, Vercel runtime, or contract field shape changes.
