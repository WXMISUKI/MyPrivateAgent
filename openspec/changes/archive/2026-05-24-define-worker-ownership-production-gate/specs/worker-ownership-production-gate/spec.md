## ADDED Requirements

### Requirement: Worker ownership production gate MUST be machine-readable

The runtime MUST expose a production gate before worker ownership can become default execution authority for recovery, retry, or worker dispatch.

The gate MUST include:

- contract version
- overall status
- production default enabled flag
- readiness sections
- missing sections
- next allowed action
- non-goals

#### Scenario: Production gate is blocked

- **WHEN** vendor lock semantics, renewal supervision, rollout, migration, auto-claim policy, or audit evidence is missing
- **THEN** the gate reports `overall_status = blocked`
- **AND** worker ownership remains explicit or opt-in
- **AND** default production ownership enforcement remains disabled

#### Scenario: Production gate is ready

- **WHEN** all production readiness sections are complete
- **THEN** the gate may report `overall_status = ready`
- **AND** enabling default production ownership still requires explicit runtime configuration

### Requirement: Production ownership MUST distinguish SQL row lease from vendor lock

The production gate MUST NOT treat SQL row lease/fencing as a vendor-specific distributed lock unless vendor lock semantics are explicitly present.

#### Scenario: SQL row lease only

- **WHEN** the runtime uses SQLAlchemy row lease/fencing without vendor-specific lock semantics
- **THEN** the production gate remains blocked
- **AND** the gate identifies `vendor_lock_semantics` as a missing section

### Requirement: Production ownership MUST require renewal and rollout evidence

Default production worker ownership MUST require heartbeat renewal supervision and rollout readiness evidence.

#### Scenario: Renewal supervisor is missing

- **WHEN** no renewal supervisor contract is present
- **THEN** the gate remains blocked
- **AND** it MUST NOT allow default recovery ownership enforcement

#### Scenario: Rollout checklist is incomplete

- **WHEN** migration, stale fencing, recovery-entry auto-claim, or audit rollout checks are incomplete
- **THEN** the gate remains blocked
- **AND** missing checklist entries are machine-readable

### Requirement: Production ownership MUST keep recovery entry auto-claim explicit

Recovery entry auto-claim MUST remain disabled by default until the production gate is ready and an explicit runtime configuration enables it.

#### Scenario: Auto-claim is requested while gate is blocked

- **WHEN** recovery entry auto-claim would run under a blocked production gate
- **THEN** the runtime MUST fail closed or keep descriptor-evidence-only mode
- **AND** it MUST NOT silently claim ownership as a side effect
