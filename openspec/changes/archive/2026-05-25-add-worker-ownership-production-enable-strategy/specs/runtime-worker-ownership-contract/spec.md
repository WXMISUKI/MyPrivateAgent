## MODIFIED Requirements

### Requirement: Runtime worker ownership MUST expose production operation readiness

The runtime MUST expose worker ownership production readiness as compact machine-readable evidence.

#### Scenario: Production gate exposes default enablement strategy evidence

- **WHEN** the runtime worker ownership production gate is inspected
- **THEN** the `fail_closed_default_decision` section evidence MUST include strategy status, required sections, blocking sections, explicit enablement request state, production default allowment, and fail-closed policy evidence
- **AND** the evidence MUST NOT imply production ownership has been default-enabled
