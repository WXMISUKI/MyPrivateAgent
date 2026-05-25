# child-executor-dispatch-contract Specification Delta

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
- required contracts
- recommended next step
- non-goals

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

#### Scenario: Dispatch contract is quality-gated
- **WHEN** runtime contract smoke evaluates Runtime Profile
- **THEN** it MUST emit a `child_executor_dispatch_contract` check
- **AND** quality gate summary MUST expose `child_executor_dispatch_coverage`
- **AND** missing or malformed dispatch evidence MUST fail closed as uncovered
