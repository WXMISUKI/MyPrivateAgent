# embedded-sdk-recovery-protocol Specification Delta

## MODIFIED Requirements

### Requirement: Recovery failure MUST be observable

The system MUST write recovery status, failure reason, and compact recovery operation evidence into runtime metadata and event stream whenever a recovery attempt is blocked or fails closed.

#### Scenario: Recovery attempt blocked

- **WHEN** a caller attempts a recovery that is not allowed
- **THEN** the system MUST emit a recovery-related status event
- **AND** the run metadata MUST reflect the latest recovery status and reason
- **AND** the event payload MUST include a recovery operation record with the blocked entrypoint and machine-readable reason

### Requirement: Recovery metadata MUST include persistence evidence

Recovery probe results, successful durable reattachment metadata, and blocked recovery metadata MUST include compact persistence evidence so governance consumers do not infer it from private SDK internals.

#### Scenario: Probe returns persistence evidence

- **WHEN** `probe_run_recovery(run_id)` returns a result
- **THEN** the result includes the current persistence posture
- **AND** it includes workspace backend kind, durability, and fallback status
- **AND** it includes a recovery operation boundary describing supported auditable entrypoints and the worker ownership non-goal

#### Scenario: Recovery failure records persistence blocker

- **WHEN** a recovery attempt fails because the workspace backend is memory-only or degraded
- **THEN** the recovery event metadata includes the persistence blocker
- **AND** the emitted reason remains machine-readable
- **AND** the emitted recovery operation includes the same persistence posture and workspace blocker evidence
