## MODIFIED Requirements

### Requirement: Runtime worker ownership MUST expose production operation readiness

The runtime MUST expose worker ownership production readiness as compact machine-readable evidence.

#### Scenario: Production gate exposes auto-claim policy evidence

- **WHEN** the runtime worker ownership production gate is inspected
- **THEN** the `recovery_entry_auto_claim_policy` section evidence MUST include policy status, missing policy sections, default enabled flag, descriptor-evidence fallback, gate readiness requirement, entrypoint allowlist, and audit requirement evidence
- **AND** the evidence MUST NOT imply recovery entry auto-claim has run or is enabled by default

#### Scenario: Production gate exposes rollout readiness evidence

- **WHEN** the runtime worker ownership production gate is inspected
- **THEN** the `rollout_checklist` section evidence MUST include rollout status, missing rollout sections, production rollout confirmation, strict-mode rollout, fallback policy, migration, stale fencing, and rollback plan evidence
- **AND** the evidence MUST NOT imply production ownership has been enabled

#### Scenario: Production gate exposes renewal supervisor evidence

- **WHEN** the runtime worker ownership production gate is inspected
- **THEN** the `heartbeat_renewal_supervisor` section evidence MUST include renewal supervisor status, missing sections, default enabled flag, and lease-loss fail-closed evidence
- **AND** the evidence MUST NOT imply a background renewal supervisor has started

#### Scenario: Production gate is consumed by durable recovery

- **WHEN** durable recovery production gating consumes `worker_ownership.production_gate`
- **THEN** the ownership gate MUST remain descriptive evidence only
- **AND** SQL row lease/fencing MUST NOT be treated as production recovery authorization
- **AND** production ownership enforcement MUST remain disabled unless the ownership gate is ready and explicitly enabled
