## Why

Worker ownership already has an explicit `WORKER_OWNERSHIP_STORE_MODE` bootstrap knob, but the runtime contract quality gate does not yet continuously prove that this configuration remains visible and conservative. This slice closes the v1 production-readiness loop by making the store mode part of runtime contract smoke evidence and quality gate summaries.

## What Changes

- Add runtime contract smoke evidence for default worker ownership store mode.
- Add quality gate summary coverage for worker ownership store mode.
- Add Runtime Contract Gate normalization and snapshot guard fields for the new coverage.
- Keep the safe default as `memory_only`.
- Preserve `strict_sql` fail-closed and `prefer_sql_with_fallback` diagnostic fallback semantics as evidence.
- Non-goals:
  - Do not switch the default ownership store to SQL.
  - Do not implement database vendor-specific distributed lock semantics.
  - Do not add automatic lease renewal, background workers, or scheduler ownership claiming.
  - Do not change SDK recovery gate activation rules.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `runtime-worker-ownership-contract`: add quality gate coverage expectations for worker ownership store mode.

## Impact

- Backend contract smoke:
  - `backend/scripts/runtime_contract_smoke.py`
- Quality gate report and Runtime Contract Gate:
  - `backend/scripts/quality_gate_report.py`
  - `backend/services/runtime_contract_gate_service.py`
  - `backend/services/runtime_contract_snapshot_service.py`
- Tests:
  - `tests/agent_framework/test_runtime_contract_smoke.py`
  - `tests/agent_framework/test_quality_gate_report.py`
  - `tests/agent_framework/test_runtime_contract_gate_service.py`
  - `tests/agent_framework/test_runtime_contract_snapshot_service.py`
- Docs truth sources:
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`

