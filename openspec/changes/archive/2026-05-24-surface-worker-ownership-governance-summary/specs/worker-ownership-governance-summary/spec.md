# worker-ownership-governance-summary Specification

## Purpose

Ensure Governance Timeline compact runtime contract warning summaries expose worker ownership store mode coverage without requiring operators to expand the full payload.

## ADDED Requirements

### Requirement: Runtime contract warning summary MUST show worker ownership coverage

Governance formatting MUST include a compact worker ownership coverage label when summarizing runtime contract degraded payloads.

#### Scenario: Coverage is present

- **WHEN** `runtime_contract_summary.worker_ownership_store_mode_coverage.mode_smoke = true`
- **THEN** the summary includes `worker_ownership=covered`

#### Scenario: Coverage is missing

- **WHEN** the runtime contract status is not `unknown`
- **AND** worker ownership store mode coverage is missing or false
- **THEN** the summary includes `worker_ownership=missing`

#### Scenario: Gate status is unknown

- **WHEN** runtime contract status is `unknown`
- **THEN** the summary includes `worker_ownership=unknown`
