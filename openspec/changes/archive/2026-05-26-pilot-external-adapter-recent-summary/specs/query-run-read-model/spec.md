## ADDED Requirements

### Requirement: external_adapter Recent Summary Read Model

The system MUST provide `external_adapter_recent_summary` as a dedicated recent summary read model built from Query Control trace events for the `external_adapter` channel.

#### Scenario: Runtime Surface exposes recorded external adapter summary

- **WHEN** Query Control trace events exist with `channel = external_adapter`
- **THEN** Runtime Surface MUST expose `external_adapter_recent_summary`
- **AND** the contract MUST include `contract_version`, `connected`, `recording_state`, `items`, `latest_query_id`, `latest_stage`, `latest_summary`, `latest_timestamp`, `total_items`, and `reason`
- **AND** each item MUST use the shared recent summary field set: `query_id`, `latest_stage`, `latest_summary`, `latest_timestamp`, and `recording_state`

#### Scenario: No external adapter records remain a safe summary state

- **WHEN** no Query Control trace events exist for `external_adapter`
- **THEN** the contract MUST return `recording_state = no_records`
- **AND** it MUST NOT synthesize query identity from framework-specific payloads

#### Scenario: external_adapter summary does not imply deeper read models

- **WHEN** `external_adapter_recent_summary` is recorded
- **THEN** the system MUST NOT expose external adapter query detail, query history, or query workspace behavior as part of this change
