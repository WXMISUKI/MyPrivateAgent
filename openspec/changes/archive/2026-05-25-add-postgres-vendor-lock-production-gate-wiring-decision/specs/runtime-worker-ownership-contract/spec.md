## ADDED Requirements

### Requirement: Runtime worker ownership MUST expose PostgreSQL production gate wiring decision evidence

The worker ownership runtime contract MUST provide a read-only decision that records whether a PostgreSQL vendor lock semantics candidate is explicitly approved as future production gate input.

#### Scenario: Wiring decision defaults to blocked

- **WHEN** the wiring decision is built without semantics candidate evidence or approval metadata
- **THEN** it MUST report `overall_status = blocked`
- **AND** it MUST expose missing semantics binding, decision, approval, rollout, rollback, and fallback sections
- **AND** it MUST report `wiring_allowed = false`
- **AND** it MUST report `will_update_production_gate = false`
- **AND** it MUST report `will_enable_production_lock = false`

#### Scenario: Complete decision allows future wiring without side effects

- **WHEN** the wiring decision receives ready PostgreSQL semantics binding evidence and explicit approval metadata
- **THEN** it MAY report `overall_status = ready`
- **AND** it MAY report `wiring_allowed = true`
- **AND** it MUST still report `will_update_production_gate = false`
- **AND** it MUST still report `will_enable_production_lock = false`
- **AND** it MUST still report `executes_advisory_lock = false`

#### Scenario: SQL row lease is not promoted by wiring decision

- **WHEN** strict SQL row lease/fencing exists
- **THEN** the wiring decision MUST report `sql_row_lease_is_vendor_lock = false`
- **AND** it MUST NOT treat SQL row lease/fencing as production vendor lock authority
