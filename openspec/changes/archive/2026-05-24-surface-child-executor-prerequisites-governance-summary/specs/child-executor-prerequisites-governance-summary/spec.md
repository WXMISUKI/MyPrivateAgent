# child-executor-prerequisites-governance-summary Specification

## Purpose

Ensure Governance Timeline compact runtime contract warning summaries expose child executor execution prerequisites coverage without requiring operators to expand the full payload.

## ADDED Requirements

### Requirement: Runtime contract warning summary MUST show child executor prerequisites coverage

Governance formatting MUST include a compact child executor execution prerequisites coverage label when summarizing runtime contract degraded payloads.

#### Scenario: Coverage is present

- **WHEN** `runtime_contract_summary.child_executor_execution_prerequisites_coverage.prerequisites_smoke = true`
- **THEN** the summary includes `child_executor_prerequisites=covered`

#### Scenario: Coverage is missing

- **WHEN** the runtime contract status is not `unknown`
- **AND** child executor execution prerequisites coverage is missing or false
- **THEN** the summary includes `child_executor_prerequisites=missing`

#### Scenario: Gate status is unknown

- **WHEN** runtime contract status is `unknown`
- **THEN** the summary includes `child_executor_prerequisites=unknown`
