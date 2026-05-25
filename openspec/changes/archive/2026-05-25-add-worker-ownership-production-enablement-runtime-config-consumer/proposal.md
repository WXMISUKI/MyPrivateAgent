## Why

Worker ownership production gate composition dry-run can now prove a fully ready evidence set without side effects, but callers still need a stable runtime config consumer to turn caller-owned production enablement metadata into the existing enablement input and dry-run contracts.

This change closes that next seam without enabling production defaults, executing locks, starting background workers, or running recovery auto-claim.

## What Changes

- Add a side-effect-free worker ownership production enablement runtime config consumer contract.
- The consumer accepts caller-owned runtime config or rollout artifact metadata and normalizes it into:
  - production default enablement input source evidence
  - production gate composition dry-run evidence
  - explicit non-execution and non-enablement posture
- Extend runtime smoke, Quality Gate, and Runtime Contract Gate summaries with machine-readable consumer evidence.
- Keep default behavior fail-closed: no default production ownership, no advisory lock execution, no background supervisor, and no recovery auto-claim.

Non-goals:

- Do not read files, pull remote config, or mutate runtime environment.
- Do not enable production worker ownership by default.
- Do not execute PostgreSQL advisory lock SQL.
- Do not start renewal supervisor lifecycle.
- Do not run recovery auto-claim.
- Do not change SDK recovery default behavior.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `runtime-worker-ownership-contract`: Add runtime config consumer evidence for production enablement input and dry-run composition.
- `worker-ownership-production-gate`: Add quality gate coverage requirements for production enablement runtime config consumer evidence.

## Impact

- Backend contract builder:
  - `backend/agent_framework/worker_ownership.py`
  - `backend/agent_framework/__init__.py`
- Runtime smoke and gate summaries:
  - `backend/scripts/runtime_contract_smoke.py`
  - `backend/scripts/quality_gate_report.py`
  - `backend/services/runtime_contract_gate_service.py`
- Focused tests:
  - `tests/agent_framework/test_worker_ownership.py`
  - `tests/agent_framework/test_runtime_contract_smoke.py`
  - `tests/agent_framework/test_quality_gate_report.py`
  - `tests/agent_framework/test_runtime_contract_gate_service.py`
- Documentation:
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`
