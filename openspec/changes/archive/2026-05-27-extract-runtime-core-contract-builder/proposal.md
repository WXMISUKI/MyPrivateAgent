## Why

`RuntimeSurfaceService._build_runtime_core_contract()` still constructs the Runtime Core payload directly inside the service after the top-level profile shell and profile context have been extracted. Moving this stable contract shell behind a dedicated builder keeps Runtime Surface assembly decomposable and reinforces the `run_id` runtime-instance boundary.

收口对象：`runtime_core` contract 的默认 shell、runtime scope overlay、child merge state merge。非目标：不改变 Runtime Profile payload shape，不修改 query/read-model endpoints，不推进 governance overview 拆分，不触碰数据库迁移或 child executor 行为。

## What Changes

- Add a dedicated `RuntimeCoreContractBuilder` for the Runtime Surface `runtime_core` contract.
- Keep `RuntimeSurfaceService._build_runtime_core_contract()` as a compatibility wrapper that delegates to the builder.
- Preserve existing `runtime_core` fields, defaults, `child_display_id` fallback, trace summary handling, and child merge section evidence.
- Add focused backend tests for default contract, scoped contract overlay, and service wrapper delegation.
- Sync OpenSpec, runtime contract docs, and roadmap status.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `runtime-surface-contract-assembler`: clarify that Runtime Core contract assembly must be a concern-specific builder while preserving public profile shape.

## Impact

- Backend:
  - `backend/services/runtime_surface_service.py`
  - New or existing builder module containing `RuntimeCoreContractBuilder`
  - `tests/agent_framework/test_runtime_surface_service.py`
- Docs/specs:
  - `openspec/specs/runtime-surface-contract-assembler/spec.md`
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`
- API/frontend:
  - No public API or frontend payload change.
