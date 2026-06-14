## ADDED Requirements

### Requirement: Service provider management supports acceptance-gate consumption
The provider service consumption contract SHALL expose enough compact live status for the provider onboarding acceptance gate to evaluate explicit managed-provider readiness.

#### Scenario: Acceptance gate reads live provider status
- **WHEN** the acceptance gate reads `/api/service-providers` through the service contract
- **THEN** each provider entry includes `provider_id`, `overall_status`, `configured`, `enabled`, `capabilities`, `gates`, `warnings`, and `boundaries`
- **AND** known providers may include `onboarding_id` and `onboarding_path`

#### Scenario: Acceptance gate preserves explicit invocation boundary
- **WHEN** a provider is accepted by the acceptance gate
- **THEN** service-provider readiness still represents explicit capability consumption only
- **AND** it does not imply default chat grounding, GraphRAG execution, source binding automation, or final answer policy promotion
