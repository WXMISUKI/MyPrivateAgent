# runtime-contract-summary-nested-snapshot

## ADDED Requirements

### Requirement: Runtime contract snapshot MUST guard runtime summary nested coverage

`RuntimeContractSnapshotService` MUST treat core `runtime_contract_summary` nested fields as stable backend contract paths.

#### Scenario: Subagent detail coverage is present

- **WHEN** `runtime_contract_gate.runtime_contract_summary.subagent_lane_query_detail_coverage.detail_smoke` is present
- **THEN** the `runtime_contract_gate` snapshot remains healthy
- **AND** the nested coverage paths are included in `stable_fields`

#### Scenario: Subagent detail coverage is missing

- **WHEN** `runtime_contract_summary.subagent_lane_query_detail_coverage` is missing
- **THEN** the snapshot is degraded
- **AND** `runtime_contract_gate.missing_fields` includes `runtime_contract_summary.subagent_lane_query_detail_coverage`

#### Scenario: Subagent detail coverage smoke flag is missing

- **WHEN** `runtime_contract_summary.subagent_lane_query_detail_coverage.detail_smoke` is missing
- **THEN** the snapshot is degraded
- **AND** `runtime_contract_gate.missing_fields` includes `runtime_contract_summary.subagent_lane_query_detail_coverage.detail_smoke`
