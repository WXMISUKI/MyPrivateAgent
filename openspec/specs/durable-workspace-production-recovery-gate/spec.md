# durable-workspace-production-recovery-gate Specification

## Purpose

Define the fail-closed production gate that must pass before durable workspace cross-process recovery can become default runtime behavior.

## Requirements

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

#### Scenario: Worker ownership gate evidence is linked

- **WHEN** the durable recovery gate evaluates worker ownership readiness
- **THEN** the `worker_ownership_production_gate` section MUST include nested worker ownership gate evidence
- **AND** the evidence MUST include ownership gate contract version, overall status, production-default flag, missing sections, and next allowed action
- **AND** the durable recovery gate MUST remain blocked when the ownership gate is blocked or not production-default enabled

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

#### Scenario: Descriptor lifecycle is governed

- **WHEN** continuation descriptor lifecycle governance is implemented and covered by runtime quality gates
- **THEN** the production recovery gate marks `descriptor_lifecycle_governance` as ready
- **AND** the gate still remains blocked when worker ownership, audit, rollout, registry policy, checkpoint/cursor gate, or loader handoff sections are missing

### Requirement: Production recovery MUST preserve loader non-execution boundary

DurableRecoveryLoader MUST remain a read-only candidate loader unless an explicit production recovery handoff policy is ready.

#### Scenario: Loader candidate is ready but handoff policy is missing

- **WHEN** DurableRecoveryLoader can produce a registry-backed candidate
- **AND** production loader handoff policy is missing
- **THEN** the production recovery gate remains blocked
- **AND** the loader MUST NOT execute recovery by itself

#### Scenario: Handoff policy is defined

- **WHEN** loader execution handoff policy is implemented and covered by runtime quality gates
- **THEN** the production recovery gate marks `loader_execution_handoff_policy` as ready
- **AND** the gate still remains blocked when worker ownership, audit, rollout, registry policy, or checkpoint/cursor gate sections are missing

#### Scenario: Recovery audit is ready but ownership or rollout is missing

- **WHEN** recovery audit operation history readiness is implemented and covered by runtime quality gates
- **THEN** the production recovery gate marks `recovery_audit_operation_history` as ready
- **AND** the gate still remains blocked when worker ownership, rollout, registry policy, or checkpoint/cursor gate sections are missing

#### Scenario: Registry/checkpoint policy is ready but ownership or rollout is missing

- **WHEN** registry binding resolution policy and checkpoint/resume cursor gate policy are implemented and covered by runtime quality gates
- **THEN** the production recovery gate marks `registry_binding_resolution` and `checkpoint_resume_cursor_gate` as ready
- **AND** the gate still remains blocked when worker ownership production gate or rollout sections are missing
- **AND** default production recovery execution remains disabled

#### Scenario: Loader candidate is ready but executor binding is missing

- **WHEN** DurableRecoveryLoader can produce a registry-backed candidate
- **AND** no recovery executor binding exists
- **THEN** the handoff decision remains blocked
- **AND** the loader MUST NOT execute recovery by itself
