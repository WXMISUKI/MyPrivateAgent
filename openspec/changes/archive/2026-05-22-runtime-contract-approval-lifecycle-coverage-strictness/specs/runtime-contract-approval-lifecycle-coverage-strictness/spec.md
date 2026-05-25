# runtime-contract-approval-lifecycle-coverage-strictness

## ADDED Requirements

### Requirement: Approval lifecycle recovery coverage MUST be fail-closed

Runtime Contract Gate and degraded trace normalization MUST recompute approval lifecycle recovery coverage from its machine-readable fields.

#### Scenario: Coverage flag is true but evidence disagrees

- **WHEN** `approval_lifecycle_recovery_coverage.alignment_smoke` is truthy
- **AND** at least one of `replayed_submission_status`, `ignored_submission_status`, or `resolved_recovery_reason` is not the expected value
- **THEN** normalized `alignment_smoke` MUST be `false`
- **AND** the original status and reason fields MUST remain visible for diagnostics.

#### Scenario: Coverage evidence is complete

- **WHEN** `alignment_smoke` is truthy
- **AND** `replayed_submission_status = replayed`
- **AND** `ignored_submission_status = ignored`
- **AND** `resolved_recovery_reason = already_resolved`
- **THEN** normalized `alignment_smoke` MAY be `true`.
