## MODIFIED Requirements

### Requirement: Runtime worker ownership MUST expose production operation readiness

The runtime MUST expose worker ownership production readiness as compact machine-readable evidence.

#### Scenario: Production gate exposes vendor lock semantics evidence

- **WHEN** the runtime worker ownership production gate is inspected
- **THEN** the `vendor_lock_semantics` section evidence MUST include vendor lock status, current posture, SQL-row-lease posture, missing lock semantics sections, production lock allowment, lock adapter, lock scope, fencing guarantee, failover semantics, TTL/renewal semantics, and stale owner cleanup evidence
- **AND** SQL row lease/fencing MUST NOT be treated as vendor lock semantics

#### Scenario: Production gate remains blocked when vendor lock semantics are absent

- **WHEN** the worker ownership adapter is durable SQL but no vendor-specific lock semantics are present
- **THEN** the worker ownership production gate remains blocked
- **AND** `vendor_lock_semantics` remains listed in `missing_sections`
