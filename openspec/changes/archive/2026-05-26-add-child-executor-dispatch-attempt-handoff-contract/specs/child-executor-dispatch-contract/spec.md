## ADDED Requirements
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
