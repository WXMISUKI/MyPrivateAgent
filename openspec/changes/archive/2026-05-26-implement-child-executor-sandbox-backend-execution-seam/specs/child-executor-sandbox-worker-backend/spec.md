## MODIFIED Requirements

### Requirement: Sandbox dispatch attempt MUST return compact evidence
A sandbox worker backend adapter MUST return compact dispatch attempt evidence when invoked by the opt-in dispatcher.

The attempt evidence MUST include:

- attempt id
- backend id
- child run id
- status
- `will_dispatch`
- started and finished timestamps
- sandbox reference
- output reference
- audit reference
- error code
- retryable flag

#### Scenario: Dispatch attempt succeeds
- **WHEN** the dispatcher invokes a ready sandbox backend adapter
- **THEN** the adapter returns compact attempt evidence
- **AND** the evidence includes sandbox, output, and audit references
- **AND** the evidence does not inline unbounded execution output

#### Scenario: Dispatch attempt fails
- **WHEN** the sandbox backend adapter cannot start or complete execution
- **THEN** it returns compact failure evidence
- **AND** `will_dispatch` is false unless work actually started
- **AND** it includes a stable error code and retryable flag

#### Scenario: Opt-in execution seam completes compactly
- **WHEN** the sandbox backend execution seam receives a valid payload with `child_run_id` and `idempotency_key`
- **THEN** it MUST return a valid compact dispatch attempt envelope
- **AND** the envelope status MUST be `completed`
- **AND** it MUST include sandbox, output, and audit references
- **AND** it MUST NOT inline child output or parent merge data

#### Scenario: Opt-in execution seam fails closed
- **WHEN** the sandbox backend execution seam receives unsafe payload, missing required payload fields, or missing idempotency evidence
- **THEN** it MUST return compact blocked evidence
- **AND** it MUST NOT invoke the executor callback
- **AND** it MUST include a stable error code

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
- opt-in execution seam support status
- opt-in execution seam fail-closed status

#### Scenario: Sandbox backend coverage is complete
- **WHEN** runtime contract smoke validates a ready sandbox adapter, an incomplete adapter, an unsafe payload, compact dispatch attempt evidence, and opt-in execution seam paths
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
