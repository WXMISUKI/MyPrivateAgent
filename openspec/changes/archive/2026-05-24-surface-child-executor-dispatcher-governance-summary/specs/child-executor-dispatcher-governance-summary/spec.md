# child-executor-dispatcher-governance-summary Specification

## Purpose

Ensure Governance Timeline compact runtime contract warning summaries expose opt-in child executor dispatcher coverage without requiring operators to expand the full payload.

## ADDED Requirements

### Requirement: Runtime contract warning summary MUST show child executor dispatcher coverage

Governance formatting MUST include a compact child executor dispatcher coverage label when summarizing runtime contract degraded payloads.

#### Scenario: Coverage is present

- **WHEN** `runtime_contract_summary.child_executor_dispatcher_coverage.dispatcher_smoke = true`
- **THEN** the summary includes `child_executor_dispatcher=covered`

#### Scenario: Coverage is missing

- **WHEN** the runtime contract status is not `unknown`
- **AND** child executor dispatcher coverage is missing or false
- **THEN** the summary includes `child_executor_dispatcher=missing`

#### Scenario: Gate status is unknown

- **WHEN** runtime contract status is `unknown`
- **THEN** the summary includes `child_executor_dispatcher=unknown`
