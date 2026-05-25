## ADDED Requirements

### Requirement: Production ownership gate MUST expose vendor lock target decision input source blockers

The worker ownership production gate MUST expose vendor lock target decision input source evidence inside the `vendor_lock_semantics` section.

#### Scenario: Target decision input source is missing

- **WHEN** the production ownership gate is inspected without target decision input source evidence
- **THEN** the `vendor_lock_semantics` section MUST remain blocked
- **AND** its evidence MUST include `vendor_lock_target_input_source_status = blocked`
- **AND** its evidence MUST include input source missing sections
- **AND** its evidence MUST include `vendor_lock_target_input_sql_row_lease_is_vendor_lock = false`

#### Scenario: Input source does not bypass production enablement

- **WHEN** a target decision input source is ready
- **THEN** production default ownership MUST still require vendor lock semantics, rollout, renewal supervisor, auto-claim policy, audit evidence, and explicit production default enablement
