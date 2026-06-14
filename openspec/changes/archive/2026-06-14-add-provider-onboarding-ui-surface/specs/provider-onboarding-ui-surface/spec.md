## ADDED Requirements

### Requirement: Settings exposes provider onboarding status
MyPrivateAgent SHALL expose a read-only frontend surface for known external provider onboarding in the settings provider area.

#### Scenario: Provider onboarding catalog is visible
- **WHEN** an operator opens the settings provider area
- **THEN** the UI displays known onboarding entries from `/api/provider-onboarding`
- **AND** each visible entry includes provider id, kind, default base URL, capability ids, env var names, and documentation paths when provided

#### Scenario: Onboarding readiness checklist is visible
- **WHEN** onboarding readiness is available for an entry
- **THEN** the UI displays its configuration status, readiness checks, recommended action, and live probe paths
- **AND** the UI does not hide entries that are unconfigured or missing optional checks

### Requirement: Live provider readiness is correlated without execution
The provider onboarding UI SHALL correlate onboarding entries with live service-provider status while remaining side-effect-free.

#### Scenario: Live provider status is shown
- **WHEN** `/api/service-providers` returns a provider matching an onboarding entry provider id
- **THEN** the UI displays its overall status, configured flag, enabled flag, capability statuses, warnings, gates, onboarding path, and evidence preview path when provided

#### Scenario: Missing live provider remains actionable
- **WHEN** an onboarding entry has no matching live service provider
- **THEN** the UI keeps the onboarding entry visible
- **AND** it indicates that live provider status is not currently registered or reachable through the management list

### Requirement: Provider onboarding UI is read-only
The provider onboarding UI MUST NOT mutate runtime configuration or invoke provider workloads.

#### Scenario: Refresh is the only provider-facing action
- **WHEN** an operator uses the provider onboarding UI
- **THEN** the UI may call only read endpoints for onboarding catalog, onboarding readiness, and service-provider list
- **AND** it MUST NOT call provider capability invoke endpoints, capability test endpoints, chat endpoints, source binding endpoints, or configuration write endpoints

#### Scenario: Runtime promotion boundaries remain visible
- **WHEN** an entry or live provider exposes boundaries
- **THEN** the UI displays those boundaries as status metadata
- **AND** it does not imply default chat grounding, GraphRAG execution, source binding automation, provider startup, or final answer policy promotion
