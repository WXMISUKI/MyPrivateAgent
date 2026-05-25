## ADDED Requirements

### Requirement: Runtime recovery MUST expose durable checkpoint status
The system MUST expose machine-readable durable checkpoint status for embedded runtime runs.

#### Scenario: Durable checkpoint is available
- **GIVEN** a run has persisted run snapshot, event log, approval snapshot, and continuation descriptor
- **AND** the workspace backend is durable and not in fallback mode
- **WHEN** recovery is probed for that run
- **THEN** the recovery payload MUST include `checkpoint.status = ready`
- **AND** it MUST include a stable `checkpoint.contract_version`
- **AND** it MUST identify the checkpoint kind and run state

#### Scenario: Durable checkpoint is missing
- **GIVEN** no durable checkpoint can be derived for a run
- **WHEN** recovery is probed for that run
- **THEN** the recovery payload MUST include `checkpoint.status = missing`
- **AND** recovery MUST remain unrecoverable with `recovery_reason = checkpoint_missing`

### Requirement: Runtime recovery MUST expose resume cursor status
The system MUST derive a resume cursor when a checkpoint maps to a supported recovery entrypoint.

#### Scenario: Approval continuation can resume through registry
- **GIVEN** a pending approval checkpoint references a continuation descriptor with a registered binding id
- **AND** the current continuation registry can resolve that binding
- **WHEN** recovery is probed for the run
- **THEN** the recovery payload MUST include `resume_cursor.cursor_status = ready`
- **AND** `resume_cursor.entrypoint = submit_approval.approved`
- **AND** `resume_cursor.recovery_reason = ready_via_registry`

#### Scenario: Cursor requires missing binding
- **GIVEN** a checkpoint references a continuation descriptor binding id
- **AND** the current continuation registry cannot resolve that binding
- **WHEN** recovery is probed for the run
- **THEN** the recovery payload MUST include `resume_cursor.cursor_status = blocked`
- **AND** `resume_cursor.recovery_reason = missing_registered_binding`
- **AND** execution MUST NOT resume

### Requirement: Resolved approvals MUST produce stale or state-gated cursors
The system MUST NOT derive an executable approval resume cursor for approvals that have already resolved.

#### Scenario: Approval already approved
- **GIVEN** an approval has status `approved`
- **WHEN** the run recovery read model is requested
- **THEN** the approval entrypoint MUST be state-gated or stale
- **AND** the machine-readable reason MUST include `already_resolved`

#### Scenario: Approval denied
- **GIVEN** an approval has status `denied`
- **WHEN** the run recovery read model is requested
- **THEN** the approval entrypoint MUST NOT be recoverable
- **AND** the machine-readable reason MUST include `denied`

### Requirement: Runtime contract smoke MUST cover checkpoint and cursor alignment
The runtime contract smoke gate MUST prove checkpoint and resume cursor alignment using executable embedded runtime samples.

#### Scenario: Smoke validates durable checkpoint recovery
- **WHEN** `runtime_contract_smoke.py` runs
- **THEN** it MUST emit a check for durable checkpoint/resume cursor alignment
- **AND** the check MUST include checkpoint status, cursor status, recovery reason, and approval lifecycle alignment evidence

#### Scenario: Quality gate summarizes checkpoint recovery coverage
- **WHEN** `quality_gate_report.py` reads runtime contract smoke output
- **THEN** `runtime_contract_summary` MUST expose checkpoint/resume cursor coverage
- **AND** missing or malformed smoke evidence MUST fail closed
