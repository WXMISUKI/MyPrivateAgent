# governance-overview-run-state-surface Specification

## Purpose
Define the governance overview run state surface consumed by Runtime Surface and Governance Timeline.
## Requirements
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
- child merge count fields
- child merge section-source evidence

#### Scenario: Parent overview reads run state from backend contract

- **GIVEN** child merged semantics are available for the current runtime scope
- **WHEN** runtime profile is returned
- **THEN** `governance_overview.run` MUST include the parent-facing merge fields
- **AND** it MUST include child merge section source, section ids, and section counts
- **AND** the frontend MUST be able to render parent overview without reconstructing them from child summary cards

### Requirement: Runtime Profile Must Remain Valid Without Explicit Scope

When explicit run scope cannot be resolved, runtime profile MUST remain valid and return an empty-but-typed run overview instead of failing.

#### Scenario: No scope can be resolved

- **GIVEN** no explicit run scope is supplied and no current scheduler runtime can be resolved
- **WHEN** runtime profile is built
- **THEN** `governance_overview.run` MUST still be present
- **AND** the run overview MUST remain empty but structurally valid

### Requirement: Runtime Surface child merge run-state fixtures MUST align with child executor prerequisites
Runtime Surface tests that assert child merge state in `runtime_core` or `governance_overview.run` MUST construct child executor fixtures that satisfy current child executor execution prerequisites.

#### Scenario: Governance run state surfaces merged child semantics
- **WHEN** Runtime Surface test setup expects `runtime_core.child_merge_intent` and `governance_overview.run.child_merge_intent` to reflect executed child output
- **THEN** the setup MUST first produce a successfully merged child executor output
- **AND** it MUST include required execution opt-in evidence instead of relying on blocked child execution fallback semantics

### Requirement: Governance overview run state assembly MUST use a dedicated builder
The system MUST assemble `governance_overview.run` through a concern-specific run-state builder while preserving the Runtime Profile payload shape.

#### Scenario: Builder preserves empty run overview
- **WHEN** no runtime scope can be resolved
- **THEN** the run-state builder MUST return the existing empty-but-typed run overview
- **AND** `governance_overview.run` MUST remain present in Runtime Profile

#### Scenario: Builder preserves scoped run overview
- **WHEN** runtime scope includes run identity and trace fields
- **THEN** the run-state builder MUST preserve `run_id`, `parent_run_id`, `child_run_id`, `child_display_id`, `scheduler_run_id`, `run_kind`, `status`, `trace_count`, and `latest_trace_event`
- **AND** `child_display_id` MUST continue to fall back to `child_run_id` when no explicit display id exists

#### Scenario: Builder preserves parent-facing child merge evidence
- **WHEN** runtime scope includes child merge state and section evidence
- **THEN** the run-state builder MUST preserve `child_merge_*` fields in `governance_overview.run`
- **AND** it MUST keep the child merge section source, section ids, and section counts intact
