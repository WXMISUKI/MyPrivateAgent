## MODIFIED Requirements

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

#### Scenario: Child executor promotion gate coverage is missing

- **WHEN** Runtime Contract Gate lacks `runtime_contract_summary.child_executor_promotion_gate_coverage`
- **THEN** Runtime Contract Snapshot MUST report the runtime contract gate as degraded

#### Scenario: Child executor promotion gate smoke flag is missing

- **WHEN** Runtime Contract Gate lacks `runtime_contract_summary.child_executor_promotion_gate_coverage.gate_smoke`
- **THEN** Runtime Contract Snapshot MUST report the runtime contract gate as degraded

#### Scenario: Child executor dispatch coverage is missing

- **WHEN** Runtime Contract Gate lacks `runtime_contract_summary.child_executor_dispatch_coverage`
- **THEN** Runtime Contract Snapshot MUST report the runtime contract gate as degraded

#### Scenario: Child executor dispatch smoke flag is missing

- **WHEN** Runtime Contract Gate lacks `runtime_contract_summary.child_executor_dispatch_coverage.dispatch_smoke`
- **THEN** Runtime Contract Snapshot MUST report the runtime contract gate as degraded

#### Scenario: Child executor dispatcher coverage is missing

- **WHEN** Runtime Contract Gate lacks `runtime_contract_summary.child_executor_dispatcher_coverage`
- **THEN** Runtime Contract Snapshot MUST report the runtime contract gate as degraded

#### Scenario: Child executor dispatcher smoke flag is missing

- **WHEN** Runtime Contract Gate lacks `runtime_contract_summary.child_executor_dispatcher_coverage.dispatcher_smoke`
- **THEN** Runtime Contract Snapshot MUST report the runtime contract gate as degraded

#### Scenario: Recovery retry evidence coverage is missing

- **WHEN** Runtime Contract Gate lacks `runtime_contract_summary.recovery_retry_evidence_coverage`
- **THEN** Runtime Contract Snapshot MUST report the runtime contract gate as degraded

#### Scenario: Recovery retry evidence smoke flag is missing

- **WHEN** Runtime Contract Gate lacks `runtime_contract_summary.recovery_retry_evidence_coverage.retry_smoke`
- **THEN** Runtime Contract Snapshot MUST report the runtime contract gate as degraded

#### Scenario: Recovery retry scheduler coverage is missing

- **WHEN** Runtime Contract Gate lacks `runtime_contract_summary.recovery_retry_scheduler_coverage`
- **THEN** Runtime Contract Snapshot MUST report the runtime contract gate as degraded

#### Scenario: Recovery retry scheduler smoke flag is missing

- **WHEN** Runtime Contract Gate lacks `runtime_contract_summary.recovery_retry_scheduler_coverage.scheduler_smoke`
- **THEN** Runtime Contract Snapshot MUST report the runtime contract gate as degraded

#### Scenario: Durable recovery loader coverage is missing

- **WHEN** Runtime Contract Gate lacks `runtime_contract_summary.durable_recovery_loader_coverage`
- **THEN** Runtime Contract Snapshot MUST report the runtime contract gate as degraded

#### Scenario: Durable recovery loader smoke flag is missing

- **WHEN** Runtime Contract Gate lacks `runtime_contract_summary.durable_recovery_loader_coverage.loader_smoke`
- **THEN** Runtime Contract Snapshot MUST report the runtime contract gate as degraded
