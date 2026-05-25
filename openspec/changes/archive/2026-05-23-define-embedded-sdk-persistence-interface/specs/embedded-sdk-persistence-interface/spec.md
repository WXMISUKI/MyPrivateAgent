## ADDED Requirements

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
