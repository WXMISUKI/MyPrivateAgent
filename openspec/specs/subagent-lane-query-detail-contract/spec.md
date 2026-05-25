# subagent-lane-query-detail-contract Specification

## Purpose
Define the dedicated subagent lane query detail read model without leaking unrelated history or workspace state.
## Requirements
### Requirement: Backend MUST expose subagent_lane query detail

Runtime Profile MUST expose a dedicated backend read model for a single `subagent_lane` `query_id`.

#### Scenario: Recorded query detail

- **WHEN** persisted Query Control traces contain matching `subagent_lane` events
- **THEN** the detail contract reports `recording_state = recorded`
- **AND** includes `stage_chain`, `recent_events`, `latest_stage`, `latest_summary`, and event counts

### Requirement: Missing query id MUST fail closed

The detail contract MUST reject empty query ids without scanning timeline events.

#### Scenario: Query id missing

- **WHEN** callers omit `query_id`
- **THEN** the detail contract reports `recording_state = unavailable`
- **AND** `reason = query_id_missing`

### Requirement: Detail contract MUST stay separate from history and workspace

The `subagent_lane` detail endpoint MUST remain a single-query read model.

#### Scenario: No history or workspace payload

- **WHEN** callers read a `subagent_lane` query detail
- **THEN** the response does not include `history_items`, `page`, `next_cursor`, or workspace view state
