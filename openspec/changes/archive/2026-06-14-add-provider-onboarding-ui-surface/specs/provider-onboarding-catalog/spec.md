## ADDED Requirements

### Requirement: Onboarding catalog supports frontend read-only consumption
Provider onboarding catalog responses SHALL include stable fields suitable for a frontend read-only onboarding surface.

#### Scenario: UI consumes onboarding list fields
- **WHEN** the frontend reads `/api/provider-onboarding`
- **THEN** each entry includes enough compact fields to display provider identity, setup env names, default base URL, capabilities, checks, management paths, docs, and boundaries
- **AND** the response remains free of secrets, raw provider payloads, retrieved documents, generated answers, and executable clients

#### Scenario: UI consumes onboarding readiness fields
- **WHEN** the frontend reads `/api/provider-onboarding/{onboarding_id}/readiness`
- **THEN** the response includes configuration status, checks, live probe hints, boundaries, and recommended action
- **AND** the readiness response remains side-effect-free and does not perform a live provider probe
