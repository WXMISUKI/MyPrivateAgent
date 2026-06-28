## ADDED Requirements

### Requirement: Coze workflow dependency mapping SHALL classify every node
The system SHALL map every declared Coze workflow node into one of the following categories: `runtime_capability`, `provider_backed`, `artifact_input`, or `explicit_blocker`.

#### Scenario: Route node maps to runtime capability
- **WHEN** a route workflow declares an HTTP request step and the runtime supports the corresponding capability
- **THEN** the dependency mapping SHALL mark the node as `runtime_capability`
- **AND THEN** the mapping SHALL expose the target capability id

#### Scenario: File input maps to artifact input
- **WHEN** a workflow step consumes an uploaded spreadsheet or file reference
- **THEN** the dependency mapping SHALL mark the node as `artifact_input`
- **AND THEN** the mapping SHALL expose the runtime-managed input reference type

### Requirement: Coze workflow dependency mapping SHALL surface blockers explicitly
The system SHALL mark unsupported or unresolved workflow dependencies as `explicit_blocker` and SHALL include a machine-readable blocker reason.

#### Scenario: Unsupported node is blocked
- **WHEN** a workflow references a node that has no supported runtime capability or provider mapping
- **THEN** the dependency mapping SHALL mark the node as `explicit_blocker`
- **AND THEN** the response SHALL include a blocker reason that explains what is missing

#### Scenario: Provider-backed step is unavailable
- **WHEN** a workflow step depends on a provider-backed capability that is not registered or not ready
- **THEN** the dependency mapping SHALL mark the node as `explicit_blocker`
- **AND THEN** the response SHALL identify the missing provider-backed dependency

### Requirement: Coze workflow dependency mapping SHALL be readable by Workflow Lab and registry APIs
The system SHALL expose dependency mapping through the workflow registry read surface and Workflow Lab read surface so reviewers can inspect the same contract before promotion.

#### Scenario: Workflow Lab reads the mapping
- **WHEN** a user opens a workflow in Workflow Lab
- **THEN** the UI SHALL render the dependency mapping categories and blocker reasons

#### Scenario: Registry exposes the mapping
- **WHEN** a client fetches the workflow detail from the registry API
- **THEN** the response SHALL include the dependency mapping contract
