# durable-recovery-operation-contract Specification

## Purpose

Define a compact, auditable recovery operation contract for Embedded SDK durable recovery entrypoints without claiming distributed worker ownership or executable persistence.

## ADDED Requirements

### Requirement: SDK MUST expose a recovery operation boundary

The Embedded SDK contract MUST declare the supported durable recovery operation entrypoints and the worker ownership boundary.

#### Scenario: Contract declares operation boundary

- **WHEN** a consumer calls `build_contract()`
- **THEN** the contract MUST include `recovery_operation_contract`
- **AND** it MUST list `submit_approval.approved` and `resume_run.continue_loop` as supported operation entrypoints
- **AND** it MUST state that worker ownership / lease is not implemented in this slice

### Requirement: Recovery operation records MUST be compact and non-executable

Recovery operation records MUST contain audit evidence without copying executable internals.

#### Scenario: Operation record is emitted

- **WHEN** the SDK records a recovery operation
- **THEN** the record MUST include operation id, run id, entrypoint, operation status, reason fields, checkpoint/cursor references, continuation reference, workspace evidence, and persistence posture
- **AND** it MUST NOT include Python callable objects, executable handlers, provider clients, or active stream iterators

### Requirement: Successful durable reattachment MUST record recovered operation evidence

The SDK MUST record a recovered operation when a persisted descriptor is reattached through the continuation registry during an actual recovery entrypoint call.

#### Scenario: Approved tool continuation recovers via registry

- **GIVEN** a persisted tool continuation descriptor is available
- **AND** the current SDK instance reattaches it through the continuation registry
- **WHEN** `submit_approval(request_id, "approved")` completes recovery
- **THEN** run metadata MUST include a latest recovery operation with `operation_status = recovered`
- **AND** the operation entrypoint MUST be `submit_approval.approved`

#### Scenario: Loop continuation recovers via registry

- **GIVEN** a persisted loop continuation descriptor is available
- **AND** the current SDK instance reattaches it through the continuation registry
- **WHEN** `resume_run(run_id, continue_loop=True)` completes recovery
- **THEN** run metadata MUST include a latest recovery operation with `operation_status = recovered`
- **AND** the operation entrypoint MUST be `resume_run.continue_loop`

### Requirement: Fail-closed recovery MUST record blocked operation evidence

The SDK MUST record blocked recovery operation evidence whenever an actual recovery entrypoint fails closed.

#### Scenario: Recovery is blocked by workspace or registry gate

- **WHEN** a recovery attempt fails closed because durable workspace, fallback, descriptor, approval state, or registry binding evidence is insufficient
- **THEN** the SDK MUST emit a `recovery_failed_closed` event
- **AND** the event payload MUST include `recovery_operation.operation_status = blocked`
- **AND** run metadata MUST retain the latest recovery operation
