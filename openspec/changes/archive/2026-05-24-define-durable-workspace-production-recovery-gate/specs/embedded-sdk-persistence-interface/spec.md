## ADDED Requirements

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

#### Scenario: Durable degraded posture

- **WHEN** fallback is active
- **THEN** the production recovery gate reports `overall_status = blocked`
- **AND** fallback MUST NOT be presented as production cross-process recovery
