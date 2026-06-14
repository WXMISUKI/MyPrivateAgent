## ADDED Requirements

### Requirement: Service provider list supports onboarding UI correlation
The service provider consumption contract SHALL provide stable fields that allow a frontend onboarding surface to correlate live provider readiness with static onboarding guidance.

#### Scenario: UI correlates known provider entries
- **WHEN** the frontend reads `/api/service-providers`
- **THEN** each known provider entry may include `onboarding_id` and `onboarding_path`
- **AND** the UI can join the entry to onboarding guidance by `provider_id` without invoking provider workloads

#### Scenario: UI displays live readiness boundaries
- **WHEN** a service provider entry exposes readiness metadata
- **THEN** the entry includes overall status, configured flag, enabled flag, capability statuses, gates, warnings, and boundaries suitable for read-only display
- **AND** this status does not imply default runtime promotion or automatic orchestration
