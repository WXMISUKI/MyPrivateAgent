## ADDED Requirements

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

Recovery probe results and blocked recovery metadata MUST include compact persistence evidence so governance consumers do not infer it from private SDK internals.

#### Scenario: Probe returns persistence evidence
- **WHEN** `probe_run_recovery(run_id)` returns a result
- **THEN** the result includes the current persistence posture
- **AND** it includes workspace backend kind, durability, and fallback status

#### Scenario: Recovery failure records persistence blocker
- **WHEN** a recovery attempt fails because the workspace backend is memory-only or degraded
- **THEN** the recovery event metadata includes the persistence blocker
- **AND** the emitted reason remains machine-readable
