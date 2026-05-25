## Overview

This slice applies the existing runtime contract quality pattern to `child_executor_promotion_gate`. The gate contract already answers whether the delegated child execution context may be promoted beyond the relationship seam. The new work only proves that this contract is present and machine-readable in the smoke and quality gate artifacts.

## Contract Summary Shape

Add `runtime_contract_summary.child_executor_promotion_gate_coverage`:

- `gate_smoke`: boolean, fail-closed
- `contract_version`: string
- `gate_status`: string
- `allowed`: boolean
- `failure_reason`: string
- `blocker_count`: non-negative integer
- `recommended_next_step`: string

The smoke should cover the default blocked path and confirm:

- contract version is present
- `gate_status = blocked`
- `allowed = false`
- failure reason is present
- recommended next step is present
- blockers are represented as a list

This does not require an allowed promotion sample because the current phase intentionally keeps `delegate_run(...)` relationship-only unless future implementation slices add a real executor.

## Fail-Closed Behavior

Missing, malformed, or incomplete quality gate reports must normalize to:

- `gate_smoke = false`
- empty strings for textual evidence
- `allowed = false`
- `blocker_count = 0`

Runtime Contract Snapshot should degrade if the coverage object or `gate_smoke` is missing.

## Testing Strategy

Focused tests should cover:

- runtime contract smoke emits `child_executor_promotion_gate`
- quality gate report derives `child_executor_promotion_gate_coverage`
- Runtime Contract Gate derives and normalizes the coverage
- Runtime Contract Snapshot degrades when coverage or `gate_smoke` is missing

