## MODIFIED Requirements

### Requirement: Production recovery MUST require descriptor lifecycle governance

Default cross-process recovery MUST require descriptor lifecycle evidence for creation, binding, readiness, staleness, resolution, and unsafe payload rejection.

#### Scenario: Descriptor lifecycle is governed

- **WHEN** continuation descriptor lifecycle governance is implemented and covered by runtime quality gates
- **THEN** the production recovery gate marks `descriptor_lifecycle_governance` as ready
- **AND** the gate still remains blocked when worker ownership, audit, rollout, registry policy, checkpoint/cursor gate, or loader handoff sections are missing

#### Scenario: Descriptor lifecycle is incomplete

- **WHEN** descriptors are persisted but lifecycle state governance is incomplete
- **THEN** the production recovery gate remains blocked
- **AND** missing descriptor lifecycle sections are machine-readable
