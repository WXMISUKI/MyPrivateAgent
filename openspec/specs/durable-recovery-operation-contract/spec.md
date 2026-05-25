# durable-recovery-operation-contract Specification

## Purpose

Define a compact, auditable recovery operation contract for Embedded SDK durable recovery entrypoints without claiming distributed worker ownership or executable persistence.

## Requirements

### Requirement: SDK MUST expose a recovery operation boundary

The Embedded SDK contract MUST declare the supported durable recovery operation entrypoints and the worker ownership boundary. Future worker ownership, retry, and audit hardening contracts MUST extend or consume this recovery operation evidence instead of replacing it with parallel recovery status models.

#### Scenario: Contract declares operation boundary

- **WHEN** a consumer calls `build_contract()`
- **THEN** the contract MUST include `recovery_operation_contract`
- **AND** it MUST list `submit_approval.approved` and `resume_run.continue_loop` as supported operation entrypoints
- **AND** it MUST state that worker ownership / lease is not implemented until the worker ownership contract is implemented
- **AND** future retry and audit contracts MUST preserve the same operation identity fields

#### Scenario: Contract declares production audit readiness

- **WHEN** a consumer calls the recovery operation contract builder
- **THEN** the contract MUST include recovery audit production readiness evidence
- **AND** the evidence MUST declare operation history and audit summary support
- **AND** it MUST declare `authorization_source = false`

### Requirement: Recovery operation records MUST be compact and non-executable

Recovery operation records MUST contain audit evidence without copying executable internals, and their contract construction SHOULD live behind a dedicated recovery operation Module rather than inside the SDK orchestration class. When worker ownership or retry evidence is supplied, the operation record MUST preserve compact evidence fields without requiring executable internals.

#### Scenario: Operation record is emitted

- **WHEN** the SDK records a recovery operation
- **THEN** the record MUST include operation id, run id, entrypoint, operation status, reason fields, checkpoint/cursor references, continuation reference, workspace evidence, and persistence posture
- **AND** it MUST NOT include Python callable objects, executable handlers, provider clients, or active stream iterators
- **AND** the SDK orchestration path SHOULD delegate recovery operation record construction to the dedicated recovery operation Module
- **AND** supplied worker ownership evidence MUST remain compact and non-executable
- **AND** supplied retry evidence MUST remain compact and non-executable

#### Scenario: Operation record has no ownership evidence

- **WHEN** the SDK records a recovery operation without worker ownership evidence
- **THEN** `worker_ownership.implemented` MUST remain `false`
- **AND** the operation MUST preserve the worker lease boundary without claiming distributed ownership

#### Scenario: Operation record has no retry evidence

- **WHEN** the SDK records a recovery operation outside a retry attempt
- **THEN** the operation MAY omit the `retry` field
- **AND** existing recovery operation consumers MUST continue to work

#### Scenario: SDK recovery gate passes retry evidence to operation record

- **WHEN** an SDK recovery gate records a blocked or failed recovery operation for an explicit retry attempt
- **THEN** the operation record MUST include the supplied retry evidence
- **AND** the operation record MUST NOT include callable continuations, executable handlers, provider clients, or active stream iterators

### Requirement: Successful durable reattachment MUST record recovered operation evidence

The SDK MUST record a recovered operation when a persisted descriptor is reattached through the continuation registry during an actual recovery entrypoint call, and the latest operation evidence MUST be available to the Runtime Surface recovery read model.

#### Scenario: Approved tool continuation recovers via registry

- **GIVEN** a persisted tool continuation descriptor is available
- **AND** the current SDK instance reattaches it through the continuation registry
- **WHEN** `submit_approval(request_id, "approved")` completes recovery
- **THEN** run metadata MUST include a latest recovery operation with `operation_status = recovered`
- **AND** the operation entrypoint MUST be `submit_approval.approved`
- **AND** a subsequent recovery probe MUST expose the latest recovery operation for `run_recovery` consumption

#### Scenario: Loop continuation recovers via registry

- **GIVEN** a persisted loop continuation descriptor is available
- **AND** the current SDK instance reattaches it through the continuation registry
- **WHEN** `resume_run(run_id, continue_loop=True)` completes recovery
- **THEN** run metadata MUST include a latest recovery operation with `operation_status = recovered`
- **AND** the operation entrypoint MUST be `resume_run.continue_loop`
- **AND** a subsequent recovery probe MUST expose the latest recovery operation for `run_recovery` consumption

### Requirement: Fail-closed recovery MUST record blocked operation evidence

The SDK MUST record blocked recovery operation evidence whenever an actual recovery entrypoint fails closed, including worker ownership validation failures when ownership enforcement is explicitly configured.

#### Scenario: Recovery is blocked by workspace or registry gate

- **WHEN** a recovery attempt fails closed because durable workspace, fallback, descriptor, approval state, or registry binding evidence is insufficient
- **THEN** the SDK MUST emit a `recovery_failed_closed` event
- **AND** the event payload MUST include `recovery_operation.operation_status = blocked`
- **AND** run metadata MUST retain the latest recovery operation

#### Scenario: Recovery is blocked by worker ownership gate

- **WHEN** a recovery attempt fails closed because worker ownership validation fails
- **THEN** the SDK MUST emit a `recovery_failed_closed` event
- **AND** the event payload MUST include `recovery_operation.operation_status = blocked`
- **AND** the operation MUST include compact `worker_ownership` evidence
- **AND** run metadata MUST retain the latest recovery operation
