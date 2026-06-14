## ADDED Requirements

### Requirement: Service provider entries may reference onboarding guidance
The provider service consumption contract SHALL allow live provider entries to cross-reference static onboarding catalog guidance when a known provider family exists.

#### Scenario: Known provider has onboarding reference
- **WHEN** a service provider entry corresponds to a known onboarding catalog provider id
- **THEN** the entry includes `onboarding_id`
- **AND** it includes an onboarding detail path under `/api/provider-onboarding/{onboarding_id}`

#### Scenario: Unknown provider remains valid
- **WHEN** a service provider entry has no known onboarding catalog entry
- **THEN** the provider management contract remains valid
- **AND** the provider entry does not require an onboarding reference
