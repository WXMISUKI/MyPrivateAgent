# unified-capability-runtime Specification

## MODIFIED Requirements

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

#### Scenario: External voice provider registration
- **GIVEN** `ENABLE_EXTERNAL_VOICE_CAPABILITY_PROVIDER=true`
- **WHEN** a client requests `GET /api/capabilities`
- **THEN** `voice.tts.edge` and `voice.asr.vosk` are exposed with `transport=http`
- **AND** their status is resolved from the configured external provider health endpoints.

### Requirement: Capability Health
The backend SHALL expose provider-neutral health for each capability.

#### Scenario: Health reports disabled or dependency status
- **WHEN** a client requests `GET /api/capabilities/voice.tts.edge/health`
- **THEN** the response returns the same status category used by the registry
- **AND** includes a human-readable reason when the capability is not ready.

#### Scenario: External provider unreachable
- **GIVEN** an HTTP capability provider is configured but unreachable
- **WHEN** a client requests capability health
- **THEN** the response reports `status=unreachable`
- **AND** includes an error code `CAPABILITY_PROVIDER_UNREACHABLE`.

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

#### Scenario: External capability invocation delegates to provider
- **GIVEN** `voice.tts.edge` is registered as an HTTP capability
- **WHEN** a client posts to `POST /api/capabilities/voice.tts.edge/invoke`
- **THEN** the backend delegates the payload to the configured external provider invoke endpoint
- **AND** returns the provider-neutral response envelope.

## ADDED Requirements

### Requirement: Capability Provider Heartbeat
The backend SHALL expose a live heartbeat surface for external capability providers.

#### Scenario: Heartbeat reports provider and capability status
- **WHEN** a client requests `GET /api/capabilities/heartbeat`
- **THEN** the response includes `contract_version`
- **AND** includes provider heartbeat records
- **AND** includes per-capability health records for the provider.

#### Scenario: Heartbeat survives provider outage
- **GIVEN** an external capability provider is configured but unreachable
- **WHEN** a client requests `GET /api/capabilities/heartbeat`
- **THEN** the response still returns 200
- **AND** the provider record reports `status=unreachable`
- **AND** includes a machine-readable error code.
