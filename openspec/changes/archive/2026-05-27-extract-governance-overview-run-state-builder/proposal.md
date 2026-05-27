## Why

`RuntimeSurfaceService._build_governance_overview_contract()` still constructs `governance_overview.run` inline even though `runtime_core` and profile context are now separated. Extracting the run-state section makes the shared run identity and child merge state easier to test without touching recovery, promotion, or dispatch sections.

收口对象：`governance_overview.run` 的 run identity、trace summary、child merge state 和 section evidence。非目标：不抽完整 `governance_overview`，不改变 payload shape，不碰 recovery alignment、child executor promotion/dispatch 或 frontend。

## What Changes

- Add a dedicated `GovernanceOverviewRunStateBuilder`.
- Make `_build_governance_overview_contract()` delegate only the `run` section to the new builder.
- Preserve all current `governance_overview.run` fields and fallback behavior.
- Add focused tests for default run state, scoped run state, child merge evidence, and service wrapper integration.
- Sync OpenSpec, runtime contracts docs, and roadmap.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `governance-overview-run-state-surface`: clarify that `governance_overview.run` assembly is owned by a dedicated run-state builder.
- `runtime-surface-contract-assembler`: clarify that governance run-state can be decomposed before the full governance overview builder is extracted.

## Impact

- Backend:
  - New backend service builder module or equivalent builder boundary
  - `backend/services/runtime_surface_service.py`
  - `tests/agent_framework/test_runtime_surface_service.py`
- Docs/specs:
  - `openspec/specs/governance-overview-run-state-surface/spec.md`
  - `openspec/specs/runtime-surface-contract-assembler/spec.md`
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`
- API/frontend:
  - No public API or frontend contract change.
