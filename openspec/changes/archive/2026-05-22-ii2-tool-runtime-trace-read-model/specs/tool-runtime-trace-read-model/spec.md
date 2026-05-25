## ADDED Requirements

### Requirement: Compact Tool Runtime Observation Payload

The system MUST preserve compact tool runtime execution metadata in query
control record payloads.

#### Scenario: Tool result contains runtime execution metadata

- **GIVEN** a tool result event contains `execution.retry`,
  `execution.timeout`, and `execution.schema_validation`
- **WHEN** `QueryControlEventMapperService.build_record_payload(...)` is called
- **THEN** the payload MUST include `tool_runtime_observation`
- **AND** the payload MUST include compact status fields
- **AND** the payload MUST NOT copy full result text.

### Requirement: Query Control Contract Announces Tool Runtime Observation

The system MUST describe the compact tool runtime observation payload in the
query control runtime contract.

#### Scenario: Runtime contract is built

- **WHEN** `QueryControlPlaneService.build_runtime_contract()` is called
- **THEN** the tool runtime adapter boundary MUST include
  `tool_runtime_observation_payload = compact_status_summary`.
