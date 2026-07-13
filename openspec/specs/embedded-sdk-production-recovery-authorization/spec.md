# embedded-sdk-production-recovery-authorization Specification

## Purpose
TBD - created by archiving change add-embedded-sdk-production-recovery-authorization-slice. Update Purpose after archive.
## Requirements
### Requirement: Embedded SDK production recovery authorization dry-run MUST be machine-readable
The system MUST expose a side-effect-free `embedded_sdk_production_recovery_authorization` contract that explains whether current Embedded SDK recovery evidence is sufficient for an explicit production recovery authorization review.

#### Scenario: Default authorization is blocked
- **WHEN** no explicit authorization request source is present
- **THEN** the contract MUST report `overall_status = blocked`
- **AND** it MUST include `authorization_request_source` in `missing_sections`
- **AND** it MUST report `will_execute = false`

#### Scenario: Authorization can be ready without executing recovery
- **WHEN** production recovery gate, loader handoff, worker ownership, audit evidence, and authorization input source are all ready
- **THEN** the contract MAY report `overall_status = ready`
- **AND** it MUST report `will_execute = false`
- **AND** it MUST NOT submit approval, resume a run, claim ownership, or start background recovery

### Requirement: Authorization dry-run MUST remain distinct from run recovery probe
The system MUST keep explicit production recovery authorization dry-run separate from run-specific recovery probe results.

#### Scenario: Run is recoverable but authorization is blocked
- **WHEN** a run-specific recovery probe reports a registry-backed recoverable candidate
- **AND** production recovery authorization dry-run is blocked
- **THEN** the run recovery result MUST remain recoverable
- **AND** the authorization contract MUST remain the authority for production authorization readiness

#### Scenario: Authorization is ready but run probe is unrecoverable
- **WHEN** production recovery authorization dry-run reports `ready`
- **AND** a specific run is missing descriptor or approval evidence
- **THEN** the run recovery probe MUST remain unrecoverable
- **AND** authorization readiness MUST NOT bypass run-specific blockers

### Requirement: Authorization dry-run MUST preserve fail-closed evidence
The system MUST preserve compact, machine-readable blocker evidence when production recovery authorization is not ready.

#### Scenario: Production recovery gate is blocked
- **WHEN** `production_recovery_gate.overall_status != ready`
- **THEN** the authorization contract MUST remain blocked
- **AND** it MUST include `production_recovery_gate` in `missing_sections`

#### Scenario: Worker ownership input source is incomplete
- **WHEN** worker ownership production enablement input source or runtime config consumer evidence is incomplete
- **THEN** the authorization contract MUST remain blocked
- **AND** it MUST include `worker_ownership_enablement_input` in `missing_sections`

### Requirement: Authorization dry-run MUST be quality-gate verifiable
Runtime contract smoke, quality gate summary, runtime contract gate, and snapshot coverage MUST expose Embedded SDK production recovery authorization evidence.

#### Scenario: Authorization smoke is healthy
- **WHEN** runtime contract smoke runs authorization dry-run checks
- **THEN** the smoke output MUST include blocked and ready authorization samples
- **AND** it MUST prove both samples keep `will_execute = false`

#### Scenario: Missing authorization coverage fails closed
- **WHEN** quality gate or runtime contract gate cannot read authorization dry-run evidence
- **THEN** the contract summary MUST fail closed rather than silently claiming authorization coverage

