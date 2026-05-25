## ADDED Requirements

### Requirement: Worker ownership operations MUST expose a production gate

Operational readiness MUST include a production gate that distinguishes preview, durable SQL lease/fencing, and production-default ownership readiness.

#### Scenario: Memory or fallback posture

- **WHEN** worker ownership uses memory-only or fallback posture
- **THEN** the production gate reports `overall_status = blocked`
- **AND** production default ownership enforcement remains disabled

#### Scenario: Strict SQL posture without vendor lock

- **WHEN** strict SQL ownership is configured and migrations are ready
- **THEN** operational readiness may report durable row lease/fencing
- **AND** the production gate remains blocked unless vendor lock semantics, renewal supervision, rollout, auto-claim policy, and audit evidence are complete

### Requirement: Runtime smoke MUST cover production gate posture

The runtime contract smoke check MUST expose worker ownership production gate evidence.

#### Scenario: Smoke validates production gate blocked boundary

- **WHEN** `runtime_contract_smoke.py` emits the `worker_ownership_store_mode` check
- **THEN** it MUST include production gate contract version, status, missing sections, and default-enabled flag
- **AND** the check MUST prove production default ownership enforcement is disabled when the gate is blocked
