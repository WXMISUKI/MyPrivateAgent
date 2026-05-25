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

#### Scenario: Rollout checklist is incomplete

- **WHEN** migration, stale fencing, recovery-entry auto-claim, or audit rollout checks are incomplete
- **THEN** the gate remains blocked
- **AND** missing checklist entries are machine-readable

### Requirement: Runtime worker ownership MUST expose production operation readiness

The runtime MUST expose worker ownership production readiness as compact machine-readable evidence.

#### Scenario: Production gate exposes renewal supervisor evidence

- **WHEN** the runtime worker ownership production gate is inspected
- **THEN** the `heartbeat_renewal_supervisor` section evidence MUST include renewal supervisor status, missing sections, default enabled flag, and lease-loss fail-closed evidence
- **AND** the evidence MUST NOT imply a background renewal supervisor has started

#### Scenario: Production gate is consumed by durable recovery

- **WHEN** durable recovery production gating consumes `worker_ownership.production_gate`
- **THEN** the ownership gate MUST remain descriptive evidence only
- **AND** SQL row lease/fencing MUST NOT be treated as production recovery authorization
- **AND** production ownership enforcement MUST remain disabled unless the ownership gate is ready and explicitly enabled
