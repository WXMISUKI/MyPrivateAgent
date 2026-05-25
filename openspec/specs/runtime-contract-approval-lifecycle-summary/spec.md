# runtime-contract-approval-lifecycle-summary Specification

## Purpose
Ensure runtime contract summaries expose approval lifecycle recovery coverage and related child executor coverage fields.
## Requirements
### Requirement: Runtime contract summary MUST expose approval lifecycle recovery coverage

The Quality Gate runtime contract summary MUST expose approval lifecycle recovery alignment as a first-class machine-readable coverage object.

#### Scenario: Approval lifecycle alignment check is healthy

- **WHEN** runtime contract smoke emits `approval_lifecycle_recovery_alignment` with `ok = true`
- **AND** `replayed_submission_status = replayed`
- **AND** `ignored_submission_status = ignored`
- **AND** `resolved_recovery_reason = already_resolved`
- **THEN** the runtime contract summary includes `approval_lifecycle_recovery_coverage.alignment_smoke = true`
- **AND** it preserves the replayed, ignored, and recovery reason fields.

#### Scenario: Approval lifecycle alignment check is missing

- **WHEN** a legacy report lacks `approval_lifecycle_recovery_alignment`
- **THEN** the runtime contract summary includes `approval_lifecycle_recovery_coverage.alignment_smoke = false`
- **AND** it emits stable empty default status and reason fields.

### Requirement: Runtime contract gates MUST guard approval lifecycle recovery summary shape

Runtime Contract Gate and Snapshot guards MUST treat approval lifecycle recovery coverage as part of the stable runtime contract summary.

#### Scenario: Runtime Contract Gate normalizes summary coverage

- **WHEN** a quality gate report already includes `approval_lifecycle_recovery_coverage`
- **THEN** Runtime Contract Gate normalizes the field into the runtime contract surface.

#### Scenario: Snapshot summary field is missing

- **WHEN** Runtime Contract Gate lacks `runtime_contract_summary.approval_lifecycle_recovery_coverage`
- **THEN** Runtime Contract Snapshot reports the runtime contract gate as degraded.

### Requirement: Runtime contract summary MUST expose child executor promotion gate coverage

The Quality Gate runtime contract summary MUST expose child executor promotion gate coverage as a first-class machine-readable coverage object.

#### Scenario: Child executor promotion gate check is healthy

- **WHEN** runtime contract smoke emits `child_executor_promotion_gate` with `ok = true`
- **THEN** the runtime contract summary includes `child_executor_promotion_gate_coverage.gate_smoke = true`
- **AND** it preserves the gate status, allow/deny result, failure reason, blocker count, and recommended next step

#### Scenario: Child executor promotion gate check is missing

- **WHEN** a legacy report lacks `child_executor_promotion_gate`
- **THEN** the runtime contract summary includes `child_executor_promotion_gate_coverage.gate_smoke = false`
- **AND** it emits stable empty default evidence

### Requirement: Runtime contract summary MUST expose child executor dispatch coverage

The Quality Gate runtime contract summary MUST expose child executor dispatch coverage as a first-class machine-readable coverage object.

#### Scenario: Child executor dispatch check is healthy

- **WHEN** runtime contract smoke emits `child_executor_dispatch_contract` with `ok = true`
- **THEN** the runtime contract summary includes `child_executor_dispatch_coverage.dispatch_smoke = true`
- **AND** it preserves the dispatch status, readiness, backend readiness, blocker count, and recommended next step

#### Scenario: Child executor dispatch check is missing

- **WHEN** a legacy report lacks `child_executor_dispatch_contract`
- **THEN** the runtime contract summary includes `child_executor_dispatch_coverage.dispatch_smoke = false`
- **AND** it emits stable empty default evidence

### Requirement: Runtime contract summary MUST expose recovery retry evidence coverage

The Quality Gate runtime contract summary MUST expose recovery retry evidence coverage as a first-class machine-readable coverage object.

#### Scenario: Recovery retry evidence check is healthy

- **WHEN** runtime contract smoke emits `recovery_retry_evidence` with `ok = true`
- **AND** the check proves compact exhausted retry evidence for an SDK fail-closed recovery operation
- **THEN** the runtime contract summary includes `recovery_retry_evidence_coverage.retry_smoke = true`
- **AND** it preserves retry status, attempt bounds, terminal flag, recovery reason, and idempotency key presence

#### Scenario: Recovery retry evidence check is missing

- **WHEN** a legacy report lacks `recovery_retry_evidence`
- **THEN** the runtime contract summary includes `recovery_retry_evidence_coverage.retry_smoke = false`
- **AND** it emits stable empty default evidence

### Requirement: Runtime contract gates MUST guard recovery retry evidence summary shape

Runtime Contract Gate and artifact schema guards MUST treat recovery retry evidence coverage as part of the stable runtime contract summary.

#### Scenario: Runtime Contract Gate normalizes retry coverage

- **WHEN** a quality gate report already includes `recovery_retry_evidence_coverage`
- **THEN** Runtime Contract Gate normalizes the field into the runtime contract surface
- **AND** malformed or contradictory retry evidence MUST fail closed with `retry_smoke = false`

#### Scenario: Artifact schema summary field is missing

- **WHEN** a runtime contract summary lacks `recovery_retry_evidence_coverage.retry_smoke`
- **THEN** the runtime contract artifact schema reports the summary as degraded
