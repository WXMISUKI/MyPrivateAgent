## MODIFIED Requirements

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
- sandbox execution seam evidence when sandbox dispatch readiness is evaluated
- required contracts
- recommended next step
- non-goals

When the selected backend is a sandbox worker backend, dispatch readiness MUST also require adapter contract readiness, sandbox guard readiness, audit readiness, idempotency readiness, explicit sandbox backend binding evidence, callable dispatcher backend adapter binding, execution seam support evidence, child run payload evidence, and idempotency payload evidence.

#### Scenario: Default dispatch is blocked
- **WHEN** the default child executor dispatch contract is built
- **THEN** it MUST report `overall_status = blocked`
- **AND** it MUST set `dispatch_ready = false`
- **AND** it MUST set `will_dispatch = false`
- **AND** it MUST preserve the relationship seam
- **AND** it MUST include blockers that explain why dispatch is unavailable

#### Scenario: Opt-in sandbox dispatch contract is ready
- **WHEN** promotion gate, execution prerequisites, sandbox backend registry, sandbox backend binding, sandbox execution seam evidence, child run payload evidence, and idempotency payload evidence are all ready
- **THEN** the dispatch contract MUST report `overall_status = ready`
- **AND** it MUST set `dispatch_ready = true`
- **AND** it MUST keep `will_dispatch = false`
- **AND** it MUST expose ready dispatch attempt handoff evidence
- **AND** it MUST NOT invoke a backend adapter

#### Scenario: Opt-in sandbox dispatch is blocked by missing idempotency
- **WHEN** sandbox dispatch evidence is otherwise ready but the payload lacks idempotency evidence
- **THEN** the dispatch contract MUST report `overall_status = blocked`
- **AND** it MUST include `sandbox_payload_idempotency_ready` in blockers
- **AND** it MUST keep `will_dispatch = false`

#### Scenario: Opt-in sandbox dispatch is blocked by unsafe payload
- **WHEN** sandbox dispatch evidence is otherwise ready but payload contains unsafe runtime objects
- **THEN** the dispatch contract MUST report `overall_status = blocked`
- **AND** it MUST include `sandbox_payload_unsafe` in blockers
- **AND** it MUST expose unsafe payload keys
- **AND** it MUST keep `will_dispatch = false`

### Requirement: Dispatch Contract Must Expose Attempt Handoff Evidence
The child executor dispatch contract MUST expose a machine-readable dispatch attempt handoff contract before any dispatcher may invoke a backend adapter.

#### Scenario: Opt-in sandbox handoff is envelope-ready
- **WHEN** dispatch prerequisites, sandbox backend evidence, sandbox backend binding, execution seam evidence, and payload idempotency evidence are ready
- **THEN** the handoff contract MAY report ready
- **AND** it MUST still keep `will_dispatch = false`
- **AND** it MUST prove the attempt envelope can be validated without starting a worker

### Requirement: Dispatch Attempt Handoff Must Be Quality-Gated
Runtime smoke, Quality Gate, Runtime Contract Gate, and Snapshot guard MUST expose dispatch attempt handoff evidence.

#### Scenario: Handoff smoke is healthy
- **WHEN** runtime contract smoke evaluates child executor dispatch
- **THEN** it MUST emit default blocked handoff evidence
- **AND** it MUST emit opt-in envelope-ready handoff evidence
- **AND** it MUST emit opt-in ready dispatch contract evidence
- **AND** missing or malformed evidence MUST fail closed in quality summaries
