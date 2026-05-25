## MODIFIED Requirements

### Requirement: Runtime worker ownership MUST expose production operation readiness

The runtime MUST expose worker ownership production readiness as compact machine-readable evidence.

#### Scenario: Production gate exposes ownership audit evidence

- **WHEN** the runtime worker ownership production gate is inspected
- **THEN** the `ownership_audit_evidence` section evidence MUST include audit evidence status, missing audit sections, compact ownership evidence, operation history readiness, recovery operation link readiness, timeline writer readiness, idempotent dedupe readiness, and authorization-source posture
- **AND** the evidence MUST NOT imply audit evidence authorizes ownership or recovery execution

#### Scenario: Production gate remains blocked when audit evidence is not ready

- **WHEN** ownership audit evidence is compact but operation history, recovery operation link, timeline writer, or idempotent dedupe evidence is missing
- **THEN** the worker ownership production gate remains blocked
- **AND** `ownership_audit_evidence` remains listed in `missing_sections`
