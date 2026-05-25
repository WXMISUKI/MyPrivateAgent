## ADDED Requirements

### Requirement: SDK approval lifecycle trace adapter MUST be opt-in

The Embedded SDK MUST NOT require governance trace persistence to execute approval lifecycle operations.

#### Scenario: Recorder is not configured
- **WHEN** the SDK emits `approval_resolved`, `approval_replayed`, `approval_ignored`, or `recovery_failed_closed`
- **AND** no approval lifecycle trace recorder is configured
- **THEN** SDK execution continues normally
- **AND** the SDK event stream remains available as the local source of truth

#### Scenario: Recorder fails
- **WHEN** a configured approval lifecycle trace recorder raises or returns failure
- **THEN** SDK execution MUST continue
- **AND** the approval decision or recovery failure semantics MUST NOT change

### Requirement: Adapter MUST record compact governance evidence

The adapter MUST map selected SDK approval lifecycle events to compact runtime trace evidence without copying executable internals.

#### Scenario: Approval resolved is recorded
- **WHEN** `submit_approval(...)` accepts a pending approval decision
- **THEN** the adapter records a trace event containing `run_id`, `approval_request_id`, `status_kind = approval_resolved`, decision, and approval status
- **AND** it MUST NOT include executable continuation callables

#### Scenario: Replay and ignored submissions are recorded
- **WHEN** `submit_approval(...)` returns replayed or ignored lifecycle status
- **THEN** the adapter records `approval_replayed` or `approval_ignored` with original and attempted decision evidence where available
- **AND** it MUST preserve the SDK-owned lifecycle status kind

#### Scenario: Recovery blocked is recorded
- **WHEN** an approval recovery attempt emits `recovery_failed_closed`
- **THEN** the adapter records recovery blocker evidence including machine-readable `recovery_reason` or `blocked_reason`
- **AND** it MUST NOT reinterpret the recovery reason

### Requirement: Adapter MUST dedupe lifecycle trace writes

The adapter MUST use a stable dedupe key for approval lifecycle trace writes.

#### Scenario: Duplicate replay submission
- **WHEN** the same replayed approval lifecycle evidence is recorded more than once
- **THEN** the adapter MUST avoid writing duplicate runtime trace entries when the trace service can detect the same dedupe key

#### Scenario: Distinct lifecycle status
- **WHEN** the same approval later produces a different lifecycle status kind
- **THEN** the adapter MUST use a distinct dedupe key
- **AND** the new status may produce a separate trace entry

