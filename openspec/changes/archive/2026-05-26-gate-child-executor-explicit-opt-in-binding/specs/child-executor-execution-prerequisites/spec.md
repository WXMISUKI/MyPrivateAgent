## ADDED Requirements

### Requirement: Explicit Executor Binding Opt-In Must Be Required

The system MUST require explicit executor binding opt-in before a delegated child run can be considered ready for real executor handoff.

The explicit binding readiness evidence MUST include:

- binding status
- binding source
- selected backend id
- adapter kind
- readiness boolean
- missing requirements
- non-goals

#### Scenario: Explicit binding is missing

- **WHEN** child executor preflight has context budget, merge semantics, and worker backend evidence but no explicit executor binding opt-in
- **THEN** `child_executor_execution_prerequisites` MUST include `explicit_executor_binding_opt_in` in `missing_requirements`
- **AND** readiness MUST remain false
- **AND** the relationship seam MUST remain preserved

#### Scenario: Explicit binding is present

- **WHEN** child executor preflight includes explicit executor binding opt-in and the remaining prerequisites are ready
- **THEN** the explicit binding requirement MUST report ready
- **AND** the evidence MUST identify the opt-in source and selected backend

#### Scenario: Record-only binding is not execution authorization

- **WHEN** `delegate_binding.binding_status = bound` exists without explicit executor binding opt-in
- **THEN** the system MUST NOT treat that binding as real executor authorization
- **AND** execution and dispatch readiness MUST remain fail-closed.
