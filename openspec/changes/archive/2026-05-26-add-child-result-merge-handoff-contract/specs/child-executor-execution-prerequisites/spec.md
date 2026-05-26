## ADDED Requirements
### Requirement: Child Result Merge Handoff Must Be Machine-Readable
Child executor execution prerequisites MUST expose a machine-readable child result merge handoff contract for the `child_result_merge_semantics_defined` requirement.

The handoff evidence MUST include contract version, overall status, readiness boolean, merge source, normalized merge strategy, strategy support status, intent policy readiness, artifact envelope requirement, section handoff requirement, parent metadata support, replay compatibility, missing sections, next allowed action, and non-goals.

#### Scenario: Merge handoff is missing
- **WHEN** no child result merge source is available
- **THEN** `child_executor_execution_prerequisites` MUST keep `child_result_merge_semantics_defined` in `missing_requirements`
- **AND** the requirement evidence MUST expose blocked handoff status
- **AND** real executor dispatch MUST remain disabled

#### Scenario: Merge handoff is supported
- **WHEN** child executor preflight includes a supported merge strategy
- **THEN** the `child_result_merge_semantics_defined` requirement MUST report ready
- **AND** the handoff evidence MUST expose the normalized merge strategy and source path
- **AND** this readiness MUST NOT by itself authorize worker dispatch

#### Scenario: Merge handoff is unsupported
- **WHEN** child executor preflight includes an unsupported merge strategy
- **THEN** the handoff contract MUST fail closed
- **AND** execution prerequisites MUST remain blocked

### Requirement: Child Result Merge Handoff Must Be Quality-Gated
Runtime smoke, Quality Gate, Runtime Contract Gate, and snapshot guard MUST expose coverage evidence for child result merge handoff readiness.

#### Scenario: Merge handoff smoke is healthy
- **WHEN** runtime contract smoke evaluates child executor prerequisites
- **THEN** it MUST emit default fail-closed merge handoff evidence
- **AND** it MUST emit opt-in supported merge handoff evidence
- **AND** malformed or missing handoff evidence MUST fail closed in the quality gate summary
