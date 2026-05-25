# embedded-persistence-governance-summary Specification

## Purpose

Ensure Governance Timeline compact runtime contract warning summaries expose Embedded SDK persistence coverage without requiring operators to expand the full payload.

## Requirements

### Requirement: Runtime contract warning summary MUST show embedded persistence coverage

Governance formatting MUST include a compact Embedded SDK persistence coverage label when summarizing runtime contract degraded payloads.

#### Scenario: Coverage is present

- **WHEN** `runtime_contract_summary.embedded_sdk_persistence_coverage.persistence_smoke = true`
- **THEN** the summary includes `embedded_persistence=covered`

#### Scenario: Coverage is missing

- **WHEN** the runtime contract status is not `unknown`
- **AND** Embedded SDK persistence coverage is missing or false
- **THEN** the summary includes `embedded_persistence=missing`

#### Scenario: Gate status is unknown

- **WHEN** runtime contract status is `unknown`
- **THEN** the summary includes `embedded_persistence=unknown`
