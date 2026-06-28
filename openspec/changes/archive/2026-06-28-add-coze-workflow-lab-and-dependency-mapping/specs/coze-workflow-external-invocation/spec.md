## ADDED Requirements

### Requirement: External Workflow Invocation Uses Capability Id
The system SHALL expose migrated workflows to external callers through stable capability ids.

#### Scenario: External caller invokes workflow capability
- **GIVEN** a migrated workflow is active and ready
- **WHEN** an external caller invokes `coze.workflow.<workflow_id>` through the capability invocation endpoint
- **THEN** the backend uses the same workflow runtime envelope as internal invocation
- **AND** includes workflow id, capability id, run id, status, result or error, and trace summary.

### Requirement: External Invocation Is Governed
The system SHALL preserve governance boundaries for external workflow invocation.

#### Scenario: Caller is not authorized
- **WHEN** a caller is not allowed to invoke a workflow capability
- **THEN** the backend returns a structured authorization error
- **AND** the workflow is not executed.

#### Scenario: Workflow is not ready
- **WHEN** an external caller invokes a draft, review, invalid, blocked, deprecated, or archived workflow
- **THEN** the backend returns a structured blocked or unavailable response
- **AND** the workflow is not executed.

### Requirement: External Invocation Supports Version Awareness
The system SHALL expose enough version metadata for callers to detect workflow contract changes.

#### Scenario: Invocation returns workflow version
- **WHEN** a workflow invocation completes or fails
- **THEN** the response trace or metadata includes workflow version
- **AND** callers can record which workflow contract version produced the result.

### Requirement: External Invocation Handles File Inputs Safely
The system SHALL avoid requiring external callers to pass local filesystem paths for reusable file workflows.

#### Scenario: External caller uses artifact reference
- **WHEN** an external caller invokes a file-based workflow
- **THEN** the input can use an artifact reference or runtime-managed file reference
- **AND** local test fixture paths remain limited to lab or backend smoke contexts.
