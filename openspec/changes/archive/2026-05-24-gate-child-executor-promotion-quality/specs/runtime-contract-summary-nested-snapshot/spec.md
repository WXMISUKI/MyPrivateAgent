## MODIFIED Requirements

### Requirement: Runtime contract snapshot MUST guard nested runtime contract summary coverage fields

Runtime Contract Snapshot MUST guard nested runtime contract summary coverage fields that consumers rely on for fail-closed quality gate interpretation.

#### Scenario: Child executor promotion gate coverage is missing

- **WHEN** Runtime Contract Gate lacks `runtime_contract_summary.child_executor_promotion_gate_coverage`
- **THEN** Runtime Contract Snapshot MUST report the runtime contract gate as degraded

#### Scenario: Child executor promotion gate smoke flag is missing

- **WHEN** Runtime Contract Gate lacks `runtime_contract_summary.child_executor_promotion_gate_coverage.gate_smoke`
- **THEN** Runtime Contract Snapshot MUST report the runtime contract gate as degraded

