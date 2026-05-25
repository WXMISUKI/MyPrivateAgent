# subagent-lane-detail-gate-trace Specification

## Purpose
Ensure degraded runtime contract traces carry subagent lane query detail coverage evidence.
## Requirements
### Requirement: Degraded trace payload MUST include subagent detail coverage

`runtime_contract_gate_degraded` trace payloads MUST include normalized `subagent_lane_query_detail_coverage` inside `runtime_contract_summary`.

#### Scenario: Coverage present

- **WHEN** Runtime Contract Gate summary includes `subagent_lane_query_detail_coverage`
- **THEN** the degraded trace payload preserves `detail_smoke`, `contract_version`, `recording_state`, `stage_count`, and `recent_event_count`

### Requirement: Missing coverage MUST fail closed

Missing or malformed subagent detail coverage MUST normalize to an explicit false coverage object.

#### Scenario: Coverage missing

- **WHEN** Runtime Contract Gate summary does not include valid `subagent_lane_query_detail_coverage`
- **THEN** degraded trace payload reports `detail_smoke = false`
- **AND** count fields are `0`

### Requirement: Coverage change MUST affect fingerprint

Runtime contract degraded trace dedupe MUST treat subagent detail coverage changes as meaningful.

#### Scenario: Detail smoke flips from false to true

- **WHEN** two degraded gate summaries differ only in `subagent_lane_query_detail_coverage.detail_smoke`
- **THEN** the second runtime profile read writes a new `runtime_contract_gate_degraded` trace
- **AND** the two trace fingerprints differ
