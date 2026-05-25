## MODIFIED Requirements

### Requirement: run_recovery MUST preserve retry summary evidence

The Runtime Surface recovery read model MUST expose retry summary evidence derived from recovery operation history while preserving the existing compact operation boundary.

#### Scenario: run_recovery exposes retry terminal summary

- **WHEN** `RuntimeSurfaceService.get_run_recovery(run_id=...)` returns operation history with terminal retry evidence
- **THEN** `run_recovery.recovery_audit_summary` MUST include the latest retry status
- **AND** it MUST include the latest retry terminal reason
- **AND** it MUST NOT expose executable continuation internals

#### Scenario: run_recovery consumes SDK-gate retry evidence

- **WHEN** SDK recovery gates have recorded recovery operations with compact retry evidence
- **THEN** `run_recovery.recovery_operation_history` MUST preserve the normalized retry fields
- **AND** `run_recovery.recovery_audit_summary.retry_status_counts` MUST count those retry statuses
- **AND** latest retry fields MUST be derived from the SDK-produced operation evidence

