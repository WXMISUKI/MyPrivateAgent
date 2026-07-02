# provider-onboarding-ui-surface Specification

## Purpose
Defines the read-only frontend surface that lets operators inspect known external provider onboarding guidance together with live provider management readiness.
## Requirements
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

### Requirement: Settings view MAY present provider ops posture beside existing provider diagnostics
The Settings view SHALL be able to expose the read-only provider ops control plane beside provider configuration, onboarding, and failover observability.

#### Scenario: Provider ops card renders in Settings
- **WHEN** a user opens the model/provider Settings tab
- **THEN** the UI MAY render a Provider Ops card backed by `/api/provider-ops`
- **AND** the card shows compact provider posture and summary data
- **AND** it remains a diagnostic-only read surface

#### Scenario: Provider ops load fails closed
- **WHEN** `/api/provider-ops` is unavailable or returns an error
- **THEN** the UI shows a degraded or empty diagnostic state
- **AND** it does not hide the provider area silently
- **AND** it does not block provider configuration, onboarding, diagnostics, or failover surfaces

#### Scenario: Provider ops does not expose mutations
- **WHEN** a user inspects provider ops posture
- **THEN** the UI does not offer configuration writes, runtime promotion, routing changes, or capability execution actions through the provider ops card

