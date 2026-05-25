## MODIFIED Requirements

### Requirement: Production ownership MUST keep recovery entry auto-claim explicit

Recovery entry auto-claim MUST remain disabled by default until the production gate is ready and an explicit runtime configuration enables it.

#### Scenario: Auto-claim policy is missing

- **WHEN** no recovery-entry auto-claim policy contract is present
- **THEN** the worker ownership production gate remains blocked
- **AND** the `recovery_entry_auto_claim_policy` section evidence MUST identify missing auto-claim policy sections
- **AND** default recovery entry auto-claim remains disabled

#### Scenario: Auto-claim policy is present but not default-enabled

- **WHEN** the auto-claim policy contract is present but reports `auto_claim_enabled_by_default = false`
- **THEN** the worker ownership production gate remains blocked
- **AND** the `recovery_entry_auto_claim_policy` section remains not ready
- **AND** default recovery entry auto-claim remains disabled

#### Scenario: Auto-claim is requested while gate is blocked

- **WHEN** recovery entry auto-claim would run under a blocked production gate
- **THEN** the runtime MUST fail closed or keep descriptor-evidence-only mode
- **AND** it MUST NOT silently claim ownership as a side effect
