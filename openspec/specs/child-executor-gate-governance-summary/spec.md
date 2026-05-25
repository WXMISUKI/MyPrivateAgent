# child-executor-gate-governance-summary Specification

## Purpose

Ensure Governance Timeline compact runtime contract warning summaries expose child executor promotion gate coverage without requiring operators to expand the full payload.

## Requirements

### Requirement: Runtime contract warning summary MUST show child executor gate coverage

Governance formatting MUST include a compact child executor promotion gate coverage label when summarizing runtime contract degraded payloads.

#### Scenario: Coverage is present

- **WHEN** `runtime_contract_summary.child_executor_promotion_gate_coverage.gate_smoke = true`
- **THEN** the summary includes `child_executor_gate=covered`

#### Scenario: Coverage is missing

- **WHEN** the runtime contract status is not `unknown`
- **AND** child executor promotion gate coverage is missing or false
- **THEN** the summary includes `child_executor_gate=missing`

#### Scenario: Gate status is unknown

- **WHEN** runtime contract status is `unknown`
- **THEN** the summary includes `child_executor_gate=unknown`
