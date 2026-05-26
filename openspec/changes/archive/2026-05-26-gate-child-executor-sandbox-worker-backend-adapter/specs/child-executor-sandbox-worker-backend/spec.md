## ADDED Requirements

### Requirement: Sandbox backend adapter coverage MUST enter runtime contract gates

The system MUST expose sandbox worker backend adapter evidence as a dedicated runtime contract coverage object before real child executor sandbox dispatch can be treated as quality-gated.

The coverage object MUST include:

- coverage status
- contract version
- ready adapter contract status
- missing guard fail-closed status
- unsafe payload fail-closed status
- compact attempt validation status
- backend invocation count
- dispatch attempt status

#### Scenario: Sandbox backend coverage is complete

- **WHEN** runtime contract smoke validates a ready sandbox adapter, an incomplete adapter, an unsafe payload, and compact dispatch attempt evidence
- **THEN** Quality Gate MUST expose `runtime_contract_summary.child_executor_sandbox_backend_coverage.sandbox_backend_smoke = true`
- **AND** Runtime Contract Gate MUST preserve the normalized coverage fields
- **AND** Runtime Contract Snapshot MUST treat the coverage and smoke flag as stable required fields

#### Scenario: Sandbox backend coverage is missing

- **WHEN** the runtime contract report omits sandbox backend adapter coverage or reports incomplete evidence
- **THEN** Quality Gate and Runtime Contract Gate MUST fail closed with `sandbox_backend_smoke = false`
- **AND** Runtime Contract Snapshot MUST degrade when the summary coverage object or smoke flag is missing

#### Scenario: Sandbox backend coverage does not enable real dispatch

- **WHEN** sandbox backend adapter coverage is healthy
- **THEN** the default child executor backend MUST remain relationship-only unless a separate explicit dispatch-ready contract and opt-in dispatcher are supplied
- **AND** coverage MUST NOT start a worker, queue, sandbox runtime, or remote executor
