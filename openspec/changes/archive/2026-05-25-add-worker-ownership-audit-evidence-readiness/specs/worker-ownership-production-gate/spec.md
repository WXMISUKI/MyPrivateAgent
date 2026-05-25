## MODIFIED Requirements

### Requirement: Production ownership MUST keep audit evidence descriptive

Ownership audit evidence MUST remain a descriptive readiness signal and MUST NOT become a production execution authorization source.

#### Scenario: Audit evidence is missing

- **WHEN** no ownership audit evidence contract is present
- **THEN** the worker ownership production gate remains blocked
- **AND** the `ownership_audit_evidence` section evidence MUST identify missing audit evidence sections

#### Scenario: Audit evidence is present but incomplete

- **WHEN** audit evidence is compact but operation history, recovery operation link, timeline writer, or idempotent dedupe evidence is missing
- **THEN** the worker ownership production gate remains blocked
- **AND** the `ownership_audit_evidence` section remains not ready

#### Scenario: Audit evidence is treated as authorization

- **WHEN** an audit evidence contract reports `authorization_source = true`
- **THEN** the worker ownership production gate MUST remain blocked
- **AND** production ownership MUST NOT be default-enabled from audit evidence alone
