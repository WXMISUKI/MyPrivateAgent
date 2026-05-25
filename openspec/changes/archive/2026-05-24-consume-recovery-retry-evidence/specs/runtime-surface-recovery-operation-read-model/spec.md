## ADDED Requirements

### Requirement: run_recovery MUST preserve retry summary evidence
The Runtime Surface recovery read model MUST expose retry summary evidence derived from recovery operation history while preserving the existing compact operation boundary.

#### Scenario: run_recovery exposes retry terminal summary
- **WHEN** `RuntimeSurfaceService.get_run_recovery(run_id=...)` returns operation history with terminal retry evidence
- **THEN** `run_recovery.recovery_audit_summary` MUST include the latest retry status
- **AND** it MUST include the latest retry terminal reason
- **AND** it MUST NOT expose executable continuation internals

