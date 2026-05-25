# worker-ownership-production-gate Delta

## ADDED Requirements

### Requirement: Production gate MUST explain auto-claim entrypoint allowlist posture

The worker ownership production gate MUST expose machine-readable recovery-entry auto-claim allowlist evidence while keeping the recovery entry auto-claim section blocked by default.

#### Scenario: Production gate exposes allowlist blocker context

- **WHEN** the worker ownership production gate is built
- **THEN** the `recovery_entry_auto_claim_policy` section evidence MUST include `auto_claim_entrypoint_allowlist_contract_version`
- **AND** it MUST include `auto_claim_entrypoint_allowlist_status`
- **AND** it MUST include `auto_claim_allowed_entrypoints`
- **AND** it MUST include `auto_claim_missing_entrypoints`
- **AND** it MUST include `auto_claim_default_auto_claim_enabled`
- **AND** it MUST include `auto_claim_requires_production_gate_ready`
- **AND** the section MUST remain blocked when auto-claim is not enabled by default
