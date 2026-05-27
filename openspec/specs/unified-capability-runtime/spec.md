# unified-capability-runtime Specification

## Purpose
Defines the provider-neutral capability runtime registry for AI capabilities such as ASR, TTS, OCR, multimodal inference, and video generation. The registry lets MyPrivateAgent discover, health-check, and invoke local or external providers without binding frontend or agent code to provider-specific runtime environments.
## Requirements
### Requirement: Capability Registry Contract
The backend SHALL expose a provider-neutral capability registry for AI capabilities.

#### Scenario: Registry lists voice capabilities
- **WHEN** a client requests `GET /api/capabilities`
- **THEN** the response includes `contract_version`
- **AND** includes registered capabilities for `voice.tts.edge` and `voice.asr.vosk`
- **AND** each capability includes `capability_id`, `kind`, `transport`, `provider`, `status`, `input_schema`, and `output_schema`.

#### Scenario: Registry returns one capability
- **WHEN** a client requests `GET /api/capabilities/voice.tts.edge`
- **THEN** the response returns the matching capability contract
- **AND** does not expose provider internals beyond the contract.

### Requirement: Capability Health
The backend SHALL expose provider-neutral health for each capability.

#### Scenario: Health reports disabled or dependency status
- **WHEN** a client requests `GET /api/capabilities/voice.tts.edge/health`
- **THEN** the response returns the same status category used by the registry
- **AND** includes a human-readable reason when the capability is not ready.

### Requirement: Capability Invocation
The backend SHALL expose a short synchronous invocation endpoint for registered capabilities.

#### Scenario: Disabled capability invocation returns structured unavailable error
- **GIVEN** voice runtime is disabled
- **WHEN** a client posts to `POST /api/capabilities/voice.tts.edge/invoke`
- **THEN** the backend returns a structured unavailable error
- **AND** the main server remains healthy.

#### Scenario: Unknown capability returns not found
- **WHEN** a client posts to `POST /api/capabilities/unknown/invoke`
- **THEN** the backend returns a structured not-found error.

### Requirement: Frontend Capability API Wrapper
The frontend SHALL provide a provider-neutral capability API wrapper.

#### Scenario: Frontend calls capability runtime
- **WHEN** frontend code calls `capabilityApi.list()`, `capabilityApi.get(id)`, `capabilityApi.health(id)`, or `capabilityApi.invoke(id, payload)`
- **THEN** requests go through the existing API base and auth interceptor.
