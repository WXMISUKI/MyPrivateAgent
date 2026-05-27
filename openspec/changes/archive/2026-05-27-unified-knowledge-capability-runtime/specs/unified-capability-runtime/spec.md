## ADDED Requirements

### Requirement: External knowledge provider registration
The backend SHALL be able to register external Knowledge Provider capabilities through the unified capability runtime.

#### Scenario: Knowledge provider registration is enabled
- **GIVEN** an external knowledge provider is configured
- **WHEN** a client requests `GET /api/capabilities`
- **THEN** `knowledge.rag.retrieve` and `knowledge.graph.query` are exposed with `transport=http`
- **AND** their status is resolved from the configured provider health endpoints

#### Scenario: Knowledge provider heartbeat survives outage
- **GIVEN** an external knowledge provider is configured but unreachable
- **WHEN** a client requests `GET /api/capabilities/heartbeat`
- **THEN** the response still returns 200
- **AND** the provider record reports `status=unreachable`
- **AND** includes a machine-readable error code

