# child-executor-sandbox-worker-backend Specification

## Purpose

Define the sandbox worker backend adapter contract required before child executor dispatch can move from relationship-only readiness into real worker invocation.

## Requirements

### Requirement: Sandbox worker backend MUST expose an adapter contract

The system MUST define a sandbox worker backend adapter contract before any child executor backend can be treated as dispatch-ready for real worker execution.

The adapter contract MUST include:

- backend id
- adapter kind
- contract version
- sandbox mode
- execution mode
- input contract
- output contract
- resource limits
- isolation guards
- audit hooks
- idempotency evidence
- failure modes

#### Scenario: Adapter contract is ready

- **WHEN** a sandbox worker backend is registered as a real dispatch candidate
- **THEN** it MUST expose the adapter contract fields
- **AND** it MUST identify sandbox, resource, audit, and idempotency guards
- **AND** it MUST NOT require callers to infer readiness from backend id alone

#### Scenario: Adapter contract is incomplete

- **WHEN** a sandbox worker backend omits required adapter contract evidence
- **THEN** the backend MUST remain not dispatch-ready
- **AND** dispatch contract evaluation MUST fail closed with a machine-readable blocker

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

### Requirement: Sandbox backend MUST enforce execution guard categories

The sandbox worker backend adapter MUST expose guard evidence for isolation, resource limits, timeout policy, environment allowlist, filesystem/workspace boundary, network policy, audit recording, and idempotency.

#### Scenario: Guard evidence is complete

- **WHEN** all required guard categories are present
- **THEN** backend registry may report the backend as sandbox-ready
- **AND** dispatch contract may use the backend as a dispatch-ready candidate

#### Scenario: Guard evidence is missing

- **WHEN** any required guard category is missing
- **THEN** backend registry MUST keep `dispatch_ready = false`
- **AND** the backend blockers include the missing guard category

### Requirement: Sandbox backend MUST reject unsafe payloads

The sandbox worker backend adapter MUST reject payloads that include executable callables, provider clients, open streams, process handles, or unbounded raw output.

#### Scenario: Unsafe payload is submitted

- **WHEN** dispatch input includes unsafe runtime-only objects
- **THEN** the adapter MUST fail closed
- **AND** compact evidence includes an unsafe payload error code
- **AND** no worker execution is started

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

### Requirement: Sandbox Backend Must Support Dispatch Attempt Envelope Handoff
Sandbox worker backend evidence MUST describe the compact dispatch attempt envelope schema used by child executor dispatch handoff validation.

#### Scenario: Sandbox attempt envelope is valid
- **WHEN** an opt-in sandbox backend produces all required attempt fields
- **THEN** handoff validation MUST report the envelope as valid
- **AND** this validation MUST NOT start a worker or imply production dispatch enablement

#### Scenario: Sandbox attempt envelope is malformed
- **WHEN** required attempt fields are missing
- **THEN** handoff validation MUST fail closed with missing field evidence
