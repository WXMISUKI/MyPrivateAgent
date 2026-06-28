## ADDED Requirements

### Requirement: Provider failover analytics SHALL expose a compact read model
The system SHALL expose provider failover analytics as a compact read model derived from planner child execution metadata.

#### Scenario: Analytics returns summary metrics
- **WHEN** a client requests the failover analytics summary
- **THEN** the response SHALL include `window_days`, `total_children`, `switched_children`, `total_switches`, `switch_rate`, and `average_switches_per_switched_child`
- **AND THEN** the response SHALL include top provider, pair, and model summaries

#### Scenario: Analytics ignores stale executions
- **WHEN** child execution metadata is older than the requested window
- **THEN** the analytics response SHALL exclude that execution from the summary

### Requirement: Provider failover analytics SHALL remain read-only
The system SHALL not mutate planner routing, provider configuration, or runtime promotion state when producing failover analytics.

#### Scenario: Summary generation has no side effects
- **WHEN** the analytics endpoint is called
- **THEN** the system SHALL only read existing execution metadata
- **AND THEN** it SHALL not alter provider configuration, scheduler state, or route selection

### Requirement: Settings view SHALL present provider failover observability
The system SHALL expose the failover analytics read model in the Settings view as a diagnostic dashboard.

#### Scenario: Failover board renders metrics
- **WHEN** a user opens the model/provider Settings tab
- **THEN** the UI SHALL render the failover analytics summary
- **AND THEN** it SHALL show the current risk threshold context and recent failover metrics

#### Scenario: Failover board remains diagnostic
- **WHEN** a user views the failover board
- **THEN** the UI SHALL present it as an observability surface
- **AND THEN** it SHALL not offer automatic routing promotion or provider market actions

### Requirement: Provider failover analytics SHALL preserve bounded query parameters
The analytics endpoint SHALL accept only bounded window and limit parameters.

#### Scenario: Valid window is accepted
- **WHEN** a client requests analytics with an allowed window size
- **THEN** the endpoint SHALL return the corresponding summary

#### Scenario: Invalid window is rejected
- **WHEN** a client requests analytics with an unsupported window size
- **THEN** the endpoint SHALL fail closed
- **AND THEN** the response SHALL report the invalid parameter
