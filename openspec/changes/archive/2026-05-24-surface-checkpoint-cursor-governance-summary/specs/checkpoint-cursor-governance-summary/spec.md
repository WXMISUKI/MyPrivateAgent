# checkpoint-cursor-governance-summary Specification

## ADDED Requirements

### Requirement: Runtime contract warning summary MUST show checkpoint cursor coverage

Governance formatting MUST include a compact checkpoint cursor coverage label when summarizing runtime contract degraded payloads.

#### Scenario: Coverage is present

- **WHEN** `runtime_contract_summary.checkpoint_resume_cursor_coverage.cursor_smoke = true`
- **THEN** the summary includes `checkpoint_cursor=covered`

#### Scenario: Coverage is missing

- **WHEN** the runtime contract status is not `unknown`
- **AND** checkpoint cursor coverage is missing or false
- **THEN** the summary includes `checkpoint_cursor=missing`

#### Scenario: Gate status is unknown

- **WHEN** runtime contract status is `unknown`
- **THEN** the summary includes `checkpoint_cursor=unknown`
