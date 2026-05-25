## ADDED Requirements

### Requirement: Workspace backend description MUST support persistence posture derivation

Workspace backend descriptions MUST expose enough stable fields for the SDK persistence interface to derive memory, durable-ready, and durable-degraded postures.

#### Scenario: Derive memory preview
- **WHEN** `describe_backend()` returns `durable = false`
- **THEN** the SDK persistence interface can derive `persistence_posture = memory_preview`
- **AND** it does not need to inspect private workspace store implementation details

#### Scenario: Derive durable ready
- **WHEN** `describe_backend()` returns `durable = true` and `fallback_active = false`
- **THEN** the SDK persistence interface can derive `persistence_posture = durable_ready`
- **AND** it can report the backend kind and mode as evidence

#### Scenario: Derive durable degraded
- **WHEN** `describe_backend()` returns `durable = true` and `fallback_active = true`
- **THEN** the SDK persistence interface can derive `persistence_posture = durable_degraded`
- **AND** it can expose `fallback_reason` as a machine-readable blocker

### Requirement: State vocabulary MUST remain storage-focused

The durable workspace state contract MUST keep durable state kinds and runtime-only state kinds as storage vocabulary, not as recovery outcome claims.

#### Scenario: Durable state vocabulary remains separate from recovery
- **WHEN** a backend lists `tool_continuation_descriptor` or `loop_continuation_descriptor` as durable state kinds
- **THEN** the SDK persistence interface may treat the backend as descriptor-capable
- **AND** recovery probes MUST still verify descriptor presence, registry binding, and run state before reporting a run as recoverable
