# provider-onboarding-ui-surface Specification

## ADDED Requirements

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
