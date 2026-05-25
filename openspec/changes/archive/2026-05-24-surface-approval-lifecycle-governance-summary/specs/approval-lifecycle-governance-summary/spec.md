# approval-lifecycle-governance-summary Specification

## ADDED Requirements

### Requirement: Runtime contract warning summary MUST show approval lifecycle coverage

Governance formatting MUST include a compact approval lifecycle coverage label when summarizing runtime contract degraded payloads.

#### Scenario: Coverage is present

- **WHEN** `runtime_contract_summary.approval_lifecycle_recovery_coverage.alignment_smoke = true`
- **THEN** the summary includes `approval_lifecycle=covered`

#### Scenario: Coverage is missing

- **WHEN** the runtime contract status is not `unknown`
- **AND** approval lifecycle recovery coverage is missing or false
- **THEN** the summary includes `approval_lifecycle=missing`

#### Scenario: Gate status is unknown

- **WHEN** runtime contract status is `unknown`
- **THEN** the summary includes `approval_lifecycle=unknown`
