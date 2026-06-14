# embedded-sdk-persistence-interface Specification

## Purpose

This specification defines the Embedded SDK persistence posture contract. It describes the storage capability selected for the current embedded runtime and keeps that posture separate from run-specific recovery readiness.

## Requirements

### Requirement: SDK MUST expose persistence posture

The embedded SDK runtime contract MUST expose a machine-readable persistence posture for the current workspace backend.

#### Scenario: Memory preview posture
- **WHEN** the SDK is constructed with an in-memory workspace backend
- **THEN** the persistence interface reports `persistence_posture = memory_preview`
- **AND** it reports `durable = false`
- **AND** it does not claim cross-process recovery readiness

#### Scenario: Durable ready posture
- **WHEN** the SDK is constructed with a durable workspace backend that is not in fallback mode
- **THEN** the persistence interface reports `persistence_posture = durable_ready`
- **AND** it reports `durable = true`
- **AND** it marks the runtime as a cross-process recovery candidate without claiming a specific run is recoverable

#### Scenario: Durable degraded posture
- **WHEN** the configured durable workspace backend is in fallback mode
- **THEN** the persistence interface reports `persistence_posture = durable_degraded`
- **AND** it exposes the fallback reason
- **AND** recovery consumers MUST treat cross-process recovery as blocked

### Requirement: SDK and Facade MUST share persistence bootstrap

SDK and facade default construction MUST use the same embedded runtime dependency seam for persistence and continuation registry defaults.

#### Scenario: Shared factory construction
- **WHEN** a caller creates an SDK and an `AgentHarnessFacade` through `EmbeddedRuntimeFactory`
- **THEN** both runtimes use the same workspace store source
- **AND** both runtimes use the same continuation registry source
- **AND** their persistence posture is derived from the same backend description

#### Scenario: No ad hoc durable flag
- **WHEN** a caller or internal service needs durable embedded runtime behavior
- **THEN** the system MUST derive durability from the workspace backend description
- **AND** it MUST NOT treat a standalone constructor flag as proof of durable recovery support

### Requirement: Runtime dependencies MUST centralize embedded recovery seams

The embedded runtime dependency bundle MUST centralize shared recovery seams used by SDK, facade, and Runtime Surface consumers.

#### Scenario: Dependency bundle exposes recovery seams

- **WHEN** the embedded runtime factory contract is inspected
- **THEN** dependency sources MUST include `workspace_store`, `continuation_registry`, and `worker_ownership_store`
- **AND** worker ownership durability MUST be reported separately from workspace persistence posture
- **AND** worker ownership availability MUST NOT imply durable workspace readiness

### Requirement: Persistence interface MUST stay separate from recovery result

The persistence interface MUST describe storage capability and fallback state, while recovery probes MUST decide whether a specific run can resume.

#### Scenario: Durable backend without descriptor
- **WHEN** the persistence interface reports `persistence_posture = durable_ready`
- **AND** a run has no persisted continuation descriptor
- **THEN** `probe_run_recovery(run_id)` MUST still report the run as unrecoverable
- **AND** the recovery reason MUST remain descriptor-specific

#### Scenario: Memory backend with in-process continuation
- **WHEN** the persistence interface reports `persistence_posture = memory_preview`
- **AND** an in-process continuation is available
- **THEN** the SDK MAY report in-process recovery as recoverable
- **AND** it MUST NOT present that as cross-process durable recovery

### Requirement: Persistence posture MUST enter runtime contract gates

Runtime contract smoke and quality gate summaries MUST include evidence that persistence posture is normalized consistently.

#### Scenario: Smoke evidence
- **WHEN** runtime contract smoke runs embedded SDK persistence checks
- **THEN** the smoke output includes memory-preview evidence
- **AND** it includes durable or durable-degraded evidence through a controlled backend sample

#### Scenario: Gate summary
- **WHEN** quality gate or runtime contract gate reads persistence smoke evidence
- **THEN** it exposes a compact coverage summary
- **AND** missing evidence fails closed rather than silently claiming persistence coverage

### Requirement: Persistence interface MUST expose production recovery gate evidence

The embedded SDK persistence interface MUST include production recovery gate evidence that distinguishes backend durability from production cross-process recovery readiness.

#### Scenario: Memory preview posture

- **WHEN** the persistence interface reports `memory_preview`
- **THEN** the production recovery gate reports `overall_status = blocked`
- **AND** `production_default_enabled = false`

#### Scenario: Durable ready posture

- **WHEN** the persistence interface reports `durable_ready`
- **THEN** the production recovery gate may mark durable workspace backend ready
- **AND** it MUST remain blocked unless descriptor lifecycle, registry binding, checkpoint/cursor, ownership, audit, rollout, and loader handoff evidence are complete

#### Scenario: Descriptor lifecycle governance is available

- **WHEN** continuation descriptor lifecycle governance is implemented
- **THEN** the production recovery gate may mark `descriptor_lifecycle_governance` as ready
- **AND** it MUST remain blocked while registry binding, checkpoint/cursor, ownership, audit, rollout, or loader handoff evidence is missing

#### Scenario: Handoff policy is available

- **WHEN** durable loader execution handoff policy is implemented
- **THEN** the production recovery gate may mark `loader_execution_handoff_policy` as ready
- **AND** it MUST remain blocked while registry binding, checkpoint/cursor, ownership, audit, or rollout evidence is missing

#### Scenario: Recovery audit operation history is available

- **WHEN** recovery audit production readiness is implemented
- **THEN** the production recovery gate may mark `recovery_audit_operation_history` as ready
- **AND** it MUST remain blocked while registry binding, checkpoint/cursor, ownership, or rollout evidence is missing

#### Scenario: Registry/checkpoint policy is available

- **WHEN** registry/checkpoint production policy readiness is implemented
- **THEN** the production recovery gate may mark `registry_binding_resolution` and `checkpoint_resume_cursor_gate` as ready
- **AND** it MUST remain blocked while worker ownership or rollout evidence is missing

#### Scenario: Worker ownership production gate is provided

- **WHEN** the runtime factory builds the embedded persistence interface with worker ownership production gate evidence
- **THEN** `persistence_interface.production_recovery_gate` MUST preserve compact worker ownership gate status and blocker evidence
- **AND** this evidence MUST NOT enable default cross-process recovery while ownership or rollout remains blocked

#### Scenario: Durable degraded posture

- **WHEN** fallback is active
- **THEN** the production recovery gate reports `overall_status = blocked`
- **AND** fallback MUST NOT be presented as production cross-process recovery

### Requirement: Persistence posture MUST gate recovery acceptance

The Embedded SDK recovery acceptance smoke MUST use persistence posture as a gate for explicit durable recovery consumption.

#### Scenario: Durable ready posture can pass acceptance with registry evidence

- **WHEN** the workspace backend reports durable ready posture
- **AND** required continuation registry bindings are present
- **THEN** the acceptance smoke MAY report `decision = accepted`
- **AND** it MUST still describe production auto-recovery as gated

#### Scenario: Memory preview posture blocks durable acceptance

- **WHEN** the workspace backend reports memory preview posture
- **THEN** the acceptance smoke MUST report `decision = blocked`
- **AND** it MUST keep any in-process recovery evidence separate from durable cross-process recovery acceptance
