# worker-ownership-production-gate Delta

## ADDED Requirements

### Requirement: Production gate MUST expose rollout confirmation decision evidence

The worker ownership production gate MUST expose compact rollout confirmation decision evidence through the `rollout_checklist` section.

#### Scenario: Rollout checklist carries decision blocker

- **WHEN** the worker ownership production gate is built
- **THEN** the `rollout_checklist` section evidence MUST include `rollout_confirmation_decision_contract_version`
- **AND** it MUST include `rollout_confirmation_decision_status`
- **AND** it MUST include `rollout_decision_recorded`
- **AND** it MUST include `rollout_target_store_mode`
- **AND** it MUST include `rollout_confirmation_missing_sections`
- **AND** the section MUST remain blocked when the decision record is blocked

#### Scenario: Decision record does not bypass vendor lock or production enablement

- **WHEN** the rollout confirmation decision record is ready
- **THEN** the worker ownership production gate MUST still require vendor lock semantics, renewal supervisor readiness, auto-claim policy readiness, audit evidence, and explicit production default enablement
- **AND** strict SQL row lease/fencing MUST NOT be treated as vendor-specific distributed lock semantics
