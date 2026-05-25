# recovery-retry-production-scheduler-gate Specification

## Purpose

Define the production readiness gate that must pass before recovery retry can become default or background automatic execution.

## Requirements

### Requirement: Production retry scheduler gate MUST be machine-readable

The runtime MUST expose a production scheduler gate before automatic recovery retry can be enabled by default or run from a background scheduler.

The gate MUST include:

- contract version
- overall status
- automatic retry enabled by default flag
- readiness sections
- missing sections
- next allowed action
- non-goals

#### Scenario: Gate is not ready

- **WHEN** durable scheduling, idempotency, backoff, terminal policy, worker ownership, audit, or entrypoint evidence is missing
- **THEN** the gate reports `overall_status = blocked`
- **AND** automatic retry remains disabled by default
- **AND** the missing sections are machine-readable

#### Scenario: Gate is ready

- **WHEN** all production readiness sections are complete
- **THEN** the gate may report `overall_status = ready`
- **AND** automatic retry may be considered for explicit production enablement
- **AND** enabling automatic retry still requires an explicit runtime configuration

### Requirement: Production retry MUST require durable scheduling state

Automatic recovery retry MUST NOT rely on process-local timers or in-memory loops as its source of scheduling truth.

#### Scenario: Durable schedule state is missing

- **WHEN** retry scheduling state is only in process memory
- **THEN** production scheduler gate MUST remain blocked
- **AND** next allowed action identifies durable scheduling state as required

#### Scenario: Durable schedule state is present

- **WHEN** retry schedule state is durable and can survive process restart
- **THEN** the gate may mark durable scheduling state ready

### Requirement: Production retry MUST be idempotent and deduplicated

Automatic retry execution MUST use deterministic idempotency and dedupe keys so the same logical retry action cannot execute twice.

#### Scenario: Duplicate retry is observed

- **WHEN** the scheduler observes an already recorded retry operation for the same run, entrypoint, previous operation, and attempt number
- **THEN** it MUST skip execution
- **AND** it MUST return compact duplicate evidence

### Requirement: Production retry MUST respect worker ownership

Automatic retry execution MUST validate worker ownership before invoking a recovery entrypoint.

#### Scenario: Ownership is unavailable

- **WHEN** production retry would execute without valid ownership evidence
- **THEN** the scheduler MUST fail closed
- **AND** it MUST NOT execute the recovery entrypoint

#### Scenario: Ownership is valid

- **WHEN** valid lease and fencing evidence are present
- **THEN** the scheduler may execute only if all other gate sections are ready

### Requirement: Production retry MUST preserve recovery audit semantics

Automatic retry MUST extend recovery operation evidence and MUST NOT create a parallel retry event model.

#### Scenario: Retry operation is recorded

- **WHEN** automatic retry executes
- **THEN** it records a recovery operation with compact retry evidence
- **AND** audit timeline writing uses operation idempotency/dedupe evidence

#### Scenario: Audit writer fails

- **WHEN** recovery operation evidence is recorded but audit timeline writing fails
- **THEN** the retry result remains based on recovery operation evidence
- **AND** audit failure MUST NOT cause duplicate retry execution
