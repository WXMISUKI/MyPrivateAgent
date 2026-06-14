# provider-onboarding-acceptance-gate Specification

## Purpose
Defines the deterministic read-only acceptance gate for external provider onboarding. The gate proves whether a known external provider is ready for explicit managed-provider consumption by MyPrivateAgent without executing provider workloads or promoting runtime defaults.

## Requirements
### Requirement: Provider onboarding acceptance gate emits deterministic evidence
MyPrivateAgent SHALL provide a deterministic read-only acceptance gate for known external provider onboarding.

#### Scenario: Acceptance evidence is generated for a known onboarding entry
- **WHEN** an operator requests acceptance evidence for a known `onboarding_id`
- **THEN** the gate returns contract version, provider identity, onboarding readiness summary, service-provider summary when registered, expected capability ownership, boundary summary, decision, blockers, warnings, and recommended action
- **AND** the evidence is compact and machine-readable

#### Scenario: Provider id can resolve onboarding entry
- **WHEN** an operator requests acceptance evidence by known `provider_id`
- **THEN** the gate resolves the matching `onboarding_id`
- **AND** it evaluates the same acceptance requirements as an onboarding-id request

### Requirement: Acceptance decision is conservative
The provider onboarding acceptance gate SHALL fail closed when required onboarding or live management evidence is missing.

#### Scenario: Provider is accepted for explicit managed use
- **WHEN** onboarding configuration is configured
- **AND** the service-provider management list includes the expected provider id
- **AND** live provider status is `ready` or `review`
- **AND** every expected capability id is owned by the live provider entry
- **THEN** the acceptance decision is `accepted`
- **AND** the decision scope is explicit managed-provider consumption only

#### Scenario: Provider is blocked when configuration is missing
- **WHEN** onboarding readiness reports `configuration_status` other than `configured`
- **THEN** the acceptance decision is `blocked`
- **AND** blockers identify the missing onboarding configuration checks

#### Scenario: Provider is blocked when live provider is missing
- **WHEN** the onboarding entry exists but the service-provider management list does not include the expected provider id
- **THEN** the acceptance decision is `blocked`
- **AND** recommended action asks the operator to configure or register the provider before explicit use

#### Scenario: Provider is blocked when capabilities do not match
- **WHEN** the live provider entry does not own every expected capability id from onboarding
- **THEN** the acceptance decision is `blocked`
- **AND** blockers identify the missing capability ids

### Requirement: Acceptance gate is side-effect-free
The provider onboarding acceptance gate MUST NOT execute provider workloads or mutate runtime state.

#### Scenario: Acceptance uses read-only sources
- **WHEN** acceptance evidence is generated
- **THEN** the gate reads only provider onboarding catalog/readiness and service-provider management read models
- **AND** it does not call provider capability invoke endpoints, capability test endpoints, chat endpoints, source binding endpoints, configuration write endpoints, or external provider startup commands

#### Scenario: Evidence excludes unsafe payloads
- **WHEN** acceptance evidence is returned
- **THEN** it MUST NOT include API key values, retrieved documents, generated answers, provider raw payloads, executable callables, provider clients, active streams, or large raw provider responses

### Requirement: Acceptance does not promote runtime defaults
Provider onboarding acceptance SHALL distinguish explicit managed-provider readiness from production runtime promotion.

#### Scenario: Accepted provider keeps runtime promotion boundaries
- **WHEN** a provider acceptance decision is `accepted`
- **THEN** evidence still states that default chat grounding, GraphRAG execution, source binding automation, provider startup, memory/audit mutation, and final answer policy are not promoted by this gate
- **AND** any future promotion requires a separate promotion gate/change
