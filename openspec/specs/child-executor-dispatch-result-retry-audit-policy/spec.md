# child-executor-dispatch-result-retry-audit-policy Specification

## Purpose

Define the side-effect-free retry posture contract for child executor dispatch result handoff evidence.

## Requirements

### Requirement: Dispatch result retry audit policy MUST classify retry posture
The system MUST expose a side-effect-free `child_executor_dispatch_result_retry_audit_policy` contract for child executor dispatch result handoff evidence.

The contract MUST classify result posture as `not_required`, `retryable`, `terminal`, or `blocked`.

#### Scenario: Successful result does not require retry
- **WHEN** result handoff is ready and backend result status is successful
- **THEN** retry audit policy MUST report `overall_status = ready`
- **AND** `retry_policy_status = not_required`
- **AND** `retry_scheduled = false`

#### Scenario: Retryable failure is audit-ready
- **WHEN** result handoff includes retryable failure evidence
- **AND** idempotency and audit evidence are present
- **THEN** retry audit policy MUST report `retry_policy_status = retryable`
- **AND** it MUST preserve error code and retry reason
- **AND** it MUST NOT schedule retry execution

#### Scenario: Terminal failure is not retryable
- **WHEN** result handoff is blocked by unsafe payload, malformed backend result, missing adapter, or policy-denied dispatch
- **THEN** retry audit policy MUST report `retry_policy_status = terminal`
- **AND** `will_retry = false`
- **AND** missing sections or terminal reason MUST be machine-readable

### Requirement: Retryable policy MUST require idempotency and audit evidence
The system MUST require compact idempotency and audit evidence before retryable dispatch result evidence can be treated as retry-audit-ready.

#### Scenario: Retryable result lacks idempotency
- **WHEN** retryable failure evidence omits idempotency evidence
- **THEN** retry audit policy MUST fail closed with `overall_status = blocked`
- **AND** missing sections MUST include `idempotency_evidence`
- **AND** `retry_scheduled` MUST remain false

### Requirement: Dispatch result retry audit policy coverage MUST enter runtime gates
Runtime smoke, Quality Gate, Runtime Contract Gate, and Snapshot MUST expose child executor dispatch result retry audit policy coverage.

#### Scenario: Coverage is complete
- **WHEN** runtime smoke validates success/no-retry, retryable, terminal, and missing-idempotency paths
- **THEN** Quality Gate MUST expose `runtime_contract_summary.child_executor_dispatch_result_retry_audit_coverage.retry_audit_smoke = true`
- **AND** Runtime Contract Gate MUST preserve normalized retry audit evidence
- **AND** Runtime Contract Snapshot MUST guard stable coverage fields

#### Scenario: Coverage is missing
- **WHEN** a report omits retry audit evidence
- **THEN** Quality Gate and Runtime Contract Gate MUST fail closed with `retry_audit_smoke = false`
- **AND** Snapshot MUST degrade when required summary fields are missing
