## ADDED Requirements

### Requirement: Dispatch result handoff MUST expose compact audit evidence
The system MUST expose a side-effect-free `child_executor_dispatch_result_handoff` contract for child executor dispatcher backend results.

The contract MUST include contract version, overall status, result handoff readiness, dispatch attempt status, backend id, child run id, output reference status, audit reference status, retryable status, parent merge status, missing sections, and next allowed action.

#### Scenario: Sandbox backend result is handoff-ready
- **WHEN** an opt-in dispatcher invocation returns a valid sandbox dispatch attempt envelope
- **THEN** result handoff MUST report `overall_status = ready`
- **AND** it MUST expose compact output and audit reference evidence
- **AND** it MUST report that parent merge has not been performed

#### Scenario: Dispatcher attempt is blocked
- **WHEN** dispatch is blocked before backend invocation
- **THEN** result handoff MUST report `overall_status = blocked`
- **AND** it MUST include the dispatcher blocked reason
- **AND** it MUST NOT report parent merge or production dispatch authorization

#### Scenario: Backend result is malformed
- **WHEN** adapter output is missing required sandbox attempt fields or required references
- **THEN** result handoff MUST fail closed
- **AND** missing sections MUST identify the malformed result evidence
- **AND** callers MUST NOT treat the child executor as successfully handed off

### Requirement: Dispatch result handoff MUST remain separate from merge and retry execution
The system MUST keep dispatch result handoff separate from parent merge, retry scheduling, default worker enablement, and sandbox runtime execution.

#### Scenario: Result handoff is ready
- **WHEN** result handoff reports ready
- **THEN** `parent_merge_performed` MUST remain false
- **AND** `merge_authorization` MUST remain false
- **AND** `retry_scheduled` MUST remain false
- **AND** no background worker or retry loop MUST be started by this contract

### Requirement: Dispatch result handoff coverage MUST enter runtime gates
Runtime smoke, Quality Gate, Runtime Contract Gate, and Snapshot MUST expose child executor dispatch result handoff coverage.

#### Scenario: Coverage is complete
- **WHEN** runtime smoke validates ready, blocked, and malformed result handoff evidence
- **THEN** Quality Gate MUST expose `runtime_contract_summary.child_executor_dispatch_result_handoff_coverage.result_handoff_smoke = true`
- **AND** Runtime Contract Gate MUST preserve normalized result handoff evidence
- **AND** Runtime Contract Snapshot MUST guard the stable coverage fields

#### Scenario: Coverage is missing
- **WHEN** a report omits dispatch result handoff evidence
- **THEN** Quality Gate and Runtime Contract Gate MUST fail closed with `result_handoff_smoke = false`
- **AND** Runtime Contract Snapshot MUST degrade when required summary fields are missing
