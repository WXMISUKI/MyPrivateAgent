# Design

## Smoke Check
Add `child_executor_dispatch_contract` to `runtime_contract_smoke.py`. The check reads the Runtime Profile and verifies:

- contract version is present
- `overall_status = blocked`
- `dispatch_ready = false`
- `will_dispatch = false`
- relationship seam is preserved
- blockers are machine-readable and include dispatch readiness blockers

The check only inspects the profile payload.

## Quality Gate Summary
Add `child_executor_dispatch_coverage` to runtime contract summary with at least:

- `dispatch_smoke`
- `contract_version`
- `overall_status`
- `dispatch_ready`
- `will_dispatch`
- `backend_dispatch_ready`
- `blocker_count`
- `recommended_next_step`

Missing or malformed evidence must fail closed as `dispatch_smoke = false`.

## Runtime Contract Gate
Runtime Contract Gate should normalize both new and legacy artifacts:

- new artifacts use their emitted summary
- old artifacts derive coverage from raw checks if possible
- missing checks return uncovered coverage

## Snapshot Guard
Runtime Contract Snapshot should guard `runtime_contract_summary.child_executor_dispatch_coverage` and `.dispatch_smoke`, so CI consumers can detect summary drift.
