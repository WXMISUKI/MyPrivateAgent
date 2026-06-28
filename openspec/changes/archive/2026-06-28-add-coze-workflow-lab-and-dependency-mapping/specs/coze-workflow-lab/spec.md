## ADDED Requirements

### Requirement: Workflow Lab Registry Surface
The system SHALL expose a workflow lab registry surface for migrated Coze workflows.

#### Scenario: Lab lists migrated workflows
- **WHEN** a client requests the workflow lab list
- **THEN** the response includes each migrated workflow id, name, version, status, capability id, readiness, owner, and launch evidence status
- **AND** draft, review, active, blocked, deprecated, and archived workflows remain visible to maintainers.

#### Scenario: Lab hides no blockers
- **WHEN** a workflow has missing prompts, missing examples, unsupported dependencies, invalid manifest fields, or provider readiness blockers
- **THEN** the lab response includes machine-readable blockers
- **AND** the workflow is not presented as production-ready.

### Requirement: Workflow Lab Detail Surface
The system SHALL expose a workflow detail contract for lab use.

#### Scenario: Detail includes schemas and examples
- **WHEN** a client opens a workflow detail
- **THEN** the response includes input schema, output schema, prompts metadata, acceptance examples, dependency mapping, governance, status, and capability id
- **AND** prompt bodies may be summarized or linked without exposing unrelated workflow assets.

### Requirement: Workflow Lab Example Replay
The system SHALL let maintainers replay acceptance examples through the same invocation contract as production callers.

#### Scenario: Example replay succeeds
- **GIVEN** a workflow is active and ready
- **WHEN** a maintainer invokes an acceptance example from the lab
- **THEN** the backend invokes the workflow through the standard capability/runtime envelope
- **AND** the response includes run id, status, result, trace summary, and expected-output comparison.

#### Scenario: Example replay is blocked
- **GIVEN** a workflow is draft, review, invalid, or missing dependencies
- **WHEN** a maintainer invokes an acceptance example from the lab
- **THEN** the backend returns a structured blocked response
- **AND** includes the blocker codes that must be resolved before promotion.

### Requirement: Workflow Lab Expected Output Diff
The system SHALL compare actual invocation results against acceptance expected output.

#### Scenario: Expected output matches
- **WHEN** actual result equals the expected JSON fixture under workflow acceptance
- **THEN** the comparison status is `match`
- **AND** the lab can use the result as launch evidence.

#### Scenario: Expected output differs
- **WHEN** actual result differs from expected JSON
- **THEN** the comparison status is `mismatch`
- **AND** the response includes a compact machine-readable diff summary.

### Requirement: Workflow Lab Launch Evidence
The system SHALL support publishing replayable launch acceptance evidence for migrated workflows.

#### Scenario: Launch evidence is linked
- **WHEN** a workflow has a `docs/integration/*-launch-acceptance` record
- **THEN** the lab detail includes the evidence path and decision if available
- **AND** missing evidence is visible as a review item for active workflows.
