## ADDED Requirements

### Requirement: Promoted Coze workflows SHALL expose a stable capability invoke contract
The system SHALL expose promoted workflows through a stable capability id of the form `coze.workflow.<workflow_id>` and SHALL invoke them through the capability runtime envelope.

#### Scenario: Active workflow invoke succeeds
- **WHEN** a workflow is in an active and ready state
- **THEN** invoking its capability id SHALL return a stable envelope that includes workflow id, capability id, workflow version, run id, status, authorization, invocation policy, and trace summary

#### Scenario: Capability id remains stable
- **WHEN** a workflow version changes without changing the workflow identity
- **THEN** the capability id SHALL remain stable
- **AND THEN** the returned envelope SHALL include the workflow version

### Requirement: Draft and review workflows SHALL fail closed
The system SHALL not expose draft or review workflows as production callable capabilities by default.

#### Scenario: Draft workflow invocation is blocked
- **WHEN** a client invokes a workflow that is still draft
- **THEN** the system SHALL fail closed
- **AND THEN** the response SHALL indicate that the workflow is not callable as production capability

#### Scenario: Review workflow invocation is blocked
- **WHEN** a client invokes a workflow that is in review
- **THEN** the system SHALL fail closed
- **AND THEN** the response SHALL indicate that the workflow has not been promoted

### Requirement: Workflow invoke endpoints SHALL reuse the same production envelope
The system SHALL use the same invocation envelope for `POST /api/coze-workflows/{workflow_id}/invoke` and `POST /api/capabilities/{capability_id}/invoke`.

#### Scenario: Workflow endpoint and capability endpoint match
- **WHEN** a promoted workflow is invoked through either endpoint
- **THEN** both endpoints SHALL return the same contract shape
- **AND THEN** both endpoints SHALL preserve the same trace and policy fields

### Requirement: Workflow invocation SHALL remain behind capability runtime enforcement
The system SHALL not bypass capability runtime checks when invoking a workflow and SHALL preserve fail-closed behavior for readiness, ownership, and policy failures.

#### Scenario: Missing readiness blocks invocation
- **WHEN** a workflow is not ready for promotion
- **THEN** invocation SHALL be blocked before execution
- **AND THEN** the response SHALL include the reason for the block

#### Scenario: Ownership mismatch blocks invocation
- **WHEN** a capability invocation is attempted against a provider or workflow that does not own the capability
- **THEN** the system SHALL fail closed
- **AND THEN** the response SHALL report the ownership mismatch
