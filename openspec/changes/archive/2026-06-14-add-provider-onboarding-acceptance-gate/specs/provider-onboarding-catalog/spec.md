## ADDED Requirements

### Requirement: Onboarding catalog supports acceptance-gate consumption
Provider onboarding catalog responses SHALL provide stable identity, readiness, capability, and boundary fields for the provider onboarding acceptance gate.

#### Scenario: Acceptance gate reads onboarding detail
- **WHEN** the acceptance gate reads a known onboarding entry
- **THEN** the entry includes `onboarding_id`, `provider_id`, `kind`, `capability_ids`, `checks`, `management`, and `boundaries`
- **AND** these fields are sufficient to compare expected capability ownership against service-provider management status

#### Scenario: Acceptance gate reads onboarding readiness
- **WHEN** the acceptance gate reads onboarding readiness
- **THEN** readiness includes `configuration_status`, `checks`, `live_probe_hints`, `boundaries`, and `recommended_action`
- **AND** the readiness check remains side-effect-free and does not perform a live provider probe
