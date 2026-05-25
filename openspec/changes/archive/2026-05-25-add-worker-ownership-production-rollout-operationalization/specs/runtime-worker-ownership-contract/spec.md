## MODIFIED Requirements

### Requirement: Runtime worker ownership MUST expose production operation readiness

The runtime MUST expose worker ownership production readiness as compact machine-readable evidence.

#### Scenario: Production gate exposes rollout operationalization evidence

- **WHEN** the runtime worker ownership production gate is inspected
- **THEN** the `rollout_checklist` section evidence MUST include rollout operationalization status, rollout mode, missing artifacts, rollback plan status, fallback policy status, renewal lifecycle verification status, and auto-claim decision status
- **AND** that evidence MUST NOT imply production rollout has been confirmed
- **AND** it MUST NOT enable production default worker ownership
