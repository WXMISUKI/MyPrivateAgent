# embedded-sdk-recovery-protocol Specification

## Purpose
Define the Embedded SDK recovery protocol for checkpoint, resume cursor, and registry-backed recovery decisions.
## Requirements

### Requirement: SDK recovery probe MUST expose durable checkpoint and resume cursor evidence

The SDK recovery probe MUST expose compact checkpoint and resume cursor evidence for durable recovery consumers without executing recovery.

#### Scenario: Production policy consumes checkpoint and cursor evidence

- **WHEN** registry-backed checkpoint and resume cursor evidence is available
- **THEN** production registry/checkpoint policy readiness MAY use that evidence as gate input
- **AND** it MUST NOT execute recovery or authorize default cross-process recovery by itself

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
The system MUST write recovery status, failure reason, and compact recovery operation evidence into runtime metadata and event stream whenever a recovery attempt is blocked or fails closed.

#### Scenario: Recovery attempt blocked
- **WHEN** a caller attempts a recovery that is not allowed
- **THEN** the system MUST emit a recovery-related status event
- **AND** the run metadata MUST reflect the latest recovery status and reason
- **AND** the event payload MUST include a recovery operation record with the blocked entrypoint and machine-readable reason

### Requirement: Recovery protocol MUST remain independent from durable backend choice
The system MUST keep recovery semantics stable regardless of whether the workspace store is in-memory or SQLAlchemy-backed.

#### Scenario: Different store implementations
- **WHEN** the same persisted continuation descriptor is loaded from different workspace store implementations
- **THEN** the recovery probe and fail-closed semantics MUST remain the same
- **AND** store fallback MUST NOT change the meaning of recovery results

### Requirement: Recovery probe MUST align with persistence posture

The recovery probe MUST keep its run-specific recovery result aligned with, but separate from, the SDK persistence posture.

#### Scenario: Durable degraded blocks cross-process recovery
- **WHEN** the persistence interface reports `persistence_posture = durable_degraded`
- **THEN** a recovery probe that requires durable workspace MUST report an unrecoverable result
- **AND** the recovery reason MUST identify workspace fallback as the blocker

#### Scenario: Durable ready still requires run evidence
- **WHEN** the persistence interface reports `persistence_posture = durable_ready`
- **AND** the run is missing required continuation descriptor or registry binding evidence
- **THEN** the recovery probe MUST report the run as unrecoverable
- **AND** it MUST expose the descriptor or binding blocker rather than using durable readiness as a shortcut

#### Scenario: Memory preview stays in-process only
- **WHEN** the persistence interface reports `persistence_posture = memory_preview`
- **THEN** recovery probes MUST NOT label recovery as cross-process durable recovery
- **AND** any recoverable result MUST remain scoped to in-process continuation availability

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

### Requirement: Recovery protocol MUST require production gate for default cross-process recovery

The recovery protocol MUST keep run-specific recovery probes separate from production default recovery enablement.

#### Scenario: Probe is recoverable but production gate is blocked

- **WHEN** a run-specific probe reports a registry-backed recoverable candidate
- **AND** the production recovery gate is blocked
- **THEN** recovery remains explicit or conditional
- **AND** default background or automatic cross-process recovery MUST NOT execute

#### Scenario: Probe is recoverable and handoff policy is defined

- **WHEN** a run-specific probe reports a registry-backed recoverable candidate
- **AND** loader execution handoff policy is ready
- **THEN** recovery remains explicit or conditional
- **AND** default background or automatic cross-process recovery MUST NOT execute
- **AND** missing executor binding MUST remain a fail-closed handoff decision

### Requirement: Recovery protocol MUST define descriptor lifecycle evidence

The recovery protocol MUST expose descriptor lifecycle evidence before cross-process recovery can be production-default.

#### Scenario: Descriptor lifecycle is governed

- **WHEN** a descriptor participates in production recovery
- **THEN** lifecycle evidence MUST distinguish created, bound, ready, stale, resolved, and unsafe states
- **AND** unsafe callable-like payloads MUST remain fail-closed
- **AND** lifecycle readiness MUST NOT bypass checkpoint/resume cursor, worker ownership, audit, or loader handoff gates

### Requirement: Recovery protocol MUST be acceptance-smoke verifiable

The Embedded SDK recovery protocol MUST expose enough compact evidence for a deterministic acceptance smoke to verify explicit durable registry-backed recovery consumption without enabling default automatic recovery.

#### Scenario: Acceptance smoke consumes recovery protocol evidence

- **WHEN** the acceptance smoke probes and exercises `submit_approval.approved` and `resume_run.continue_loop`
- **THEN** the recovery protocol MUST provide machine-readable recoverability, entrypoint, recovery reason, and latest operation evidence
- **AND** accepted evidence MUST NOT authorize worker lease, background recovery, distributed execution, or default `/api/chat` behavior changes
