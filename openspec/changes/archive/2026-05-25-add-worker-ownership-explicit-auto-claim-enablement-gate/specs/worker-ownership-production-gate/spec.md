# worker-ownership-production-gate Delta

## ADDED Requirements

### Requirement: Production gate MUST expose explicit auto-claim enablement blocker

The worker ownership production gate MUST explain why recovery-entry auto-claim remains blocked even when the entrypoint allowlist is ready.

#### Scenario: Auto-claim policy evidence includes explicit enablement gate

- **WHEN** the worker ownership production gate is built
- **THEN** the `recovery_entry_auto_claim_policy` section evidence MUST include `auto_claim_enablement_gate_contract_version`
- **AND** it MUST include `auto_claim_enablement_gate_status`
- **AND** it MUST include `auto_claim_will_auto_claim`
- **AND** it MUST include `auto_claim_enablement_missing_sections`
- **AND** it MUST include `auto_claim_enablement_blocked_reason`
- **AND** the section MUST remain blocked when the enablement gate is blocked
