# runtime-worker-ownership-contract Delta

## ADDED Requirements

### Requirement: Runtime MUST expose explicit auto-claim enablement gate evidence

The worker ownership runtime contract MUST expose a read-only explicit enablement gate for recovery-entry auto-claim and MUST keep auto-claim disabled unless the gate is ready.

#### Scenario: Explicit auto-claim enablement gate defaults to blocked

- **WHEN** the explicit auto-claim enablement gate contract is built with defaults
- **THEN** it MUST report `overall_status = "blocked"`
- **AND** it MUST report `will_auto_claim = false`
- **AND** it MUST include `explicit_runtime_configuration` in `missing_sections`
- **AND** it MUST include `production_gate_ready` in `missing_sections`
- **AND** it MUST NOT call `claim_run`

#### Scenario: Non-allowlisted entrypoint fails closed

- **WHEN** an explicit auto-claim enablement gate is built for an entrypoint outside the allowlist
- **THEN** it MUST report `overall_status = "blocked"`
- **AND** it MUST report `blocked_reason = "entrypoint_not_allowlisted"`
- **AND** it MUST report `will_auto_claim = false`

#### Scenario: Ready prerequisites allow explicit auto-claim decision

- **WHEN** explicit configuration, production gate readiness, durable ownership, idempotency evidence, audit evidence, lease validation, rollout decision, and allowlisted entrypoint evidence are all present
- **THEN** the gate MAY report `overall_status = "ready"`
- **AND** it MAY report `will_auto_claim = true`
- **AND** it still MUST NOT call `claim_run`
