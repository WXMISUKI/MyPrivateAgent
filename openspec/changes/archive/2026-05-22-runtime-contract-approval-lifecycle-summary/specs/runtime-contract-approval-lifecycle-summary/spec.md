# runtime-contract-approval-lifecycle-summary

## ADDED Requirements

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
