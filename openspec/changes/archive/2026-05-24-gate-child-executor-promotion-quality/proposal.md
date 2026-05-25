## Why

`child_executor_promotion_gate` is already exposed as a backend truth source, but it is not yet covered by runtime contract smoke, quality gate summary, Runtime Contract Gate normalization, or snapshot drift checks. That means a future regression could keep the UI shell visible while silently losing the gate evidence that prevents `delegate_run(...)` from being mistaken for a true child executor.

This change adds quality-gate coverage for the existing gate contract without promoting child execution behavior.

## What Changes

- Add a runtime contract smoke check for `child_executor_promotion_gate`.
- Summarize the smoke result as `runtime_contract_summary.child_executor_promotion_gate_coverage`.
- Normalize the coverage in `RuntimeContractGateService` with fail-closed defaults for missing or malformed reports.
- Add snapshot guard coverage for the new summary object and `gate_smoke`.
- Update docs and tests to keep the current relationship-seam boundary explicit.
- Non-goals:
  - No true child executor implementation.
  - No change to `delegate_run(...)` runtime behavior.
  - No frontend redesign.
  - No database migration.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `child-executor-promotion-gate`: promotion gate evidence must be smoke-tested and quality-gated.
- `runtime-contract-approval-lifecycle-summary`: runtime contract summary must expose child executor promotion gate coverage.
- `runtime-contract-summary-nested-snapshot`: snapshot guard must include the new coverage object.

## Impact

- Backend quality/smoke:
  - `backend/scripts/runtime_contract_smoke.py`
  - `backend/scripts/quality_gate_report.py`
  - `backend/services/runtime_contract_gate_service.py`
  - `backend/services/runtime_contract_snapshot_service.py`
- Tests:
  - focused smoke / quality gate / runtime contract gate / snapshot tests
- Docs/specs:
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`
  - modified OpenSpec specs listed above

