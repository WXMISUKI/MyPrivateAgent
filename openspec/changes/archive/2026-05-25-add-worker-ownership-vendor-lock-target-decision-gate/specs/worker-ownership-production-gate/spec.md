## ADDED Requirements

### Requirement: Production ownership gate MUST expose vendor lock target decision blockers

The worker ownership production gate MUST expose vendor lock target decision evidence inside the `vendor_lock_semantics` section so operators can distinguish an undecided lock target from a missing implementation.

#### Scenario: Vendor lock target decision is missing

- **WHEN** the production ownership gate is inspected without a vendor lock target decision
- **THEN** the `vendor_lock_semantics` section MUST remain blocked
- **AND** its evidence MUST include `vendor_lock_target_decision_status = blocked`
- **AND** its evidence MUST include missing target decision sections
- **AND** its evidence MUST include `vendor_lock_target_sql_row_lease_is_vendor_lock = false`
- **AND** its evidence MUST include `vendor_lock_target_production_allowed = false`

#### Scenario: SQL row lease remains separate from vendor lock target decision

- **WHEN** strict SQL row lease/fencing is available
- **THEN** the production ownership gate MUST still report SQL row lease as not being a vendor lock target
- **AND** default production ownership MUST remain disabled unless all production gate sections are ready and explicit default enablement is requested
