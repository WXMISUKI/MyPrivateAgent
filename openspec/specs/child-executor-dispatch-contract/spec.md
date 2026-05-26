# child-executor-dispatch-contract Specification

## Purpose
Define the final side-effect-free dispatch boundary that prevents a child executor promotion candidate from being mistaken for a real dispatched worker.

## Requirements
### Requirement: Child Executor Dispatch Contract Must Be Machine-Readable
The system MUST expose a machine-readable `child_executor_dispatch_contract` that describes whether a delegated child run may be dispatched to a real child executor.

The contract MUST include:

- a contract version
- an overall status
- dispatch readiness
- a `will_dispatch` flag
- selected backend id and backend dispatch evidence
- promotion gate evidence
- execution prerequisite evidence
- blockers
- required contracts
- recommended next step
- non-goals

When the selected backend is a sandbox worker backend, dispatch readiness MUST also require adapter contract readiness, sandbox guard readiness, audit readiness, and idempotency readiness.

#### Scenario: Default dispatch is blocked
- **WHEN** the default child executor dispatch contract is built
- **THEN** it MUST report `overall_status = blocked`
- **AND** it MUST set `dispatch_ready = false`
- **AND** it MUST set `will_dispatch = false`
- **AND** it MUST preserve the relationship seam
- **AND** it MUST include blockers that explain why dispatch is unavailable

#### Scenario: Promotion gate passes but backend dispatch is not ready
- **WHEN** child executor preflight and promotion gate are ready but the selected backend reports `dispatch_ready = false`
- **THEN** the dispatch contract MUST remain blocked
- **AND** it MUST include `worker_backend_dispatch_ready` in blockers
- **AND** it MUST NOT imply that a real child executor has started

#### Scenario: Sandbox backend evidence is incomplete
- **WHEN** the selected sandbox backend lacks adapter contract readiness, sandbox guard readiness, audit readiness, or idempotency readiness
- **THEN** the dispatch contract MUST remain blocked
- **AND** it MUST expose a blocker for the missing sandbox backend evidence
- **AND** it MUST set `will_dispatch = false`

#### Scenario: Dispatch contract is quality-gated
- **WHEN** runtime contract smoke evaluates Runtime Profile
- **THEN** it MUST emit a `child_executor_dispatch_contract` check
- **AND** quality gate summary MUST expose `child_executor_dispatch_coverage`
- **AND** missing or malformed dispatch evidence MUST fail closed as uncovered

### Requirement: Child Executor Dispatch Contract Must Be Side-Effect Free
The child executor dispatch contract MUST only describe dispatch readiness and MUST NOT execute dispatch behavior.

#### Scenario: Dispatch contract is inspected
- **WHEN** SDK, Runtime Surface, or Governance Overview reads the dispatch contract
- **THEN** the system MUST return compact readiness evidence
- **AND** it MUST NOT create child runs, allocate workers, start executor processes, mutate persisted state, or change approval/recovery state

### Requirement: Runtime Surface Must Expose Dispatch Contract
Runtime Surface MUST expose the child executor dispatch contract so UI and governance consumers do not infer dispatch readiness from promotion gate fields.

#### Scenario: Runtime profile is built
- **WHEN** Runtime Surface builds a runtime profile
- **THEN** the profile MUST expose `child_executor_dispatch_contract`
- **AND** embedded runtime boundaries MUST expose the same dispatch boundary
- **AND** governance overview MUST expose the same dispatch boundary

### Requirement: Dispatch Readiness Must Require Explicit Executor Binding
The child executor dispatch contract MUST require explicit executor binding readiness before reporting dispatch-ready.

#### Scenario: Dispatch is blocked without explicit binding
- **WHEN** promotion gate and backend evidence are otherwise ready but explicit executor binding opt-in is missing
- **THEN** dispatch contract MUST report `overall_status = blocked`
- **AND** it MUST include `explicit_executor_binding_opt_in` in blockers
- **AND** it MUST keep `will_dispatch = false`

#### Scenario: Dispatch includes explicit binding evidence
- **WHEN** dispatch contract is built
- **THEN** it MUST expose explicit binding status, source, selected backend, and blockers as compact evidence
- **AND** consumers MUST NOT infer dispatch readiness from record-only binding fields.
