# recovery-infrastructure-governance-summary Specification

## Purpose

Ensure compact governance summaries expose recovery retry scheduler and durable recovery loader coverage.

## Requirements

### Requirement: Runtime contract warning summary MUST show retry scheduler coverage

Governance formatting MUST include a compact retry scheduler coverage label when summarizing runtime contract degraded payloads.

#### Scenario: Coverage is present

- **WHEN** `runtime_contract_summary.recovery_retry_scheduler_coverage.scheduler_smoke = true`
- **THEN** the summary includes `recovery_retry_scheduler=covered`

#### Scenario: Coverage is missing

- **WHEN** runtime contract status is not `unknown`
- **AND** retry scheduler coverage is missing or false
- **THEN** the summary includes `recovery_retry_scheduler=missing`

#### Scenario: Gate status is unknown

- **WHEN** runtime contract status is `unknown`
- **THEN** the summary includes `recovery_retry_scheduler=unknown`

### Requirement: Runtime contract warning summary MUST show durable loader coverage

Governance formatting MUST include a compact durable loader coverage label when summarizing runtime contract degraded payloads.

#### Scenario: Coverage is present

- **WHEN** `runtime_contract_summary.durable_recovery_loader_coverage.loader_smoke = true`
- **THEN** the summary includes `durable_loader=covered`

#### Scenario: Coverage is missing

- **WHEN** runtime contract status is not `unknown`
- **AND** durable loader coverage is missing or false
- **THEN** the summary includes `durable_loader=missing`

#### Scenario: Gate status is unknown

- **WHEN** runtime contract status is `unknown`
- **THEN** the summary includes `durable_loader=unknown`

### Requirement: Degraded trace payload MUST preserve durable loader coverage

The Health Router MUST normalize and write `durable_recovery_loader_coverage` inside `runtime_contract_gate_degraded.payload.runtime_contract_summary`.

#### Scenario: Durable loader coverage is present

- **WHEN** durable loader evidence is complete
- **THEN** the trace payload includes `durable_recovery_loader_coverage.loader_smoke = true`
- **AND** trace detail includes `durable_loader=covered`

#### Scenario: Durable loader coverage is missing

- **WHEN** durable loader evidence is absent or malformed
- **THEN** the trace payload includes `durable_recovery_loader_coverage.loader_smoke = false`
