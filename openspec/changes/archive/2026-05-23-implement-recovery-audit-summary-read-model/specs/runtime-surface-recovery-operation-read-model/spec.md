# runtime-surface-recovery-operation-read-model Specification Delta

## MODIFIED Requirements

### Requirement: Runtime Surface MUST expose recovery operation evidence through run_recovery

The Runtime Surface run recovery read model MUST expose compact recovery operation evidence produced by the Embedded SDK, and future audit hardening MUST keep Runtime Surface as the read-side entry for recovery operation summaries.

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
