# child-executor-dispatch-governance-summary Specification

## Purpose

Ensure Governance Timeline compact runtime contract warning summaries expose child executor dispatch boundary coverage without requiring operators to expand the full payload.

## ADDED Requirements

### Requirement: Runtime contract warning summary MUST show child executor dispatch coverage

Governance formatting MUST include a compact child executor dispatch coverage label when summarizing runtime contract degraded payloads.

#### Scenario: Coverage is present

- **WHEN** `runtime_contract_summary.child_executor_dispatch_coverage.dispatch_smoke = true`
- **THEN** the summary includes `child_executor_dispatch=covered`

#### Scenario: Coverage is missing

- **WHEN** the runtime contract status is not `unknown`
- **AND** child executor dispatch coverage is missing or false
- **THEN** the summary includes `child_executor_dispatch=missing`

#### Scenario: Gate status is unknown

- **WHEN** runtime contract status is `unknown`
- **THEN** the summary includes `child_executor_dispatch=unknown`
