# runtime-contract-approval-lifecycle-summary Specification Delta

## MODIFIED Requirements
### Requirement: Runtime Contract Summary Must Include Child Executor Gate Coverage
The runtime contract summary MUST include machine-readable coverage for child executor promotion, execution prerequisites, and dispatch boundary checks.

#### Scenario: Child executor dispatch coverage is present
- **WHEN** runtime contract smoke emits `child_executor_dispatch_contract` with `ok = true`
- **THEN** the runtime contract summary MUST include `child_executor_dispatch_coverage.dispatch_smoke = true`
- **AND** the coverage MUST include dispatch status, readiness, backend readiness, blocker count, and recommended next step

#### Scenario: Child executor dispatch coverage is missing
- **WHEN** a legacy report lacks `child_executor_dispatch_contract`
- **THEN** the runtime contract summary MUST include `child_executor_dispatch_coverage.dispatch_smoke = false`
