## Why

Worker ownership production enablement now has a side-effect-free runtime config consumer, but the evidence is still mainly reachable through direct builder and quality gate paths. For the v1 closeout, the runtime needs an explicit `RuntimeSurfaceService -> EmbeddedRuntimeFactory -> worker_ownership` binding so operators can see caller-owned production enablement config evidence through the same Runtime Profile contract used by governance tooling.

收口对象：production enablement runtime config binding only. This change binds local caller-owned config input into runtime contract assembly; it does not enable production ownership.

## What Changes

- Add an explicit runtime factory input for worker ownership production enablement config evidence.
- Let Runtime Surface bootstrap config pass a local caller-owned config payload into the default embedded runtime factory.
- Expose the resulting `worker_ownership.production_enablement_runtime_config_consumer` evidence through Runtime Profile / factory contract assembly.
- Keep missing config fail-closed and keep complete config descriptive only.
- Extend focused tests, runtime smoke, quality gate summary, Runtime Contract Gate, docs, and canonical specs where contract semantics change.

Non-goals:

- Do not read remote config, files, secrets, or environment-derived production enablement payloads.
- Do not enable production default worker ownership.
- Do not execute PostgreSQL advisory lock SQL.
- Do not start background renewal workers.
- Do not run recovery auto-claim by default.
- Do not change SDK recovery authorization semantics.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `runtime-worker-ownership-contract`: Add explicit runtime factory/profile binding requirements for production enablement runtime config consumer evidence.
- `worker-ownership-production-gate`: Add quality coverage requirements proving the binding remains fail-closed and non-authorizing.

## Impact

- Backend contracts:
  - `backend/agent_framework/runtime_dependencies.py`
  - `backend/agent_framework/worker_ownership.py`
  - `backend/services/runtime_surface_service.py`
  - `backend/services/runtime_surface_config_service.py`
  - `backend/scripts/runtime_contract_smoke.py`
  - `backend/scripts/quality_gate_report.py`
  - `backend/services/runtime_contract_gate_service.py`
  - `backend/services/runtime_contract_snapshot_service.py`
- Tests:
  - `tests/agent_framework/test_worker_ownership.py`
  - `tests/agent_framework/test_runtime_surface_service.py`
  - `tests/agent_framework/test_runtime_contract_smoke.py`
  - `tests/agent_framework/test_quality_gate_report.py`
  - `tests/agent_framework/test_runtime_contract_gate_service.py`
- Docs/specs:
  - `openspec/specs/runtime-worker-ownership-contract/spec.md`
  - `openspec/specs/worker-ownership-production-gate/spec.md`
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`
