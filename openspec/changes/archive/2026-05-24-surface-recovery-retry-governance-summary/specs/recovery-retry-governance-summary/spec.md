# recovery-retry-governance-summary Specification

## ADDED Requirements

### Requirement: Runtime contract warning summary MUST show recovery retry coverage

Governance formatting MUST include a compact recovery retry coverage label when summarizing runtime contract degraded payloads.

#### Scenario: Coverage is present

- **WHEN** `runtime_contract_summary.recovery_retry_evidence_coverage.retry_smoke = true`
- **THEN** the summary includes `recovery_retry=covered`

#### Scenario: Coverage is missing

- **WHEN** the runtime contract status is not `unknown`
- **AND** recovery retry evidence coverage is missing or false
- **THEN** the summary includes `recovery_retry=missing`

#### Scenario: Gate status is unknown

- **WHEN** runtime contract status is `unknown`
- **THEN** the summary includes `recovery_retry=unknown`
