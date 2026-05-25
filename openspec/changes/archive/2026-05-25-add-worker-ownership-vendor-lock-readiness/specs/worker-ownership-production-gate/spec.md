## MODIFIED Requirements

### Requirement: Production ownership MUST distinguish SQL row lease from vendor lock

The production gate MUST NOT treat SQL row lease/fencing as a vendor-specific distributed lock unless vendor lock semantics are explicitly present.

#### Scenario: SQL row lease only

- **WHEN** the runtime uses SQLAlchemy row lease/fencing without vendor-specific lock semantics
- **THEN** the production gate remains blocked
- **AND** the gate identifies `vendor_lock_semantics` as a missing section
- **AND** the `vendor_lock_semantics` section evidence MUST identify missing lock adapter, lock scope, fencing guarantee, failover semantics, TTL/renewal semantics, stale owner cleanup, and production allowment sections

#### Scenario: Vendor lock contract is present but not production-allowed

- **WHEN** the vendor lock semantics contract is ready but reports `production_lock_allowed = false`
- **THEN** the worker ownership production gate remains blocked
- **AND** production default ownership enforcement remains disabled
