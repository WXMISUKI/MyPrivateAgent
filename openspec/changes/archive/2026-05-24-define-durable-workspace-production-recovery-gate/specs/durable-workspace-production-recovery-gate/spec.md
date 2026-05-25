## ADDED Requirements

### Requirement: Durable workspace production recovery gate MUST be machine-readable

The runtime MUST expose a production recovery gate before cross-process recovery can become default runtime behavior.

The gate MUST include:

- contract version
- overall status
- production default enabled flag
- readiness sections
- missing sections
- next allowed action
- non-goals

#### Scenario: Production recovery gate is blocked

- **WHEN** descriptor lifecycle, registry binding, checkpoint/cursor, worker ownership, audit, rollout, or loader handoff evidence is missing
- **THEN** the gate reports `overall_status = blocked`
- **AND** cross-process recovery remains conditional or explicit
- **AND** default production recovery execution remains disabled

#### Scenario: Production recovery gate is ready

- **WHEN** all production readiness sections are complete
- **THEN** the gate may report `overall_status = ready`
- **AND** enabling default cross-process recovery still requires explicit runtime configuration

### Requirement: Production recovery MUST NOT treat durable posture as run authorization

`durable_ready` MUST remain a backend capability signal and MUST NOT authorize a specific run recovery by itself.

#### Scenario: Durable backend has no descriptor

- **WHEN** persistence posture is `durable_ready`
- **AND** descriptor lifecycle evidence is missing
- **THEN** the production recovery gate remains blocked
- **AND** the run-specific recovery probe remains the authority for recoverability

### Requirement: Production recovery MUST require descriptor lifecycle governance

Default cross-process recovery MUST require descriptor lifecycle evidence for creation, binding, readiness, staleness, resolution, and unsafe payload rejection.

#### Scenario: Descriptor lifecycle is incomplete

- **WHEN** descriptors are persisted but lifecycle state governance is incomplete
- **THEN** the production recovery gate remains blocked
- **AND** missing descriptor lifecycle sections are machine-readable

### Requirement: Production recovery MUST preserve loader non-execution boundary

DurableRecoveryLoader MUST remain a read-only candidate loader unless an explicit production recovery handoff policy is ready.

#### Scenario: Loader candidate is ready but handoff policy is missing

- **WHEN** DurableRecoveryLoader can produce a registry-backed candidate
- **AND** production loader handoff policy is missing
- **THEN** the production recovery gate remains blocked
- **AND** the loader MUST NOT execute recovery by itself
