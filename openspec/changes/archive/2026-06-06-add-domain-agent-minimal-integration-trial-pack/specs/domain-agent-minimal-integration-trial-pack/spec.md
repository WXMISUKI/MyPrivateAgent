## ADDED Requirements

### Requirement: Minimal integration trial pack runs the grounded-answer control chain
The system SHALL provide a side-effect-free trial pack that runs the existing grounded-answer trial, package dry-run, and composition trial chain from a compact caller evidence payload.

#### Scenario: Trial pack is ready
- **WHEN** the caller evidence lets the trial report return `go`
- **AND** the package dry-run returns `ready`
- **AND** the composition trial returns `ready`
- **THEN** the trial pack returns `overall_status = go`
- **AND** the report includes stage statuses, citation allowlist, preview availability, blockers, warnings, and a recommended next action

#### Scenario: Trial pack requires review
- **WHEN** no stage is blocked
- **AND** at least one stage returns `review`
- **THEN** the trial pack returns `overall_status = review`
- **AND** the report preserves stage warnings for caller review

#### Scenario: Trial pack is blocked
- **WHEN** any stage returns `blocked`
- **THEN** the trial pack returns `overall_status = blocked`
- **AND** the report preserves machine-readable blockers

### Requirement: Minimal integration trial pack remains side-effect-free
The trial pack SHALL NOT change runtime behavior or invoke production execution paths.

#### Scenario: Trial pack runs
- **WHEN** the trial pack is executed
- **THEN** no provider, model, tool, MCP, `/api/chat`, memory write, audit write, trace write, source binding, or prompt rollout is performed
- **AND** default chat retrieval injection remains disabled

### Requirement: Minimal integration trial pack is runnable from repository-side smoke input
The system SHALL include a repository-side smoke script and example payload for the minimal integration trial pack.

#### Scenario: Caller runs smoke script
- **WHEN** the smoke script is invoked with the example payload
- **THEN** it prints a compact JSON trial pack report
- **AND** it uses existing domain-agent manifests and grounded-answer services
- **AND** it does not require starting the web server
