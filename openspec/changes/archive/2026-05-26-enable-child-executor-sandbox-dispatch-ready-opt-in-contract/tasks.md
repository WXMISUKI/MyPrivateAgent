## 1. Spec And Contract

- [x] 1.1 Add OpenSpec proposal, design, dispatch contract spec delta, and task list.
- [x] 1.2 Extend `build_child_executor_dispatch_contract(...)` with opt-in sandbox execution seam and payload readiness evidence.
- [x] 1.3 Preserve default blocked / `will_dispatch=false` behavior and fail-closed blockers for missing idempotency or unsafe payload.

## 2. Gates And Tests

- [x] 2.1 Add focused SDK/dispatcher tests for opt-in ready dispatch contract and blocked payload variants.
- [x] 2.2 Extend runtime smoke and quality gate summary coverage for opt-in ready sandbox dispatch evidence.
- [x] 2.3 Update Runtime Contract Gate, Snapshot stable fields, health normalization if needed, and fixtures.

## 3. Docs, Validation, Archive

- [x] 3.1 Sync canonical OpenSpec specs, runtime contract docs, and roadmap.
- [x] 3.2 Run focused backend tests, runtime smoke, quality gate report, and OpenSpec validation.
- [x] 3.3 Archive the completed OpenSpec change.
