# runtime-contract-summary-nested-snapshot Specification Delta

## MODIFIED Requirements
### Requirement: Runtime Contract Snapshot Must Guard Nested Summary Fields
Runtime Contract Snapshot MUST guard required nested fields in `runtime_contract_gate.runtime_contract_summary`.

#### Scenario: Child executor dispatch coverage is missing
- **WHEN** Runtime Contract Gate lacks `runtime_contract_summary.child_executor_dispatch_coverage`
- **THEN** Runtime Contract Snapshot MUST mark the snapshot degraded
- **AND** it MUST report the missing field path

#### Scenario: Child executor dispatch smoke flag is missing
- **WHEN** Runtime Contract Gate lacks `runtime_contract_summary.child_executor_dispatch_coverage.dispatch_smoke`
- **THEN** Runtime Contract Snapshot MUST mark the snapshot degraded
- **AND** it MUST report the missing field path
