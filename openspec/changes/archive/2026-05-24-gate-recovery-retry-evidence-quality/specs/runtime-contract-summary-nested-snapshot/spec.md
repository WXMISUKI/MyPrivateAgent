## MODIFIED Requirements

### Requirement: Runtime contract snapshot MUST guard runtime summary nested coverage

`RuntimeContractSnapshotService` MUST treat core `runtime_contract_summary` nested fields as stable backend contract paths.

#### Scenario: Recovery retry evidence coverage is missing

- **WHEN** Runtime Contract Gate lacks `runtime_contract_summary.recovery_retry_evidence_coverage`
- **THEN** Runtime Contract Snapshot MUST report the runtime contract gate as degraded

#### Scenario: Recovery retry evidence smoke flag is missing

- **WHEN** Runtime Contract Gate lacks `runtime_contract_summary.recovery_retry_evidence_coverage.retry_smoke`
- **THEN** Runtime Contract Snapshot MUST report the runtime contract gate as degraded
