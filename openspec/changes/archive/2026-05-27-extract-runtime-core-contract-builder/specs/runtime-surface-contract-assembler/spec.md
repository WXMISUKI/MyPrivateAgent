## ADDED Requirements

### Requirement: Runtime Core contract assembly MUST use a concern-specific builder
The system MUST assemble the Runtime Surface `runtime_core` contract through a concern-specific builder boundary while preserving the public Runtime Profile contract.

#### Scenario: Runtime Core builder preserves default shell
- **WHEN** Runtime Surface assembles a profile without runtime scope
- **THEN** the `runtime_core` contract MUST keep its existing default fields and values
- **AND** the profile payload shape MUST remain unchanged for frontend and governance consumers

#### Scenario: Runtime Core builder preserves scoped overlay
- **WHEN** Runtime Surface assembles a profile with runtime scope
- **THEN** the builder MUST preserve `run_id`, `parent_run_id`, `child_run_id`, `child_display_id`, `scheduler_run_id`, `run_kind`, `status`, `trace_count`, and `latest_trace_event`
- **AND** `child_display_id` MUST continue to fall back to `child_run_id` when an explicit display id is absent

#### Scenario: Runtime Core builder preserves child merge evidence
- **WHEN** runtime scope includes child merge state or section evidence
- **THEN** the builder MUST preserve the existing child merge fields in `runtime_core`
- **AND** it MUST NOT reinterpret those fields as query lifecycle identifiers

#### Scenario: Service wrapper remains compatible
- **WHEN** existing backend callers invoke `RuntimeSurfaceService._build_runtime_core_contract()`
- **THEN** the method MUST continue to return the same contract shape
- **AND** it MUST delegate to the dedicated Runtime Core builder
