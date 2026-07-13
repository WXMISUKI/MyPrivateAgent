## MODIFIED Requirements

### Requirement: Persistence interface MUST expose production recovery gate evidence
The embedded SDK persistence interface MUST include production recovery gate evidence that distinguishes backend durability from production cross-process recovery readiness and MUST expose explicit production recovery authorization dry-run evidence as a separate contract.

#### Scenario: Memory preview posture

- **WHEN** the persistence interface reports `memory_preview`
- **THEN** the production recovery gate reports `overall_status = blocked`
- **AND** `production_default_enabled = false`
- **AND** the production recovery authorization dry-run reports `overall_status = blocked`
- **AND** it MUST keep `will_execute = false`

#### Scenario: Durable ready posture

- **WHEN** the persistence interface reports `durable_ready`
- **THEN** the production recovery gate may mark durable workspace backend ready
- **AND** it MUST remain blocked unless descriptor lifecycle, registry binding, checkpoint/cursor, ownership, audit, rollout, and loader handoff evidence are complete
- **AND** the production recovery authorization dry-run MUST remain blocked until explicit authorization input source evidence is also ready

#### Scenario: Descriptor lifecycle governance is available

- **WHEN** continuation descriptor lifecycle governance is implemented
- **THEN** the production recovery gate may mark `descriptor_lifecycle_governance` as ready
- **AND** it MUST remain blocked while registry binding, checkpoint/cursor, ownership, audit, rollout, or loader handoff evidence is missing
- **AND** the production recovery authorization dry-run MUST NOT treat descriptor lifecycle readiness as authorization source

#### Scenario: Handoff policy is available

- **WHEN** durable loader execution handoff policy is implemented
- **THEN** the production recovery gate may mark `loader_execution_handoff_policy` as ready
- **AND** it MUST remain blocked while registry binding, checkpoint/cursor, ownership, audit, or rollout evidence is missing
- **AND** the production recovery authorization dry-run MUST remain blocked while explicit authorization input source is missing

#### Scenario: Recovery audit operation history is available

- **WHEN** recovery audit production readiness is implemented
- **THEN** the production recovery gate may mark `recovery_audit_operation_history` as ready
- **AND** it MUST remain blocked while registry binding, checkpoint/cursor, ownership, or rollout evidence is missing
- **AND** the production recovery authorization dry-run MUST keep audit evidence descriptive rather than executable

#### Scenario: Registry/checkpoint policy is available

- **WHEN** registry/checkpoint production policy readiness is implemented
- **THEN** the production recovery gate may mark `registry_binding_resolution` and `checkpoint_resume_cursor_gate` as ready
- **AND** it MUST remain blocked while worker ownership or rollout evidence is missing
- **AND** default production recovery execution remains disabled

#### Scenario: Worker ownership production gate is provided

- **WHEN** the runtime factory builds the embedded persistence interface with worker ownership production gate evidence
- **THEN** `persistence_interface.production_recovery_gate` MUST preserve compact worker ownership gate status and blocker evidence
- **AND** this evidence MUST NOT enable default cross-process recovery while ownership or rollout remains blocked
- **AND** the production recovery authorization dry-run MUST consume worker ownership enablement input evidence separately from the linked production gate

#### Scenario: Durable degraded posture

- **WHEN** fallback is active
- **THEN** the production recovery gate reports `overall_status = blocked`
- **AND** fallback MUST NOT be presented as production cross-process recovery
- **AND** the production recovery authorization dry-run MUST remain blocked

