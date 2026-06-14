# provider-service-consumption-contract Specification

## Purpose
Defines the provider-neutral external service consumption management contract for MyPrivateAgent. It standardizes provider listing, readiness normalization, explicit capability invocation, and compact evidence preview while preserving provider-owned execution and data lifecycle boundaries.

## Requirements
### Requirement: External providers are listed through a management contract
MyPrivateAgent SHALL expose a provider-neutral management contract for configured external service providers without requiring provider-owned dependencies in the core backend.

#### Scenario: Provider list reports configured providers
- **WHEN** a client reads the provider management list
- **THEN** each provider entry includes `provider_id`, `kind`, `transport`, `configured`, `enabled`, `overall_status`, and `capabilities`
- **AND** the entry does not include API key values, provider client objects, retrieved documents, generated answers, or large raw provider payloads

#### Scenario: Provider is not configured
- **WHEN** a provider integration is disabled or missing its required base URL
- **THEN** the provider management contract reports `overall_status = unconfigured` or `disabled`
- **AND** the main application and ordinary chat behavior remain healthy

### Requirement: Provider readiness is normalized for governance consumers
MyPrivateAgent SHALL normalize external provider readiness into a compact caller-owned status model.

#### Scenario: Provider is ready
- **WHEN** a configured provider is reachable and its required explicit capabilities are available
- **THEN** provider readiness reports `overall_status = ready`
- **AND** each ready capability includes `capability_id`, `status`, `transport`, and `invocation_boundary`

#### Scenario: Provider is unreachable
- **WHEN** a configured provider cannot be reached
- **THEN** provider readiness reports `overall_status = unreachable`
- **AND** the response includes a structured error code or reason
- **AND** `/api/chat` behavior remains unchanged

#### Scenario: Provider capability is gated
- **WHEN** a provider exposes a capability contract but execution is not promoted
- **THEN** provider readiness reports that capability as `gated`
- **AND** the gate includes a machine-readable reason

### Requirement: Provider details preserve promotion boundaries
The provider management contract MUST distinguish explicit provider usability from production runtime promotion.

#### Scenario: RAG provider is ready
- **WHEN** an external knowledge provider is ready for explicit RAG retrieval
- **THEN** provider details include boundaries showing default chat grounding remains gated
- **AND** GraphRAG execution remains gated unless a separate GraphRAG promotion gate proves readiness
- **AND** source binding automation remains outside the provider consumption contract

#### Scenario: Non-RAG provider is ready
- **WHEN** a voice, OCR, layout, VLM, or future external provider is ready
- **THEN** provider details still expose explicit invocation boundaries
- **AND** readiness does not imply default agent workflow promotion or automatic orchestration

### Requirement: Explicit provider invocation delegates to capability runtime
MyPrivateAgent SHALL provide an explicit provider capability invocation path that delegates execution to the existing capability runtime.

#### Scenario: Provider owns capability
- **WHEN** a client invokes a capability through the provider management API
- **AND** the provider entry owns the requested `capability_id`
- **THEN** MyPrivateAgent delegates to the existing capability runtime invocation path
- **AND** the response preserves the provider-neutral capability envelope

#### Scenario: Provider does not own capability
- **WHEN** a client invokes a capability that is not owned by the requested provider
- **THEN** the response fails closed with a structured error
- **AND** no provider call is made through the management API

#### Scenario: Invocation remains explicit
- **WHEN** a provider capability invocation succeeds
- **THEN** MyPrivateAgent does not enable default chat retrieval injection
- **AND** it does not create source-to-agent bindings, approvals, memory records, audit records, or final answer policy changes

### Requirement: Provider evidence package is previewable
MyPrivateAgent SHALL expose a compact provider evidence package preview for integration review and governance diagnostics.

#### Scenario: Evidence package is generated
- **WHEN** a client requests provider evidence preview
- **THEN** the package includes provider identity, readiness summary, capability statuses, gates, warnings, boundaries, and recommended next action
- **AND** the package is caller-owned and side-effect-free

#### Scenario: Evidence package excludes unsafe payloads
- **WHEN** evidence preview is generated
- **THEN** it MUST NOT include API key values, raw retrieved documents, generated answer text, executable callables, provider clients, active streams, or large raw provider payloads

#### Scenario: Evidence package preserves provider reopen gate
- **WHEN** an explicit RAG provider is ready
- **THEN** the package recommends caller-side trial or governed explicit use
- **AND** it does not recommend provider-side enhancement unless there is a real caller feedback trigger, provider-owned gap, repeated cross-source failure class, or runtime strategy evaluation trigger

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
