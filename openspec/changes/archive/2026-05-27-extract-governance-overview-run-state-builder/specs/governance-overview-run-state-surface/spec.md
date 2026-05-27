## ADDED Requirements

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
