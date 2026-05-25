## ADDED Requirements

### Requirement: Workspace backend MUST describe durable state boundaries
The system MUST expose a machine-readable `state_contract` from embedded workspace backend descriptions.

#### Scenario: Inspect SQLAlchemy workspace backend
- **WHEN** a caller reads `SQLAlchemyEmbeddedRunWorkspaceStore.describe_backend()`
- **THEN** the response MUST include `state_contract.contract_version`
- **AND** it MUST list durable state kinds and runtime-only state kinds

#### Scenario: Inspect in-memory workspace backend
- **WHEN** a caller reads `InMemoryEmbeddedRunWorkspaceStore.describe_backend()`
- **THEN** the response MUST expose the same state vocabulary
- **AND** it MUST still report `durable = false`

### Requirement: Runtime-only executable state MUST remain explicit
The system MUST NOT imply that Python callables or temporary stream cursors are durable.

#### Scenario: Read runtime-only state kinds
- **WHEN** a caller reads the workspace state contract
- **THEN** executable continuation callables and Python function bindings MUST be listed as runtime-only state kinds
