## ADDED Requirements

### Requirement: Runtime worker ownership MUST expose a PostgreSQL advisory lock execution seam

The runtime worker ownership contract MUST expose an opt-in PostgreSQL advisory lock execution seam for vendor lock hardening. The seam MUST remain inactive unless a caller explicitly injects an executor boundary.

#### Scenario: Execution seam defaults to blocked without executor

- **WHEN** a PostgreSQL advisory lock execution seam is constructed without an executor
- **THEN** its contract MUST report `executor_bound = false`
- **AND** one-shot operations MUST return blocked evidence
- **AND** no database connection or advisory lock SQL MUST be executed
- **AND** production worker ownership MUST NOT be enabled

#### Scenario: Explicit executor can probe and acquire once

- **WHEN** a caller injects an executor and invokes the PostgreSQL advisory lock execution seam explicitly
- **THEN** the seam MAY build probe and acquire operation envelopes
- **AND** the envelopes MUST include operation kind, lock key, run identity when applicable, worker identity, and fencing token evidence
- **AND** executor denial MUST return blocked evidence rather than production authorization

#### Scenario: Execution seam requires owner identity and fencing

- **WHEN** acquire, renew, or release is requested without run id, worker id, or fencing token evidence
- **THEN** the seam MUST fail closed before invoking the executor
- **AND** the blocked reason MUST be machine-readable
- **AND** recovery entry auto-claim MUST NOT run as a side effect

#### Scenario: PostgreSQL probe embeds execution seam evidence

- **WHEN** PostgreSQL vendor lock probe evidence is inspected
- **THEN** it MUST include nested execution seam evidence
- **AND** missing executor evidence MUST keep the execution seam blocked
- **AND** ready probe metadata alone MUST NOT imply advisory lock execution or production ownership enablement
