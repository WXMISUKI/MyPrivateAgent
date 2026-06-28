# provider-ops-control-plane Specification

## Purpose

Define a read-only provider operations control plane for MyPrivateAgent. This contract makes credential, quota, cost, SLA, rate-limit, and fallback posture visible to governance consumers without changing provider execution behavior.

## ADDED Requirements

### Requirement: Provider ops posture MUST be exposed as a compact read model
The system SHALL expose a compact provider ops read model for configured external providers.

#### Scenario: Provider ops summary is available
- **WHEN** a caller reads the provider ops contract
- **THEN** each provider entry includes `provider_id`, `credential_posture`, `quota_posture`, `rate_limit_posture`, `cost_posture`, `sla_posture`, and `fallback_posture`
- **AND** the response includes a compact overall status for the provider

#### Scenario: Unconfigured provider remains visible but degraded
- **WHEN** a known provider is missing credentials or configuration
- **THEN** the provider ops contract reports a degraded or unknown posture
- **AND** it includes a machine-readable reason code or next action

### Requirement: Provider ops contract MUST remain read-only
The provider ops contract SHALL not mutate provider configuration, routing, or runtime promotion state.

#### Scenario: Provider ops is inspected
- **WHEN** a caller requests provider ops evidence
- **THEN** the system MUST only read existing provider and governance metadata
- **AND** it MUST NOT write API keys, rotate credentials, alter routing, start providers, or change `/api/chat`

### Requirement: Secrets and raw payloads MUST be excluded
The provider ops contract SHALL not expose secrets, raw provider payloads, or executable provider objects.

#### Scenario: Sensitive values are absent
- **WHEN** provider ops evidence is returned
- **THEN** it MUST NOT include API keys, tokens, raw provider clients, active streams, or large provider payloads

### Requirement: Provider ops posture MUST fail closed when evidence is missing
The provider ops contract SHALL use bounded degraded states when operational evidence is incomplete.

#### Scenario: Quota posture is unknown
- **WHEN** quota information is unavailable
- **THEN** the quota posture is `unknown` or `review`
- **AND** the contract includes a compact blocker or next action

#### Scenario: SLA posture is degraded
- **WHEN** the provider is below its operational SLA expectation
- **THEN** the SLA posture is `degraded` or equivalent bounded state
- **AND** the contract does not promote the provider to healthy readiness

### Requirement: Provider ops contract MUST be consumable by Runtime Surface
The system SHALL make the provider ops read model available to Runtime Surface or a dedicated read endpoint.

#### Scenario: Runtime Surface reads provider ops
- **WHEN** Runtime Surface assembles the runtime profile
- **THEN** it MAY include a compact provider ops summary
- **AND** the summary must remain stable for governance consumers

#### Scenario: Dedicated provider ops endpoint exists
- **WHEN** a caller needs provider operational posture without the full runtime profile
- **THEN** the system SHALL allow a dedicated read endpoint to serve the same contract
- **AND** the endpoint must remain read-only

### Requirement: Provider ops posture MUST distinguish operational safety from promotion
The system SHALL distinguish provider operational safety from runtime promotion or default chat behavior.

#### Scenario: Provider is operationally healthy
- **WHEN** the provider ops contract reports healthy posture
- **THEN** that does not imply default chat grounding, automatic orchestration, or provider market promotion

#### Scenario: Fallback posture is active
- **WHEN** a provider is operating under fallback posture
- **THEN** the contract must make the fallback posture visible
- **AND** it must not silently promote the provider as the primary execution path
