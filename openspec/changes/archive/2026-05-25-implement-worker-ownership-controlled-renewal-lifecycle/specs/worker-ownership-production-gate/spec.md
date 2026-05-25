## MODIFIED Requirements

### Requirement: Production ownership MUST require renewal and rollout evidence

Default production worker ownership MUST require heartbeat renewal supervision and rollout readiness evidence.

#### Scenario: Renewal supervisor contract is present but not production-enabled

- **WHEN** the renewal supervisor contract is present but reports `supervisor_enabled_by_default = false`
- **THEN** the worker ownership production gate remains blocked
- **AND** the `heartbeat_renewal_supervisor` section remains not ready
- **AND** production default ownership enforcement remains disabled

#### Scenario: Controlled lifecycle exists without default start

- **WHEN** the renewal supervisor contract reports `controlled_lifecycle_supported = true`
- **AND** `starts_by_default = false`
- **THEN** the `heartbeat_renewal_supervisor` section remains blocked
- **AND** the evidence MUST NOT imply production background renewal is enabled
