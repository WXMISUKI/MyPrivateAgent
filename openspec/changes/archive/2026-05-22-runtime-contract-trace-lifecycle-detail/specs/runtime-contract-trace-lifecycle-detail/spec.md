# runtime-contract-trace-lifecycle-detail

## ADDED Requirements

### Requirement: Runtime contract degraded trace detail MUST expose lifecycle recovery coverage

The backend trace detail for `runtime_contract_gate_degraded` MUST include a compact approval lifecycle recovery coverage label.

#### Scenario: Lifecycle recovery coverage is present and covered

- **WHEN** `runtime_contract_summary.approval_lifecycle_recovery_coverage.alignment_smoke = true`
- **THEN** the trace detail includes `approval_lifecycle=covered`.

#### Scenario: Lifecycle recovery coverage is present but not covered

- **WHEN** the lifecycle recovery coverage object exists but `alignment_smoke = false`
- **THEN** the trace detail includes `approval_lifecycle=missing`.

#### Scenario: Runtime contract summary is absent

- **WHEN** the degraded gate has no runtime contract summary object
- **THEN** the trace detail includes `approval_lifecycle=unknown`.
