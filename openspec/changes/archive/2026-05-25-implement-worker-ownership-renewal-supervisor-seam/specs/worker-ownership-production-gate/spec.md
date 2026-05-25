## MODIFIED Requirements

### Requirement: Production ownership MUST require renewal and rollout evidence

Default production worker ownership MUST require heartbeat renewal supervision and rollout readiness evidence.

#### Scenario: Renewal supervisor is missing

- **WHEN** no renewal supervisor contract is present
- **THEN** the gate remains blocked
- **AND** it MUST NOT allow default recovery ownership enforcement
- **AND** the `heartbeat_renewal_supervisor` section evidence MUST identify missing renewal supervisor readiness sections

#### Scenario: Renewal supervisor contract is present but not production-enabled

- **WHEN** the renewal supervisor contract is present but reports `supervisor_enabled_by_default = false`
- **THEN** the worker ownership production gate remains blocked
- **AND** the `heartbeat_renewal_supervisor` section remains not ready
- **AND** production default ownership enforcement remains disabled

#### Scenario: Renewal supervisor seam exists without background supervision

- **WHEN** the renewal supervisor contract reports `renew_once_supported = true`
- **AND** no background supervisor is present or enabled by default
- **THEN** the `heartbeat_renewal_supervisor` section remains blocked
- **AND** the evidence MUST expose that explicit one-shot renewal does not imply production background supervision

#### Scenario: Rollout checklist is incomplete

- **WHEN** migration, stale fencing, recovery-entry auto-claim, audit rollout checks, fallback policy, strict-mode rollout confirmation, or rollback planning are incomplete
- **THEN** the gate remains blocked
- **AND** missing checklist entries are machine-readable
- **AND** the `rollout_checklist` section evidence MUST identify missing rollout readiness sections

#### Scenario: Rollout contract is present but not production-confirmed

- **WHEN** the rollout readiness contract is present but reports `production_rollout_confirmed = false`
- **THEN** the worker ownership production gate remains blocked
- **AND** the `rollout_checklist` section remains not ready
- **AND** production default ownership enforcement remains disabled
