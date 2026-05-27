## Why

`RuntimeSurfaceProfileAssembler` has been moved into a dedicated module, but its top-level `assemble()` method still owns request context normalization, runtime scope construction, and recovery target selection alongside the profile shell. Extracting that context/scope concern now keeps the next refactor small and contract-stable.

收口对象：Runtime Surface profile 的输入上下文、runtime scope 调用边界、run recovery target 选择。非目标：不改变 Runtime Profile payload shape，不新增前端能力，不推进 child executor、recovery scheduler、数据库迁移或 channel promotion。

## What Changes

- Add a dedicated profile context/scope assembler for Runtime Surface profile assembly.
- Move `runtime_scope` construction and `recovery_target_run_id` derivation out of the top-level profile shell assembler.
- Keep `RuntimeSurfaceService.get_runtime_profile()` and returned profile fields externally unchanged.
- Add focused backend tests for the new assembler boundary and service delegation.
- Sync architecture and roadmap docs with the new concern-specific builder seam.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `runtime-surface-contract-assembler`: clarify that profile input context, runtime scope, and recovery target derivation must live behind a concern-specific assembler boundary while preserving public payload shape.

## Impact

- Backend code:
  - `backend/services/runtime_surface_profile_assembler.py`
  - New dedicated backend service module for profile context/scope assembly
  - `tests/agent_framework/test_runtime_surface_service.py`
- OpenSpec/docs:
  - `openspec/specs/runtime-surface-contract-assembler/spec.md`
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`
- APIs/frontend:
  - No public API or frontend contract changes.
