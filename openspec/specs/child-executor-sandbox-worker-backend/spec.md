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
