## ADDED Requirements

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
