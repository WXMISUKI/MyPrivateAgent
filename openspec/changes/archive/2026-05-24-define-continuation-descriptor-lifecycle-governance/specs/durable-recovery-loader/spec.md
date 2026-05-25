## MODIFIED Requirements

### Requirement: Loader MUST reconstruct recovery candidates from durable workspace state

The loader MUST read persisted run state, events, approval state, continuation descriptors, and recovery operation history from a durable workspace backend.

#### Scenario: Durable state is complete

- **WHEN** persisted state contains a valid checkpoint, resume cursor, and resolvable continuation binding
- **THEN** the loader produces a registry-backed recovery candidate
- **AND** it exposes descriptor lifecycle evidence
- **AND** it does not execute recovery by itself

#### Scenario: Durable state is incomplete

- **WHEN** persisted state is missing, stale, unsafe, or lacks a resolvable registry binding
- **THEN** the loader fails closed
- **AND** it returns a machine-readable recovery reason
- **AND** it exposes descriptor lifecycle evidence when descriptors are present

### Requirement: Runtime quality gates MUST cover durable loader evidence

The runtime contract smoke and quality gate summary MUST expose durable recovery loader evidence.

#### Scenario: Smoke proves ready and fail-closed paths

- **WHEN** runtime contract smoke runs
- **THEN** it MUST include a `durable_recovery_loader` check
- **AND** the check MUST cover a ready registry-backed candidate, a missing run snapshot, unresolved binding, stale approval state, and unsafe descriptor rejection
- **AND** the check MUST expose descriptor lifecycle states for quality gate consumption
