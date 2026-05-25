# subagent-lane-query-detail-readiness

## ADDED Requirements

### Requirement: Backend MUST expose subagent_lane detail readiness

Runtime Profile MUST expose a dedicated backend read model that reports whether `subagent_lane` is ready for a future query detail contract.

#### Scenario: Recorded recent summary is ready

- **WHEN** persisted Query Control traces contain `subagent_lane` events with stable `query_id` and stage values
- **THEN** the readiness contract reports `ready_for_detail = true`
- **AND** `readiness_status = ready`
- **AND** `recommended_next_change = subagent-lane-query-detail-contract`

### Requirement: Readiness MUST fail closed without records

The readiness contract MUST block detail promotion when `subagent_lane` has no recorded recent summary.

#### Scenario: No subagent lane records

- **WHEN** there are no `subagent_lane` Query Control traces
- **THEN** `ready_for_detail = false`
- **AND** `blocking_reasons` contains `recent_summary_not_recorded`

### Requirement: Endpoint MUST remain assessment only

The readiness endpoint MUST NOT return query detail events, history pagination, or workspace state.

#### Scenario: Readiness shape stays narrow

- **WHEN** the endpoint returns a readiness contract
- **THEN** it includes capability booleans and blocking reasons
- **AND** it does not include `recent_events`, `history_items`, or workspace view state
