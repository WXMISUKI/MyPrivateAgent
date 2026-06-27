## ADDED Requirements

### Requirement: Migrated Workflow Capability Delegation
The capability runtime SHALL delegate migrated Coze workflow capabilities to the workflow runtime without creating a second provider execution path.

#### Scenario: Workflow capability is listed
- **WHEN** a migrated workflow is active and ready
- **THEN** `GET /api/capabilities` includes `coze.workflow.<workflow_id>`
- **AND** the capability contract includes input schema, output schema, owner, workflow status, readiness, and asset paths.

#### Scenario: Workflow capability invocation delegates
- **WHEN** a caller invokes `POST /api/capabilities/coze.workflow.<workflow_id>/invoke`
- **THEN** the capability runtime delegates to the workflow invocation service
- **AND** preserves the standard capability response envelope.

#### Scenario: Workflow capability is not ready
- **WHEN** a workflow is draft, review, invalid, blocked, deprecated, or archived
- **THEN** it is not exposed as a ready production callable capability
- **AND** direct invocation returns a fail-closed structured error.

### Requirement: Capability Runtime Does Not Own Model Provider Configuration
The capability runtime SHALL not store raw model provider secrets for migrated workflows.

#### Scenario: Workflow declares model provider dependency
- **WHEN** a workflow declares a model or provider dependency
- **THEN** the capability contract references provider identity or capability id
- **AND** raw API keys are not included in capability metadata.
