# runtime-worker-ownership-contract Delta

## ADDED Requirements

### Requirement: Runtime MUST expose recovery auto-claim entrypoint allowlist evidence

The worker ownership runtime contract MUST expose a read-only allowlist contract for recovery-entry auto-claim entrypoints without enabling auto-claim by default.

#### Scenario: Auto-claim allowlist defaults to named entrypoints

- **WHEN** the worker ownership auto-claim entrypoint allowlist contract is built with defaults
- **THEN** it MUST report `overall_status = "ready"`
- **AND** it MUST include `submit_approval.approved` in `allowed_entrypoints`
- **AND** it MUST include `resume_run.continue_loop` in `allowed_entrypoints`
- **AND** it MUST report `default_auto_claim_enabled = false`
- **AND** it MUST report `requires_production_gate_ready = true`

#### Scenario: Auto-claim policy embeds allowlist evidence without enabling auto-claim

- **WHEN** the worker ownership auto-claim policy contract is built
- **THEN** it MUST include the nested entrypoint allowlist contract in `policy.entrypoint_allowlist`
- **AND** it MUST set `policy.entrypoint_allowlist_ready = true` when the nested allowlist is ready
- **AND** it MUST keep `auto_claim_enabled_by_default = false` unless the full policy is ready and explicitly enabled
- **AND** it MUST NOT call `claim_run`
