# subagent-lane-query-detail-smoke-gate

## ADDED Requirements

### Requirement: Runtime smoke MUST cover subagent_lane query detail

The runtime contract smoke output MUST include a dedicated `subagent_lane_query_detail` check.

#### Scenario: Detail smoke passes

- **WHEN** the runtime smoke can read a recorded `subagent_lane` query detail contract
- **THEN** the smoke output includes `name = subagent_lane_query_detail`
- **AND** reports `contract_version`, `recording_state`, `stage_count`, and `recent_event_count`
- **AND** the check is `ok = true`

### Requirement: Quality gate summary MUST expose subagent_lane detail coverage

Quality gate and runtime contract gate summaries MUST include `subagent_lane_query_detail_coverage`.

#### Scenario: Coverage is summarized

- **WHEN** contract checks include `subagent_lane_query_detail`
- **THEN** the runtime summary reports `detail_smoke = true`
- **AND** preserves `contract_version`, `recording_state`, `stage_count`, and `recent_event_count`

### Requirement: Missing detail smoke MUST fail closed

Runtime contract gate summaries MUST not imply subagent detail coverage when the check is absent.

#### Scenario: Check missing

- **WHEN** contract checks do not include `subagent_lane_query_detail`
- **THEN** `subagent_lane_query_detail_coverage.detail_smoke = false`
