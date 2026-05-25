## ADDED Requirements

### Requirement: Runtime worker ownership MUST expose PostgreSQL target artifact binding evidence

The worker ownership runtime contract MUST provide a read-only binding that maps PostgreSQL rollout artifact/config evidence to vendor lock target decision evidence.

#### Scenario: Target artifact binding defaults to blocked

- **WHEN** the PostgreSQL target artifact binding is built without artifact/config evidence
- **THEN** it MUST report `overall_status = blocked`
- **AND** it MUST expose missing source, artifact, approval, backend, adapter, target decision, rollout consumer, and source reference sections
- **AND** it MUST report `will_enable_production_lock = false`
- **AND** it MUST report `executes_advisory_lock = false`

#### Scenario: Complete artifact produces nested target decision evidence

- **WHEN** the binding receives a complete PostgreSQL rollout artifact and ready rollout consumer evidence
- **THEN** it MAY report `overall_status = ready`
- **AND** it MUST include nested ready `target_decision_input`
- **AND** it MUST include nested ready `target_decision`
- **AND** it MUST still report `will_enable_production_lock = false`
- **AND** it MUST still report `executes_advisory_lock = false`

#### Scenario: SQL row lease is never promoted by binding

- **WHEN** strict SQL row lease/fencing is present
- **THEN** the binding MUST report `sql_row_lease_is_vendor_lock = false`
- **AND** it MUST NOT use SQL row lease/fencing as PostgreSQL advisory lock authority
