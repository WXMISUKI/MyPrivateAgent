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
- dispatch attempt handoff evidence
- sandbox backend binding evidence when the selected backend is a sandbox worker
- sandbox execution seam evidence when an opt-in sandbox worker dispatch boundary is being evaluated
- sandbox payload readiness evidence, including child run id, idempotency, and unsafe payload keys
- required contracts
- recommended next step
- non-goals

When the selected backend is a sandbox worker backend, dispatch readiness MUST also require adapter contract readiness, sandbox guard readiness, audit readiness, idempotency readiness, explicit sandbox backend binding evidence, a callable dispatcher backend adapter binding, sandbox execution seam support, a child run payload, idempotency evidence, and an unsafe payload guard.

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

#### Scenario: Opt-in sandbox dispatch boundary is ready
- **WHEN** promotion gate, execution prerequisites, backend registry, sandbox backend binding, sandbox execution seam, child run payload, and idempotency evidence are all ready
- **THEN** the dispatch contract MAY report `overall_status = ready`
- **AND** it MUST set `dispatch_ready = true`
- **AND** it MUST expose `sandbox_dispatch_ready_opt_in = true`
- **AND** it MUST expose `sandbox_execution_seam_supported = true`
- **AND** it MUST expose `sandbox_payload_child_run_ready = true`
- **AND** it MUST expose `sandbox_payload_idempotency_ready = true`
- **AND** it MUST keep `will_dispatch = false`
- **AND** it MUST NOT invoke the sandbox backend adapter

#### Scenario: Opt-in sandbox dispatch blocks missing idempotency
- **WHEN** an opt-in sandbox dispatch boundary is evaluated without idempotency evidence
- **THEN** the dispatch contract MUST remain blocked
- **AND** it MUST include `sandbox_payload_idempotency_ready` in blockers
- **AND** it MUST keep `will_dispatch = false`

#### Scenario: Opt-in sandbox dispatch blocks unsafe payload
- **WHEN** an opt-in sandbox dispatch boundary is evaluated with an unsafe payload field such as a callable handler
- **THEN** the dispatch contract MUST remain blocked
- **AND** it MUST include `sandbox_payload_unsafe` in blockers
- **AND** it MUST expose the unsafe payload keys
- **AND** it MUST keep `will_dispatch = false`

#### Scenario: Dispatch contract is quality-gated
- **WHEN** runtime contract smoke evaluates Runtime Profile
- **THEN** it MUST emit a `child_executor_dispatch_contract` check
- **AND** quality gate summary MUST expose `child_executor_dispatch_coverage`
- **AND** coverage MUST include opt-in ready sandbox dispatch status, handoff readiness, no-dispatch posture, missing-idempotency blocking, and unsafe payload blocking
- **AND** missing or malformed dispatch evidence MUST fail closed as uncovered

### Requirement: Dispatch Contract Must Expose Attempt Handoff Evidence
The child executor dispatch contract MUST expose a machine-readable dispatch attempt handoff contract before any dispatcher may invoke a backend adapter.

The handoff evidence MUST include contract version, overall status, readiness boolean, dispatch contract readiness, dispatcher default posture, backend id, backend adapter kind, sandbox selection, attempt envelope support, attempt validation readiness, audit and idempotency requirements, unsafe payload guard readiness, missing sections, blocked reason, next allowed action, and non-goals.

#### Scenario: Default handoff remains blocked
- **WHEN** child executor dispatch is evaluated without ready dispatch prerequisites
- **THEN** `child_executor_dispatch_contract.child_executor_dispatch_attempt_handoff` MUST report blocked
- **AND** it MUST keep `will_dispatch = false`
- **AND** it MUST explain missing dispatch contract readiness or backend evidence

#### Scenario: Opt-in sandbox handoff is envelope-ready
- **WHEN** dispatch prerequisites and sandbox backend evidence are ready
- **THEN** the handoff contract MAY report ready
- **AND** it MUST still keep `will_dispatch = false`
- **AND** it MUST prove the attempt envelope can be validated without starting a worker

### Requirement: Dispatch Attempt Handoff Must Be Quality-Gated
Runtime smoke, Quality Gate, Runtime Contract Gate, and Snapshot guard MUST expose dispatch attempt handoff evidence.

#### Scenario: Handoff smoke is healthy
- **WHEN** runtime contract smoke evaluates child executor dispatch
- **THEN** it MUST emit default blocked handoff evidence
- **AND** it MUST emit opt-in envelope-ready handoff evidence
- **AND** missing or malformed evidence MUST fail closed in quality summaries

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

### Requirement: Dispatch Contract Must Carry Sandbox Backend Binding Evidence

Child executor dispatch contract MUST include nested sandbox backend binding evidence when sandbox backend evidence is available.

#### Scenario: Dispatch contract includes binding evidence

- **WHEN** the dispatch contract is built for a sandbox backend candidate
- **THEN** it MUST include `child_executor_sandbox_backend_binding`
- **AND** the binding MUST be preserved under `evidence.child_executor_sandbox_backend_binding`
- **AND** dispatch MUST remain blocked unless the existing promotion gate, prerequisites, backend dispatch readiness, explicit executor opt-in, and binding readiness are all ready
