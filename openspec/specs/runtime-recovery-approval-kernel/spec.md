# runtime-recovery-approval-kernel Specification

## Purpose
Define approval recovery kernel behavior for replay, ignored reversals, and resolved approval fail-closed recovery reasons.
## Requirements
### Requirement: Resolved approval submissions MUST be immutable
The system MUST treat resolved approvals as immutable lifecycle objects.

#### Scenario: Repeat the same resolved decision
- **WHEN** an already approved approval receives another approved submission
- **THEN** the system MUST return `approval_replayed`
- **AND** it MUST NOT re-execute a consumed continuation
- **AND** optional governance trace recording MUST NOT change the replay result

#### Scenario: Attempt to reverse a resolved decision
- **WHEN** an already denied approval receives an approved submission
- **THEN** the system MUST return `approval_ignored`
- **AND** it MUST NOT change the approval status
- **AND** optional governance trace recording MUST NOT change the ignored result

### Requirement: Recovery entrypoints MUST expose stable reason codes
The system MUST expose machine-readable `recovery_reason` values for recovery entrypoints.

#### Scenario: Approval is already resolved
- **WHEN** `probe_run_recovery()` or Runtime Surface recovery evaluates a resolved approval
- **THEN** the approval submission entrypoint MUST be unavailable
- **AND** it MUST expose `recovery_reason = already_resolved`
- **AND** it MAY retain `blocked_reason = approval_already_resolved` for compatibility

#### Scenario: Approval is denied
- **WHEN** a denied approval gates recovery
- **THEN** the recovery contract MUST preserve `approval_status = denied`
- **AND** it MUST NOT report the approval submission entrypoint as available

### Requirement: Quality gate MUST cover approval lifecycle recovery alignment
The system MUST include approval lifecycle and recovery alignment evidence in runtime contract smoke output.

#### Scenario: Smoke validates approval replay and ignored events
- **WHEN** runtime contract smoke runs
- **THEN** it MUST include a check proving `approval_replayed` and `approval_ignored` event payload samples exist
- **AND** the check MUST expose recovery alignment reason fields for downstream quality gate reports
