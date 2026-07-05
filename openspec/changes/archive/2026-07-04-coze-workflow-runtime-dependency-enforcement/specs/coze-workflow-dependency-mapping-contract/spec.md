## MODIFIED Requirements

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

### Requirement: Coze workflow dependency mapping SHALL be a shared preflight read model
The system SHALL expose the same dependency mapping contract through the workflow registry read surface, Workflow Lab read surface, and workflow invocation preflight so reviewers and runtime consumers inspect the same blocker semantics.

#### Scenario: Registry detail includes dependency mapping
- **WHEN** a client fetches a workflow detail from the registry API
- **THEN** the response SHALL include the dependency mapping contract
- **AND THEN** the mapping SHALL include category, blocker, and target capability fields

#### Scenario: Workflow Lab reads the same mapping contract
- **WHEN** a user opens a workflow in Workflow Lab
- **THEN** the UI SHALL render the dependency mapping categories and blocker reasons
- **AND THEN** it SHALL not re-infer a different blocker taxonomy

#### Scenario: Invoke preflight can reuse the mapping contract
- **WHEN** runtime invocation checks a workflow before execution
- **THEN** it SHALL be able to consume the same dependency mapping blockers
- **AND THEN** blocker reasons SHALL remain machine-readable and stable
