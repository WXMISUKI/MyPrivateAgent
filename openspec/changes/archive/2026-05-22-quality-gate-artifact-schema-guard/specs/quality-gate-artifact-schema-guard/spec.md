# quality-gate-artifact-schema-guard

## ADDED Requirements

### Requirement: Quality gate artifact MUST expose runtime contract schema guard

Runtime contract quality gate steps MUST include a machine-readable schema guard for `runtime_contract_summary`.

#### Scenario: Runtime summary has all stable fields

- **WHEN** a quality gate step extracts runtime `contract_checks`
- **AND** `runtime_contract_summary.subagent_lane_query_detail_coverage.detail_smoke` is present
- **THEN** the step includes `runtime_contract_artifact_schema.overall_status = healthy`
- **AND** `summary_missing_fields` is empty

#### Scenario: Runtime summary is missing a stable nested field

- **WHEN** a runtime contract summary is missing `subagent_lane_query_detail_coverage.detail_smoke`
- **THEN** the schema guard status is `degraded`
- **AND** `summary_missing_fields` includes `subagent_lane_query_detail_coverage.detail_smoke`

### Requirement: Markdown summary MUST render runtime contract schema guard

The quality gate Markdown summary MUST render runtime artifact schema guard rows when present.

#### Scenario: Schema guard is present

- **WHEN** a report step includes `runtime_contract_artifact_schema`
- **THEN** the Markdown summary includes a `Runtime Contract Artifact Schema` table
- **AND** the table includes status and missing summary field information
