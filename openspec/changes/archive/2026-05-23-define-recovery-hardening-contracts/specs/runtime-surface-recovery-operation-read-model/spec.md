# runtime-surface-recovery-operation-read-model Specification Delta

## MODIFIED Requirements

### Requirement: Runtime Surface MUST expose recovery operation evidence through run_recovery

The Runtime Surface run recovery read model MUST expose compact recovery operation evidence produced by the Embedded SDK, and future audit hardening MUST keep Runtime Surface as the read-side entry for recovery operation summaries.

#### Scenario: run_recovery includes operation boundary

- **WHEN** `RuntimeSurfaceService.get_run_recovery(run_id=...)` returns a read model
- **THEN** the read model MUST include `recovery_operation_boundary`
- **AND** the boundary MUST preserve the supported recovery operation entrypoints and worker ownership non-goal
- **AND** future recovery audit summaries MUST be derived from recovery operation evidence rather than executable internals
