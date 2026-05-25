# runtime-surface-recovery-operation-read-model Specification

## ADDED Requirements

### Requirement: Runtime Surface MUST expose recovery operation evidence through run_recovery

The Runtime Surface run recovery read model MUST expose compact recovery operation evidence produced by the Embedded SDK.

#### Scenario: run_recovery includes operation boundary

- **WHEN** `RuntimeSurfaceService.get_run_recovery(run_id=...)` returns a read model
- **THEN** the read model MUST include `recovery_operation_boundary`
- **AND** the boundary MUST preserve the supported recovery operation entrypoints and worker ownership non-goal

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

### Requirement: Runtime Surface recovery operation payload MUST remain non-executable

The Runtime Surface read model MUST NOT expose executable continuation internals.

#### Scenario: Operation evidence is normalized

- **WHEN** recovery operation evidence is copied from SDK probe output into `run_recovery`
- **THEN** the read model MUST preserve only compact fields
- **AND** it MUST NOT include Python callable objects, executable handlers, provider clients, or active stream iterators
