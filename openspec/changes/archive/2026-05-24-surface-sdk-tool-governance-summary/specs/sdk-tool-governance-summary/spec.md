# sdk-tool-governance-summary Specification

## ADDED Requirements

### Requirement: Runtime contract warning summary MUST show SDK tool coverage

Governance formatting MUST include a compact SDK tool coverage label when summarizing runtime contract degraded payloads.

#### Scenario: Coverage is present

- **WHEN** `runtime_contract_summary.sdk_tool_runtime_execution_coverage.bridge_smoke = true`
- **THEN** the summary includes `sdk_tool=covered`

#### Scenario: Coverage is missing

- **WHEN** the runtime contract status is not `unknown`
- **AND** SDK tool runtime execution coverage is missing or false
- **THEN** the summary includes `sdk_tool=missing`

#### Scenario: Gate status is unknown

- **WHEN** runtime contract status is `unknown`
- **THEN** the summary includes `sdk_tool=unknown`
