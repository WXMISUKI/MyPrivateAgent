## ADDED Requirements

### Requirement: Runtime Surface must expose runtime-plane projection readiness
The system SHALL expose a top-level Runtime Surface read-only profile for runtime-plane governance projections.

#### Scenario: Runtime profile is built without a supplied projection
- **WHEN** `RuntimeSurfaceService.get_runtime_profile()` is called
- **THEN** the profile includes `runtime_plane_governance_profile`
- **AND** the profile reports `projection_contract_status = ready`
- **AND** it reports `latest_projection_available = false`
- **AND** it explains that no projection source is currently available

### Requirement: Runtime-plane profile must summarize supplied projection compactly
The system SHALL compactly summarize a supplied runtime-plane governance projection.

#### Scenario: Projection is supplied to the builder
- **WHEN** the builder receives a runtime-plane `governance_projection`
- **THEN** it reports `latest_projection_available = true`
- **AND** it exposes request id, run id, agent id, adapter id, result status, event count, stage counts, tool call count, approval indicators, and trace reference
- **AND** it does not expose raw state, raw messages, tool handlers, callables, provider clients, or active streams

### Requirement: Runtime-plane profile must remain side-effect-free
The system SHALL keep the Runtime Surface runtime-plane profile read-only.

#### Scenario: Runtime profile includes runtime-plane governance profile
- **WHEN** the profile is generated
- **THEN** it does not execute adapters
- **AND** it does not write trace, audit, approval, scheduler, checkpoint, worker, memory, provider, or chat state
- **AND** it reports explicit boundary flags for those non-actions

### Requirement: Runtime-plane profile must be guarded by contract snapshot
The system SHALL guard the runtime-plane governance profile through Runtime Contract Snapshot.

#### Scenario: Contract snapshot is built
- **WHEN** `RuntimeContractSnapshotService` builds a snapshot for Runtime Surface
- **THEN** it checks stable fields for `runtime_plane_governance_profile`
- **AND** missing stable fields degrade the snapshot
