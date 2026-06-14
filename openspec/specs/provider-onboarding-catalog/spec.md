# provider-onboarding-catalog Specification

## Purpose
Defines the read-only onboarding catalog for known external provider projects. The catalog explains how external providers map into MyPrivateAgent capability runtime and service provider management without starting services, mutating configuration, or promoting runtime defaults.

## Requirements
### Requirement: Known external providers are exposed in an onboarding catalog
MyPrivateAgent SHALL expose a read-only provider onboarding catalog for known external provider families.

#### Scenario: Catalog lists known providers
- **WHEN** a client reads the provider onboarding catalog
- **THEN** the response includes entries for knowledge, voice, OCR, layout, and document VLM provider families
- **AND** each entry includes `onboarding_id`, `provider_id`, `kind`, `purpose`, `default_base_url`, `capability_ids`, `env`, `docs`, `checks`, and `boundaries`

#### Scenario: Catalog avoids secrets and raw payloads
- **WHEN** the provider onboarding catalog is returned
- **THEN** it MUST NOT include API key values, provider raw payloads, retrieved documents, generated answers, model weights, or executable clients

### Requirement: Onboarding entries define configuration and capability mapping
Each onboarding entry SHALL describe how an external provider maps into MyPrivateAgent capability runtime and service provider management.

#### Scenario: Knowledge provider entry maps RAG capability
- **WHEN** the knowledge provider onboarding entry is read
- **THEN** it includes `knowledge.rag.retrieve` and `knowledge.graph.query`
- **AND** it references `ENABLE_KNOWLEDGE_CAPABILITY_PROVIDER` and `KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL`
- **AND** it states that GraphRAG and default chat grounding remain gated

#### Scenario: Voice provider entry maps ASR and TTS capabilities
- **WHEN** the voice provider onboarding entry is read
- **THEN** it includes `voice.tts.edge` and `voice.asr.vosk`
- **AND** it references `ENABLE_EXTERNAL_VOICE_CAPABILITY_PROVIDER` and `VOICE_CAPABILITY_PROVIDER_BASE_URL`

#### Scenario: Document provider entries map OCR layout and VLM capabilities
- **WHEN** document provider onboarding entries are read
- **THEN** OCR includes `document.ocr.extract`
- **AND** layout includes `document.layout.parse`
- **AND** VLM includes `document.vlm.parse` and `document.vlm.parse.async`

### Requirement: Onboarding readiness checklist is side-effect-free
The onboarding catalog SHALL expose a compact readiness checklist without starting providers or mutating runtime configuration.

#### Scenario: Checklist reports configuration posture
- **WHEN** a provider entry is read
- **THEN** its checks identify required environment toggles and base URL variables
- **AND** the checks report whether current process configuration appears configured
- **AND** live runtime verification is marked as a separate probe through `/api/service-providers` or `/api/capabilities/heartbeat`

#### Scenario: Checklist remains read-only
- **WHEN** onboarding catalog APIs are called
- **THEN** MyPrivateAgent does not start external services
- **AND** it does not write `.env`, create source bindings, submit OCR/VLM jobs, execute RAG, write audit records, or change default chat behavior

### Requirement: Onboarding API exposes list detail and readiness views
MyPrivateAgent SHALL expose read-only API endpoints for provider onboarding list, detail, and readiness checklist views.

#### Scenario: List endpoint returns compact entries
- **WHEN** a client requests the onboarding list endpoint
- **THEN** the response includes `contract_version`
- **AND** it includes compact entries suitable for UI cards and governance diagnostics

#### Scenario: Detail endpoint returns one provider entry
- **WHEN** a client requests an onboarding entry by id
- **THEN** the response returns the matching entry
- **AND** unknown ids return a structured not-found error

#### Scenario: Readiness endpoint returns checks
- **WHEN** a client requests onboarding readiness for one provider
- **THEN** the response returns the provider identity, configuration checks, live probe hints, boundaries, and recommended next action

### Requirement: Onboarding catalog cross-references service provider management
Provider onboarding entries SHALL identify how to inspect live runtime state through the existing service provider management contract.

#### Scenario: Entry has live management links
- **WHEN** an onboarding entry has a known `provider_id`
- **THEN** it includes a service provider detail path under `/api/service-providers/{provider_id}`
- **AND** it includes an evidence preview path under `/api/service-providers/{provider_id}/evidence-preview`

#### Scenario: Service provider not currently configured
- **WHEN** an onboarding entry is not currently registered in capability runtime
- **THEN** the onboarding entry remains visible
- **AND** its readiness checklist recommends configuring the required env variables before live probing
