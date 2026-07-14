## Why

Runtime-plane adapters now emit compact `governance_projection`, but Runtime Surface does not yet expose a stable read-only place for governance consumers to discover that contract. The next highest-value step is to add a Runtime Surface profile section that advertises the projection contract and latest projection summary without executing adapters or writing trace/audit state.

收口对象：Runtime Surface top-level read-only profile for runtime-plane governance projections.

非目标：do not execute runtime-plane adapters, do not persist projections, do not write trace/audit, do not submit approvals, do not add frontend UI, and do not change default `/api/chat`.

## What Changes

- Add a concern-specific Runtime Surface builder for runtime-plane governance projection profile.
- Add top-level `runtime_plane_governance_profile` to `RuntimeSurfaceService.get_runtime_profile()`.
- The profile exposes projection contract readiness, supported Stage 1 adapter ids, latest projection summary when supplied, and explicit read-only boundaries.
- Add snapshot guard coverage for the new profile contract.
- Add focused Runtime Surface tests for default no-projection state and supplied projection summary state.
- Update architecture/roadmap docs and write a slice review.

## Capabilities

### New Capabilities

- `runtime-surface-runtime-plane-profile`: Defines the Runtime Surface read-only profile for runtime-plane governance projections.

### Modified Capabilities

- `runtime-plane-integration-strategy`: Records that Runtime Surface can now expose runtime-plane projection readiness without executing or persisting runtime-plane state.

## Impact

Affected code:

- `backend/services/runtime_surface_runtime_plane_builder.py`
- `backend/services/runtime_surface_profile_assembler.py`
- `backend/services/runtime_surface_service.py`
- `backend/services/runtime_contract_snapshot_service.py`
- `tests/agent_framework/test_runtime_surface_service.py`
- `tests/agent_framework/test_runtime_contract_snapshot_service.py`

Affected docs/specs:

- `openspec/changes/add-runtime-surface-runtime-plane-profile/`
- `docs/architecture/runtime_contracts.md`
- `docs/architecture/runtime_plane_integration_strategy.md`
- `docs/roadmap/next_phase_hardening.md`
- `docs/roadmap/runtime_surface_runtime_plane_profile_review.md`
