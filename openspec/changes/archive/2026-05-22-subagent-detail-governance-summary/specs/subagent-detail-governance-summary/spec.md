# subagent-detail-governance-summary

## ADDED Requirements

### Requirement: Runtime contract warning summary MUST show subagent detail coverage

Governance formatting MUST include a compact subagent detail coverage label when summarizing runtime contract degraded payloads.

#### Scenario: Coverage is present

- **WHEN** `runtime_contract_summary.subagent_lane_query_detail_coverage.detail_smoke = true`
- **THEN** the summary includes `subagent_detail=covered`

#### Scenario: Coverage is missing

- **WHEN** the runtime contract status is not `unknown`
- **AND** subagent detail coverage is missing or false
- **THEN** the summary includes `subagent_detail=missing`

#### Scenario: Gate status is unknown

- **WHEN** runtime contract status is `unknown`
- **THEN** the summary includes `subagent_detail=unknown`
