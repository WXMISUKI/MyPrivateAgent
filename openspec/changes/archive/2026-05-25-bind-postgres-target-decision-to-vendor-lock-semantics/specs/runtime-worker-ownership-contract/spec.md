## ADDED Requirements

### Requirement: Runtime worker ownership MUST expose PostgreSQL vendor lock semantics binding evidence

The worker ownership runtime contract MUST provide a read-only binding that maps PostgreSQL target artifact binding evidence into a vendor lock semantics candidate.

#### Scenario: Semantics binding defaults to blocked

- **WHEN** the PostgreSQL vendor lock semantics binding is built without target artifact binding and execution seam evidence
- **THEN** it MUST report `overall_status = blocked`
- **AND** it MUST expose missing target binding, execution seam, probe, adapter, and semantics sections
- **AND** it MUST report `will_enable_production_lock = false`
- **AND** it MUST report `will_update_production_gate = false`
- **AND** it MUST report `executes_advisory_lock = false`

#### Scenario: Complete target binding produces semantics candidate

- **WHEN** the binding receives ready PostgreSQL target artifact binding evidence and ready opt-in execution seam evidence
- **THEN** it MAY report `overall_status = ready`
- **AND** it MUST include ready nested PostgreSQL probe evidence
- **AND** it MUST include ready nested vendor lock adapter evidence
- **AND** it MUST include ready nested vendor lock semantics candidate evidence
- **AND** it MUST still report `will_enable_production_lock = false`
- **AND** it MUST still report `will_update_production_gate = false`
- **AND** it MUST still report `executes_advisory_lock = false`

#### Scenario: SQL row lease is not promoted by semantics binding

- **WHEN** strict SQL row lease/fencing exists
- **THEN** the binding MUST report `sql_row_lease_is_vendor_lock = false`
- **AND** it MUST NOT treat SQL row lease/fencing as PostgreSQL advisory lock authority
