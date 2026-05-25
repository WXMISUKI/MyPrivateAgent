## ADDED Requirements

### Requirement: Runtime Profile Must Accept Explicit Run Scope

Runtime profile APIs MUST accept optional runtime scope identifiers so the backend can build a stable parent overview contract from explicit context when available.

The accepted scope identifiers MUST include:

- `run_id`
- `parent_run_id`
- `child_run_id`
- `scheduler_run_id`

#### Scenario: Explicit run scope is supplied

- **GIVEN** the caller supplies run scope identifiers
- **WHEN** runtime profile is built
- **THEN** the backend MUST use those identifiers as the primary source of run identity
- **AND** the resulting `governance_overview.run` MUST reflect the supplied scope

### Requirement: Governance Overview Run Contract Must Surface Child Merge State

`governance_overview.run` MUST expose the stable parent-facing child merge state so frontend consumers do not need to reconstruct it from separate child merged semantics read models.

The run contract MUST include:

- current run identity fields
- latest trace summary
- `child_merge_intent`
- `child_merge_entities`
- `child_merge_conclusion`

#### Scenario: Parent overview reads run state from backend contract

- **GIVEN** child merged semantics are available for the current runtime scope
- **WHEN** runtime profile is returned
- **THEN** `governance_overview.run` MUST include the parent-facing merge fields
- **AND** the frontend MUST be able to render parent overview without reconstructing them from child summary cards

### Requirement: Runtime Profile Must Remain Valid Without Explicit Scope

When explicit run scope cannot be resolved, runtime profile MUST remain valid and return an empty-but-typed run overview instead of failing.

#### Scenario: No scope can be resolved

- **GIVEN** no explicit run scope is supplied and no current scheduler runtime can be resolved
- **WHEN** runtime profile is built
- **THEN** `governance_overview.run` MUST still be present
- **AND** the run overview MUST remain empty but structurally valid

