## MODIFIED Requirements

### Requirement: Runtime Surface MUST expose recovery operation evidence through run_recovery

The Runtime Surface run recovery read model MUST expose compact recovery operation evidence produced by the Embedded SDK, and future audit hardening MUST keep Runtime Surface as the read-side entry for recovery operation summaries.

#### Scenario: run_recovery includes operation boundary

- **WHEN** `RuntimeSurfaceService.get_run_recovery(run_id=...)` returns a read model
- **THEN** the read model MUST include `recovery_operation_boundary`
- **AND** the boundary MUST preserve the supported recovery operation entrypoints and worker ownership non-goal
- **AND** future recovery audit summaries MUST be derived from recovery operation evidence rather than executable internals

#### Scenario: run_recovery includes latest recovered operation

- **GIVEN** a run has completed a registry-backed recovery operation
- **WHEN** `RuntimeSurfaceService.get_run_recovery(run_id=...)` is called
- **THEN** the read model MUST include `latest_recovery_operation.operation_status = recovered`
- **AND** it MUST include the operation entrypoint and compact persistence evidence

#### Scenario: run_recovery includes bounded operation history

- **WHEN** recovery operation history exists in SDK run metadata
- **THEN** the read model MUST expose `recovery_operation_history`
- **AND** it MUST expose `recovery_operation_count`
- **AND** the history MUST remain bounded and compact
- **AND** the read model MUST expose `recovery_audit_summary` derived from the bounded operation history

#### Scenario: run_recovery includes audit summary without operation history

- **WHEN** no recovery operation history exists
- **THEN** `run_recovery.recovery_audit_summary.operation_count` MUST be `0`
- **AND** existing recovery read model fields MUST remain available

### Requirement: Runtime Surface recovery operation payload MUST remain non-executable

The Runtime Surface read model MUST NOT expose executable continuation internals.

#### Scenario: Operation evidence is normalized

- **WHEN** recovery operation evidence is copied from SDK probe output into `run_recovery`
- **THEN** the read model MUST preserve only compact fields
- **AND** it MUST NOT include Python callable objects, executable handlers, provider clients, or active stream iterators

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
