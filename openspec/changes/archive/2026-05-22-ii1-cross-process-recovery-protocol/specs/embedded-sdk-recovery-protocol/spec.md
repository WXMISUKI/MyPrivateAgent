## ADDED Requirements

### Requirement: Embedded SDK MUST expose a recovery probe contract
The system MUST provide a standard recovery probe for persisted continuation descriptors before attempting cross-process resume.

#### Scenario: Probe loop continuation recovery
- **WHEN** a caller needs to know whether `resume_run(..., continue_loop=True)` can recover a run from persisted state
- **THEN** the system MUST return a machine-readable recovery probe result
- **AND** the result MUST distinguish between `recoverable` and `unrecoverable`

### Requirement: Persisted descriptor without executable continuation MUST fail closed
The system MUST treat a persisted continuation descriptor without executable continuation as unrecoverable unless a future executable loader explicitly resolves it.

#### Scenario: Missing executable continuation
- **WHEN** a persisted continuation descriptor exists but no executable continuation is available in memory
- **THEN** the system MUST fail closed
- **AND** it MUST expose a stable recovery reason instead of silently pretending recovery succeeded

### Requirement: Recovery failure MUST be observable
The system MUST write recovery status and failure reason into runtime metadata and event stream whenever a recovery attempt is blocked or fails closed.

#### Scenario: Recovery attempt blocked
- **WHEN** a caller attempts a recovery that is not allowed
- **THEN** the system MUST emit a recovery-related status event
- **AND** the run metadata MUST reflect the latest recovery status and reason

### Requirement: Recovery protocol MUST remain independent from durable backend choice
The system MUST keep recovery semantics stable regardless of whether the workspace store is in-memory or SQLAlchemy-backed.

#### Scenario: Different store implementations
- **WHEN** the same persisted continuation descriptor is loaded from different workspace store implementations
- **THEN** the recovery probe and fail-closed semantics MUST remain the same
- **AND** store fallback MUST NOT change the meaning of recovery results
