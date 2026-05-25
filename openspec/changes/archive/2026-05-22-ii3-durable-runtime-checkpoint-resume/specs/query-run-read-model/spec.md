## MODIFIED Requirements

### Requirement: Query/run recovery read models MUST expose backend-owned recovery status
Runtime recovery read models MUST expose backend-owned recovery status and MUST NOT require consumers to inspect SDK private metadata.

#### Scenario: Run recovery includes checkpoint and cursor detail
- **WHEN** a consumer requests the run recovery read model
- **THEN** the response MUST include checkpoint status and resume cursor status when available
- **AND** the response MUST continue to expose `recoverable`, `recovery_reason`, and entrypoint-level recovery decisions

#### Scenario: Consumer reads unresolved recovery state
- **WHEN** checkpoint or cursor evidence is missing or malformed
- **THEN** the read model MUST report a machine-readable blocked or unknown state
- **AND** it MUST NOT infer recoverability from descriptor presence alone
